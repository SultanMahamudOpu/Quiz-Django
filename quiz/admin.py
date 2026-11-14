from django.contrib import admin
from .models import Quiz, Question, Option, Participant, QuizAttempt

class OptionInline(admin.TabularInline):
    model = Option
    extra = 4

class QuestionAdmin(admin.ModelAdmin):
    inlines = [OptionInline]
    list_display = ('question', 'quiz')
    list_filter = ('quiz',)
    search_fields = ('question',)

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 2

class QuizAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]
    list_display = ('title', 'description')
    search_fields = ('title',)

class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('name', 'classroom', 'age', 'gender', 'institution', 'user')
    search_fields = ('name', 'institution', 'user__username')

class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('participant', 'quiz', 'score', 'total_questions', 'completed_at', 'position')
    list_filter = ('quiz', 'completed_at')
    search_fields = ('participant__name', 'quiz__title')

admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Option)
admin.site.register(Participant, ParticipantAdmin)
admin.site.register(QuizAttempt, QuizAttemptAdmin)
