from django.contrib import admin

from .models import RespostaChatbot


@admin.register(RespostaChatbot)
class RespostaChatbotAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'perfil', 'ativo', 'atualizado_em')
    list_filter = ('perfil', 'ativo')
    search_fields = ('titulo', 'palavras_chave', 'resposta')
    list_editable = ('ativo',)
    fieldsets = (
        ('Regra', {
            'fields': ('titulo', 'perfil', 'palavras_chave', 'ativo')
        }),
        ('Resposta', {
            'fields': ('resposta',)
        }),
    )
