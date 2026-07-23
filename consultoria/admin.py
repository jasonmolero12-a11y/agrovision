"""Registo dos modelos de Consultoria no painel admin."""

from django.contrib import admin
from .models import Recomendacao, VisitaTecnica, FotoVisita, PragaDoenca


class FotoVisitaInline(admin.TabularInline):
    model = FotoVisita
    extra = 1


@admin.register(Recomendacao)
class RecomendacaoAdmin(admin.ModelAdmin):
    def changelist_view(self, request, extra_context=None):
        """Repara datas zero importadas do banco antigo antes de listar."""
        from django.db import connection

        if connection.vendor == 'mysql':
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE consultoria_recomendacao "
                    "SET data = CURRENT_TIMESTAMP "
                    "WHERE CAST(data AS CHAR) LIKE '0000-00-00%'"
                )
        return super().changelist_view(request, extra_context=extra_context)

    list_display = ('talhao', 'consultor', 'data', 'prioridade', 'status')
    list_filter = ('prioridade', 'status', 'consultor')
    search_fields = ('talhao__nome', 'texto_recomendacao')
    # Não usar date_hierarchy: em instalações novas do MySQL/Laragon ele
    # depende das tabelas internas de fuso horário e pode lançar ValueError.
    ordering = ('-data',)


@admin.register(VisitaTecnica)
class VisitaTecnicaAdmin(admin.ModelAdmin):
    list_display = ('propriedade', 'responsavel', 'data', 'tipo')
    list_filter = ('tipo', 'responsavel')
    search_fields = ('propriedade__nome', 'observacoes')
    date_hierarchy = 'data'
    inlines = [FotoVisitaInline]
    ordering = ('-data',)


@admin.register(FotoVisita)
class FotoVisitaAdmin(admin.ModelAdmin):
    list_display = ('visita', 'legenda', 'data_upload')
    readonly_fields = ('data_upload',)


@admin.register(PragaDoenca)
class PragaDoencaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'talhao', 'severidade', 'data_deteccao', 'resolvido')
    list_filter = ('severidade', 'resolvido')
    search_fields = ('nome', 'talhao__nome')
    date_hierarchy = 'data_deteccao'
    ordering = ('-data_deteccao',)
