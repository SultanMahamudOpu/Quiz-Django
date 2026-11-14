from django import forms
from django.contrib.auth.models import User
from .models import Participant

class ParticipantRegistrationForm(forms.ModelForm):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'placeholder': 'Username', 'class': 'form-input'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Email Address', 'class': 'form-input'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-input'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password', 'class': 'form-input'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already registered.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password']
        )
        return user

class ParticipantProfileForm(forms.ModelForm):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'placeholder': 'Username', 'class': 'form-input'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Email Address', 'class': 'form-input'}))
    new_password = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'placeholder': 'New Password (leave blank to keep current)', 'class': 'form-input'}))
    confirm_password = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'placeholder': 'Confirm New Password', 'class': 'form-input'}))

    name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'placeholder': 'Full Name', 'class': 'form-input'}))
    classroom = forms.CharField(max_length=100, label="Class", widget=forms.TextInput(attrs={'placeholder': 'Class', 'class': 'form-input'}))
    age = forms.IntegerField(widget=forms.NumberInput(attrs={'placeholder': 'Age', 'class': 'form-input'}))
    gender = forms.ChoiceField(
        choices=[('', 'Select Gender'), ('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')],
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    institution = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'placeholder': 'Institution', 'class': 'form-input'}))

    class Meta:
        model = Participant
        fields = ['name', 'classroom', 'age', 'gender', 'institution']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and hasattr(self.instance, 'user') and self.instance.user:
            self.fields['username'].initial = self.instance.user.username
            self.fields['email'].initial = self.instance.user.email
        elif self.user:
            self.fields['username'].initial = self.user.username
            self.fields['email'].initial = self.user.email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        user_query = User.objects.filter(username=username)
        if self.instance and self.instance.pk and hasattr(self.instance, 'user') and self.instance.user:
            user_query = user_query.exclude(pk=self.instance.user.pk)
        elif self.user:
            user_query = user_query.exclude(pk=self.user.pk)
            
        if user_query.exists():
            raise forms.ValidationError("Username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        user_query = User.objects.filter(email=email)
        if self.instance and self.instance.pk and hasattr(self.instance, 'user') and self.instance.user:
            user_query = user_query.exclude(pk=self.instance.user.pk)
        elif self.user:
            user_query = user_query.exclude(pk=self.user.pk)

        if user_query.exists():
            raise forms.ValidationError("Email already registered.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        if new_password and new_password != confirm_password:
            raise forms.ValidationError("New passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user if (hasattr(profile, 'user') and profile.user) else self.user
        
        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        new_password = self.cleaned_data.get('new_password')
        if new_password:
            user.set_password(new_password)
        user.save()
        
        profile.user = user
        if commit:
            profile.save()
        return profile

