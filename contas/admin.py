"""Registo dos modelos de Utilizador no painel admin do Django."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.urls import reverse
from django.utils.html import format_html
from .models import MensagemSuporte, Utilizador


@admin.register(Utilizador)
class UtilizadorAdmin(UserAdmin):
    """Configuração do Utilizador no painel admin."""
    list_display = (
        'email',
        'nome_completo',
        'tipo_utilizador',
        'perfil_solicitado',
        'status_solicitacao',
        'cv_solicitacao',
        'is_active',
        'data_registro',
    )
    list_filter = ('tipo_utilizador', 'status_solicitacao', 'perfil_solicitado', 'is_active', 'is_superuser')
    search_fields = ('email', 'nome_completo', 'telefone')
    ordering = ('nome_completo',)
    actions = ('aprovar_perfil_solicitado', 'recusar_perfil_solicitado', 'ativar_contas', 'desativar_contas')
    readonly_fields = ('last_login', 'data_registro', 'link_alterar_senha')

    fieldsets = (
        ('Dados de acesso', {
            'fields': ('email', 'password', 'link_alterar_senha')
        }),
        ('Dados pessoais', {
            'fields': ('nome_completo', 'telefone', 'foto_perfil')
        }),
        ('Permissões AgroVision', {
            'fields': (
                'tipo_utilizador',
                'perfil_solicitado',
                'justificativa_solicitacao',
                'validacao_profissional',
                'cv_solicitacao',
                'status_solicitacao',
                'ativo_sistema',
                'is_active',
                'is_staff',
                'is_superuser',
            )
        }),
        ('Permissões importantes', {
            'fields': ('groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Datas', {
            'fields': ('last_login', 'data_registro'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        ('Novo Utilizador', {
            'classes': ('wide',),
            'fields': ('email', 'nome_completo', 'tipo_utilizador', 'password1', 'password2'),
        }),
    )

    def link_alterar_senha(self, obj):
        if not obj or not obj.pk:
            return 'Guarde o utilizador antes de alterar a senha.'
        url = reverse('admin:auth_user_password_change', args=[obj.pk])
        return format_html('<a class="button" href="{}">Alterar senha deste utilizador</a>', url)
    link_alterar_senha.short_description = 'Alterar senha'

    @admin.action(description='Ativar contas selecionadas')
    def ativar_contas(self, request, queryset):
        total = queryset.update(is_active=True, ativo_sistema=True)
        self.message_user(request, f'{total} conta(s) ativada(s).')

    @admin.action(description='Desativar contas selecionadas')
    def desativar_contas(self, request, queryset):
        queryset = queryset.exclude(pk=request.user.pk)
        total = queryset.update(is_active=False, ativo_sistema=False)
        self.message_user(request, f'{total} conta(s) desativada(s). A sua própria conta foi protegida.')

    @admin.action(description='Aprovar perfil solicitado')
    def aprovar_perfil_solicitado(self, request, queryset):
        aprovados = 0
        for user in queryset.filter(status_solicitacao='pendente').exclude(perfil_solicitado=''):
            user.tipo_utilizador = user.perfil_solicitado
            user.status_solicitacao = 'aprovado'
            user.is_active = True
            user.save()
            aprovados += 1
        self.message_user(request, f'{aprovados} solicitação(ões) aprovada(s).')

    @admin.action(description='Recusar perfil solicitado')
    def recusar_perfil_solicitado(self, request, queryset):
        recusados = queryset.filter(status_solicitacao='pendente').update(status_solicitacao='recusado')
        self.message_user(request, f'{recusados} solicitação(ões) recusada(s).')


@admin.register(MensagemSuporte)
class MensagemSuporteAdmin(admin.ModelAdmin):
    list_display = ('assunto', 'utilizador', 'categoria', 'status', 'criada_em', 'respondida_em')
    list_filter = ('status', 'categoria', 'criada_em')
    search_fields = ('assunto', 'mensagem', 'utilizador__nome_completo', 'utilizador__email')
    readonly_fields = ('utilizador', 'categoria', 'assunto', 'mensagem', 'criada_em', 'atualizada_em')
