# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.contrib import admin
from django.contrib.admin import StackedInline

from signals.apps.questionnaire.models import (
    Answer,
    Page,
    PageQuestion,
    Question,
    Questionnaire,
    Response
)


class QuestionnaireAdmin(admin.ModelAdmin):
    fields = ('uuid', 'name', 'is_active', 'created_at', )
    readonly_fields = ('uuid', 'created_at', )
    list_display = ('name', 'is_active', 'created_at', )
    list_per_page = 20
    list_select_related = True


admin.site.register(Questionnaire, QuestionnaireAdmin)


class PageQuestionInline(admin.TabularInline):
    model = PageQuestion
    fields = ('question', 'required', 'order', )
    extra = 1


class PageAdmin(admin.ModelAdmin):
    inlines = (PageQuestionInline, )
    fields = ('uuid', 'questionnaire', 'description', 'order', 'created_at', )
    readonly_fields = ('uuid', 'created_at', )
    list_display = ('questionnaire', 'description', 'created_at', )
    list_per_page = 20
    list_select_related = True

    def get_form(self, request, obj=None, **kwargs):
        form = super(PageAdmin, self).get_form(request, obj, **kwargs)
        field = form.base_fields['questionnaire']
        field.widget.can_add_related = False
        field.widget.can_change_related = False
        field.widget.can_delete_related = False
        return form


admin.site.register(Page, PageAdmin)


class QuestionAdmin(admin.ModelAdmin):
    fields = ('uuid', 'slug', 'text', 'help_text', 'type', 'choices', 'json_schema', 'created_at', )
    readonly_fields = ('uuid', 'slug', 'created_at', )
    list_display = ('text', 'type', 'created_at', )
    list_per_page = 20
    list_select_related = True


admin.site.register(Question, QuestionAdmin)


class AnswerInline(StackedInline):
    model = Answer
    readonly_fields = ('uuid', 'question', 'response', 'text', 'created_at',)
    show_change_link = False
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class ResponseAdmin(admin.ModelAdmin):
    fields = ('uuid', 'questionnaire', 'expired', 'ttl', )
    readonly_fields = ('uuid', 'ttl', 'created_at', )
    list_display = ('uuid', 'questionnaire', 'get_answered_questions', )
    list_per_page = 20
    list_select_related = True
    inlines = (AnswerInline, )

    def get_answered_questions(self, obj):

        return f'{obj.answers.distinct("question").count()} of ' \
               f'{sum([page.questions.count() for page in obj.questionnaire.pages.all()])}'
    get_answered_questions.short_description = 'Answered questions'


admin.site.register(Response, ResponseAdmin)


class AnswerAdmin(admin.ModelAdmin):
    fields = ('uuid', 'question', 'response', 'text', )
    readonly_fields = ('uuid', 'question', 'response', 'text', 'created_at', )
    list_display = ('uuid', 'text', )
    list_per_page = 20
    list_select_related = True


admin.site.register(Answer, AnswerAdmin)
