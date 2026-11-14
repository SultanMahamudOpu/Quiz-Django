from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from quiz.models import Participant

class QuizAuthAndProfileTests(TestCase):
    def test_registration_flow(self):
        # 1. Register a new user
        register_url = reverse('quiz:register')
        data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }
        response = self.client.post(register_url, data)
        # Registration redirects to profile settings
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('quiz:profile'))
        
        # User should be authenticated and logged in
        user = User.objects.get(username='testuser')
        self.assertEqual(user.email, 'testuser@example.com')
        
    def test_login_with_username_and_email(self):
        # Create a user first
        user = User.objects.create_user(username='loginuser', email='loginuser@example.com', password='mypassword123')
        
        login_url = reverse('quiz:login')
        
        # Try logging in with Username
        response = self.client.post(login_url, {
            'username': 'loginuser',
            'password': 'mypassword123'
        })
        self.assertEqual(response.status_code, 302) # Redirect to dashboard
        self.client.logout()
        
        # Try logging in with Email
        response = self.client.post(login_url, {
            'username': 'loginuser@example.com',
            'password': 'mypassword123'
        })
        self.assertEqual(response.status_code, 302) # Redirect to dashboard
        self.client.logout()

    def test_profile_settings_and_credentials_update(self):
        # Create user and log in
        user = User.objects.create_user(username='profileuser', email='profileuser@example.com', password='mypassword123')
        self.client.login(username='profileuser', password='mypassword123')
        
        profile_url = reverse('quiz:profile')
        
        # POST to save profile information and update username/email/password
        profile_data = {
            'username': 'updateduser',
            'email': 'updated@example.com',
            'name': 'Updated User Name',
            'classroom': 'Class 10',
            'age': 16,
            'gender': 'Male',
            'institution': 'High School',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        
        response = self.client.post(profile_url, profile_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('quiz:dashboard'))
        
        # Check User model changes
        user.refresh_from_db()
        self.assertEqual(user.username, 'updateduser')
        self.assertEqual(user.email, 'updated@example.com')
        self.assertTrue(user.check_password('newpassword123'))
        
        # Check Participant profile creation/update
        participant = Participant.objects.get(user=user)
        self.assertEqual(participant.name, 'Updated User Name')
        self.assertEqual(participant.classroom, 'Class 10')
        self.assertEqual(participant.age, 16)
        self.assertEqual(participant.gender, 'Male')
        self.assertEqual(participant.institution, 'High School')
