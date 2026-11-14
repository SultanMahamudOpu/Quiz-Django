from django.db import models
from django.contrib.auth.models import User

class Quiz(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()

    def __str__(self):
        return self.title

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question = models.TextField()

    def __str__(self):
        return f"{self.quiz.title} - {self.question[:50]}"

class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    option = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.question.question[:30]} -> {self.option} ({self.is_correct})"

class Participant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='participant')
    name = models.CharField(max_length=150)
    classroom = models.CharField(max_length=100)  # Using classroom because 'class' is a python reserved word
    age = models.IntegerField()
    gender = models.CharField(max_length=20)
    institution = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class QuizAttempt(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    score = models.IntegerField()
    total_questions = models.IntegerField()
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-score', 'completed_at']

    @property
    def position(self):
        # Calculate rank among all attempts for this quiz
        higher_scores = QuizAttempt.objects.filter(
            quiz=self.quiz,
            score__gt=self.score
        ).count()
        same_score_earlier = QuizAttempt.objects.filter(
            quiz=self.quiz,
            score=self.score,
            completed_at__lt=self.completed_at
        ).count()
        return higher_scores + same_score_earlier + 1

    def __str__(self):
        return f"{self.participant.name} - {self.quiz.title} - {self.score}/{self.total_questions}"
