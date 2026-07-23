"""Registo do modelo de Configuração de API no painel admin."""

from django.contrib import admin

from .models import ServicoExternoAgroVision


@admin.register(ServicoExternoAgroVision)
class ServicoExternoAgroVisionAdmin(admin.ModelAdmin):
    list_display = (
        'nome',
        'codigo',
        'tipo',
        'ativo',
        'timeout_segundos',
        'atualizado_em',
    )
    list_filter = ('ativo', 'tipo')
    search_fields = ('nome', 'codigo', 'descricao', 'endpoint')
    list_editable = ('ativo', 'timeout_segundos')
    readonly_fields = ('atualizado_em',)
    fieldsets = (
        ('Identificação', {'fields': ('nome', 'codigo', 'tipo', 'descricao')}),
        ('Ligação', {'fields': ('endpoint', 'chave_api', 'timeout_segundos')}),
        ('Controlo', {'fields': ('ativo', 'atualizado_em')}),
    )

    def has_delete_permission(self, request, obj=None):
        # Evita apagar acidentalmente integrações usadas pelo sistema.
        return bool(request.user.is_superuser)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Mantém a configuração original do Gemini sincronizada para que
        # a alteração feita neste novo centro tenha efeito imediato no chatbot.
        if obj.codigo == 'gemini':
            from .models import ConfiguracaoAPI

            configuracao, _ = ConfiguracaoAPI.objects.get_or_create(pk=1)
            campos = []
            if hasattr(configuracao, 'ia_api_key'):
                configuracao.ia_api_key = obj.chave_api
                campos.append('ia_api_key')
            if hasattr(configuracao, 'ia_ativo'):
                configuracao.ia_ativo = obj.ativo
                campos.append('ia_ativo')
            if campos:
                configuracao.save(update_fields=campos)
from .models import ConfiguracaoAPI


@admin.register(ConfiguracaoAPI)
class ConfiguracaoAPIAdmin(admin.ModelAdmin):
    list_display = ('provedor', 'cidade_padrao', 'ativo', 'ia_provedor', 'ia_ativo', 'atualizado_em')
    fieldsets = (
        ('Provedor Meteorológico', {
            'fields': ('provedor', 'ativo')
        }),
        ('Chave da API', {
            'fields': ('api_key',),
            'description': 'Insira a chave (API Key) do OpenWeatherMap. Não é necessária se usar Open-Meteo.'
        }),
        ('Configurações', {
            'fields': ('url_base', 'cidade_padrao')
        }),
        ('Segurança de login e cadastro', {
            'fields': ('validar_nome_seguro', 'login_exigir_identificador_valido', 'login_exigir_senha_alfanumerica', 'cadastro_senha_exigir_letra', 'cadastro_senha_exigir_numero', 'permitir_login_por_nome'),
            'description': 'Regras globais de autenticação. Recomenda-se manter todas as proteções ativas.'
        }),
        ('Google/Gemini - IA externa', {
            'fields': ('ia_provedor', 'ia_ativo', 'ia_api_key', 'ia_modelo', 'ia_url_base'),
            'description': 'Configuração usada pelo chatbot e pelas recomendações automáticas. Se falhar, o sistema usa fallback local.'
        }),
    )

    def has_add_permission(self, request):
        """Não permite adicionar mais configurações (singleton)."""
        return not ConfiguracaoAPI.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
