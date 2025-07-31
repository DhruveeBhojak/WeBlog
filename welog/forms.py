from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Profile
from .models import BlogPost, Category
from ckeditor.widgets import CKEditorWidget



class RegisterForm(forms.ModelForm):
    profile_image = forms.ImageField(required=False)
    fullname = forms.CharField(max_length=150)
    username = forms.CharField(max_length=150)
    gender = forms.ChoiceField(choices=Profile._meta.get_field('gender').choices)
    DateofBirth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username is already taken.")
        return username
    

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email is already registered.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm = cleaned_data.get('confirm_password')

        if password and confirm and password != confirm:
            raise ValidationError("Passwords do not match.")
        
class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your password'
    }))


class BlogPostForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorWidget())
    class Meta:
        model = BlogPost
        fields = ['title', 'content','image', 'category']
    
    def __init__(self, *args, **kwargs):
        super(BlogPostForm, self).__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()