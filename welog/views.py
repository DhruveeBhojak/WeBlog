from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import RegisterForm, LoginForm, BlogPostForm
from .models import Profile, BlogPost, Category
from django.db.models import Q, Count
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, permissions
from .serializers import BlogPostSerializer
from django.http import JsonResponse
from django.contrib.auth import logout
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator
import datetime


def landing_view(request):
    bloggers = (
        Profile.objects
        .annotate(post_count=Count('user__posts'))
        .filter(post_count__gt=2)[:9]
    )

    categories = Category.objects.all()
    category_blogs = {}

    for category in categories:
        blogs = BlogPost.objects.filter(category=category).order_by('-created_at')[:3]
        if blogs.exists():
            category_blogs[category] = blogs

    return render(request, 'landing.html', {
        'bloggers': bloggers,
        'category_blogs': category_blogs
    })



def validate_username(request):
    username = request.GET.get("username", "").strip()
    if username:
        is_taken = User.objects.filter(username=username).exists()
        return JsonResponse({"is_taken": is_taken})
    return JsonResponse({"error": "Empty username"}, status=400)

def validate_email(request):
    email = request.GET.get("email", "").strip()
    if email:
        is_taken = User.objects.filter(email=email).exists()
        return JsonResponse({"is_taken": is_taken})
    return JsonResponse({"error": "Empty email"}, status=400)


# def check_username(request):
#     username = request.GET.get('username', None)
#     exists = User.objects.filter(username=username).exists()
#     return JsonResponse({'exists': exists})

# def check_email(request):
#     email = request.GET.get('email', None)
#     exists = User.objects.filter(email=email).exists()
#     return JsonResponse({'exists': exists})

def create_user_and_profile(form):
    user = User.objects.create_user(
        username=form.cleaned_data['username'],
        email=form.cleaned_data['email'],
        password=form.cleaned_data['password']
    )
    Profile.objects.create(
        user=user,
        fullname=form.cleaned_data['fullname'],
        gender=form.cleaned_data['gender'],
        DateofBirth=form.cleaned_data['DateofBirth'],
        profile_image=form.cleaned_data['profile_image']
    )
    return user

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            create_user_and_profile(form)
            messages.success(request, "Account created successfully.")
            return redirect('login')
    else:
        form = RegisterForm()
    
    return render(request, 'register.html', {'form': form})

# def register_view(request):
#     if request.method == 'POST':
#         form = RegisterForm(request.POST, request.FILES)
#         if form.is_valid():
#             username = form.cleaned_data['username']
#             email = form.cleaned_data['email']
#             user = User.objects.create_user(
#                 username=username,
#                 email=email,
#                 password=form.cleaned_data['password']
#             )

#             Profile.objects.create(
#                 user=user,
#                 fullname=form.cleaned_data['fullname'],
#                 gender=form.cleaned_data['gender'],
#                 DateofBirth=form.cleaned_data['DateofBirth'],
#                 profile_image=form.cleaned_data['profile_image']
#             )

#             messages.success(request, "Account created successfully.")
#             return redirect('login')
#     else:
#         form = RegisterForm()

#     return render(request, 'register.html', {'form': form})

# @never_cache
# def login_view(request):
#     form = LoginForm(request.POST or None)
#     if request.method == 'POST':
#         if form.is_valid():
#             username = form.cleaned_data['username']
#             password = form.cleaned_data['password']
#             user = authenticate(request, username=username, password=password)
#             if user is not None:
#                 login(request, user)
#                 messages.success(request, "Logged in successfully!")
#                 return redirect('/home/')
#             else:
#                 form.add_error(None, "Invalid credentials. Please try again.")
    
#     return render(request, 'login.html', {'form': form})

@never_cache
def login_view(request):
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid(): 
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Logged in successfully!")
            return redirect('/home/')
        else:
            form.add_error(None, "Invalid credentials. Please try again.")
    
    return render(request, 'login.html', {'form': form})


class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user

class BlogPostViewSet(viewsets.ModelViewSet):
    queryset = BlogPost.objects.all().order_by('-created_at')
    serializer_class = BlogPostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

@login_required
def home_view(request):
    query = request.GET.get('q')
    selected_category = request.GET.get('category')
    posts = BlogPost.objects.all().order_by('-created_at')

    if query:
        posts = posts.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(author__username__icontains=query)
        )

    if selected_category:
        posts = posts.filter(category__name=selected_category)

    paginator = Paginator(posts, 3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()
    return render(request, 'home.html', {
        'page_obj': page_obj,
        'categories': categories,
        'query': query,
        'selected_category': selected_category
    })

@login_required
def create_blog_view(request):
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            blog_post = form.save(commit=False)
            if not blog_post.category:
                blog_post.category, _ = Category.objects.get_or_create(name='Others')
            blog_post.author = request.user
            blog_post.save()
            messages.success(request, "Your blog was posted successfully!")
            return redirect('home')
    else:
        form = BlogPostForm()
    return render(request, 'create_blog.html', {'form': form})

def blog_detail_view(request, post_id):
    blog = get_object_or_404(BlogPost, id=post_id)
    return render(request, 'blog_detail.html', {'blog': blog})

@login_required
def profile_view(request):
    user_blogs = BlogPost.objects.filter(author=request.user).order_by('-created_at')
    return render(request, 'profile.html', {'blogs': user_blogs})

def my_blogs_view(request):
    blogs = BlogPost.objects.filter(author=request.user)
    return render(request, 'blog/profile.html', {'blogs': blogs})

@login_required
def edit_blog(request, blog_id):
    blog = get_object_or_404(BlogPost, id=blog_id, author=request.user)
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=blog)
        if form.is_valid():
            form.save()
            messages.success(request, "Blog updated successfully!")
            return redirect('profile')
    else:
        form = BlogPostForm(instance=blog)
    return render(request, 'edit_blog.html', {'form': form, 'blog': blog})

@login_required
def delete_blog(request, blog_id):
    blog = get_object_or_404(BlogPost, id=blog_id, author=request.user)
    blog.delete()
    messages.success(request, "Blog deleted successfully!")
    return redirect('profile') 

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')
