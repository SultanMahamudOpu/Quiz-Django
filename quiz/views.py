import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Max, Avg

from .models import Quiz, Question, Option, Participant, QuizAttempt
from .forms import ParticipantRegistrationForm, ParticipantProfileForm

def register_view(request):
    if request.user.is_authenticated:
        return redirect('quiz:dashboard')
    if request.method == 'POST':
        form = ParticipantRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, "Registration successful! Please complete your participant details.")
            return redirect('quiz:profile')
    else:
        form = ParticipantRegistrationForm()
    return render(request, 'quiz/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('quiz:dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('quiz:dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'quiz/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "Logged out successfully.")
    return redirect('quiz:login')

@login_required
def dashboard(request):
    # Ensure participant profile exists
    try:
        participant = request.user.participant
    except Participant.DoesNotExist:
        messages.error(request, "Please set up your profile details first.")
        # If user is admin/superuser without a participant record, create one
        if request.user.is_superuser:
            participant = Participant.objects.create(
                user=request.user,
                name="Admin User",
                classroom="Admin",
                age=30,
                gender="Male",
                institution="System"
            )
        else:
            return redirect('quiz:profile')

    quizzes = Quiz.objects.all()
    quiz_data = []

    for quiz in quizzes:
        attempts = QuizAttempt.objects.filter(participant=participant, quiz=quiz)
        has_taken = attempts.exists()
        best_score = attempts.aggregate(Max('score'))['score__max'] if has_taken else None
        
        # Calculate rank/position for their best attempt
        best_attempt = attempts.order_by('-score', 'completed_at').first()
        position = best_attempt.position if best_attempt else None

        quiz_data.append({
            'quiz': quiz,
            'has_taken': has_taken,
            'best_score': best_score,
            'position': position,
            'total_questions': quiz.questions.count(),
        })

    # Stats for the participant
    total_attempts = QuizAttempt.objects.filter(participant=participant).count()
    avg_score = QuizAttempt.objects.filter(participant=participant).aggregate(Avg('score'))['score__avg']

    context = {
        'participant': participant,
        'quiz_data': quiz_data,
        'total_attempts': total_attempts,
        'avg_score': round(avg_score, 1) if avg_score is not None else 0,
    }
    return render(request, 'quiz/dashboard.html', context)

@login_required
def profile_view(request):
    try:
        participant = request.user.participant
        created_profile = False
    except Participant.DoesNotExist:
        participant = None
        created_profile = True
    
    if request.method == 'POST':
        form = ParticipantProfileForm(request.POST, instance=participant, user=request.user)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            
            # Keep user logged in if they changed password
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)
            
            messages.success(request, "Your participant profile has been saved successfully.")
            return redirect('quiz:dashboard')
    else:
        form = ParticipantProfileForm(instance=participant, user=request.user)
        
    return render(request, 'quiz/profile.html', {
        'form': form,
        'created_profile': created_profile
    })


@login_required
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    participant = get_object_or_404(Participant, user=request.user)

    # Prepare randomized questions if they are not already in session
    session_key = f'quiz_{quiz.id}_questions'
    if session_key not in request.session:
        questions = list(quiz.questions.all())
        random.shuffle(questions)
        
        session_questions = []
        for q in questions:
            options = list(q.options.all())
            random.shuffle(options)
            session_questions.append({
                'id': q.id,
                'question': q.question,
                'options': [{'id': o.id, 'option': o.option} for o in options]
            })
        request.session[session_key] = session_questions

    questions_list = request.session[session_key]

    if request.method == 'POST':
        # Grade the Quiz
        correct_answers = 0
        total_questions = len(questions_list)

        for q_item in questions_list:
            q_id = q_item['id']
            selected_option_id = request.POST.get(f'question_{q_id}')
            if selected_option_id:
                try:
                    option = Option.objects.get(id=int(selected_option_id), question_id=q_id)
                    if option.is_correct:
                        correct_answers += 1
                except (Option.DoesNotExist, ValueError):
                    pass

        # Create attempt
        attempt = QuizAttempt.objects.create(
            participant=participant,
            quiz=quiz,
            score=correct_answers,
            total_questions=total_questions
        )

        # Clear session
        if session_key in request.session:
            del request.session[session_key]

        messages.success(request, f"Quiz submitted! You scored {correct_answers}/{total_questions}.")
        return redirect('quiz:results', attempt_id=attempt.id)

    return render(request, 'quiz/quiz.html', {
        'quiz': quiz,
        'questions': questions_list,
    })

@login_required
def results_view(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, participant__user=request.user)
    
    # Leaderboard for this quiz
    leaderboard = QuizAttempt.objects.filter(quiz=attempt.quiz).order_by('-score', 'completed_at')[:10]

    return render(request, 'quiz/results.html', {
        'attempt': attempt,
        'leaderboard': leaderboard,
    })

@login_required
def leaderboard_view(request, quiz_id=None):
    quizzes = Quiz.objects.all()
    selected_quiz = None
    attempts = []

    if quiz_id:
        selected_quiz = get_object_or_404(Quiz, id=quiz_id)
        attempts = QuizAttempt.objects.filter(quiz=selected_quiz).order_by('-score', 'completed_at')
    else:
        # Global stats: Rank participants by aggregate score or average score
        attempts = QuizAttempt.objects.order_by('-score', 'completed_at')

    return render(request, 'quiz/leaderboard.html', {
        'quizzes': quizzes,
        'selected_quiz': selected_quiz,
        'attempts': attempts,
    })
