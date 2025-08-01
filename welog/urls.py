from . import views
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BlogPostViewSet

router = DefaultRouter()
router.register(r'posts', BlogPostViewSet)

urlpatterns = [
    path('',views.landing_view, name='landing'),
    path('ajax/validate-username/', views.validate_username, name='validate_username'),
    path('ajax/validate-email/', views.validate_email, name='validate_email'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('api/', include(router.urls)),
    path('home/', views.home_view, name='home'),
    path('newblog/', views.create_blog_view, name='create_blog'),
    path('post/<int:post_id>/', views.blog_detail_view, name='blog_detail'),
    path('profile/', views.profile_view, name='profile'),
    path('my-blogs/', views.my_blogs_view, name='my_blogs'),
    path('edit/<int:blog_id>/', views.edit_blog, name='edit_blog'),
    path('delete/<int:blog_id>/', views.delete_blog, name='delete_blog'),
    path('logout/', views.logout_view, name='logout'),


 ]

