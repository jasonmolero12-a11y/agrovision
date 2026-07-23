"""Registo dos modelos de Meteorologia no painel admin."""

from django.contrib import admin
from .models import RegistroClima, Alerta


@admin.register(RegistroClima)
class RegistroClimaAdmin(admin.ModelAdmin):
    list_display = ('propriedade', 'data', 'temperatura', 'humidade', 'precipitacao', 'vento_velocidade')
    list_filter = ('propriedade',)
    ordering = ('-data',)
    actions = None


@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'propriedade', 'severidade', 'data', 'lido')
    list_filter = ('tipo', 'severidade', 'lido')
    search_fields = ('mensagem', 'propriedade__nome')
    ordering = ('-data',)
    actions = None
