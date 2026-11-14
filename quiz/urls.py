from django.urls import path
from . import views

app_name = 'quiz'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    path('', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('take/<int:quiz_id>/', views.take_quiz, name='take_quiz'),
    path('results/<int:attempt_id>/', views.results_view, name='results'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('leaderboard/<int:quiz_id>/', views.leaderboard_view, name='quiz_leaderboard'),
]
