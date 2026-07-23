"""
Modelos da app config_sistema - Configuração da API meteorológica.

Esta app permite ao Administrador configurar o provedor de API meteorológica
e a respetiva chave diretamente pelo painel admin, sem mexer no código.
"""

from django.db import models


class ServicoExternoAgroVision(models.Model):
    """Catálogo administrativo das integrações externas do AgroVision."""

    TIPO_CHOICES = [
        ('meteorologia', 'Meteorologia'),
        ('inteligencia', 'Inteligência artificial'),
        ('solo', 'Dados de solo'),
        ('satelite', 'Imagens de satélite'),
        ('agricultura', 'Dados agrícolas'),
        ('outro', 'Outro serviço'),
    ]

    codigo = models.SlugField(max_length=60, unique=True)
    nome = models.CharField(max_length=120)
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    endpoint = models.URLField(max_length=500, blank=True)
    chave_api = models.CharField(
        max_length=500,
        blank=True,
        help_text='Deixe vazia quando a API for pública e não exigir chave.',
    )
    ativo = models.BooleanField(default=True)
    timeout_segundos = models.PositiveSmallIntegerField(default=20)
    descricao = models.TextField(blank=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'serviço externo/API'
        verbose_name_plural = 'serviços externos e APIs'
        ordering = ('tipo', 'nome')

    def __str__(self):
        estado = 'ativo' if self.ativo else 'inativo'
        return f'{self.nome} ({estado})'

    @classmethod
    def configuracao(cls, codigo):
        """Obtém um serviço ativo sem derrubar o sistema em caso de falha."""
        try:
            return cls.objects.filter(codigo=codigo, ativo=True).first()
        except Exception:
            return None


class ConfiguracaoAPI(models.Model):
    """
    Configuração singleton (uma única instância) da API meteorológica.
    O Admin preenche estes campos pelo painel.
    """
    PROVEDOR_CHOICES = [
        ('openweather', 'OpenWeatherMap (requer chave)'),
        ('openmeteo', 'Open-Meteo (gratuito, sem chave)'),
    ]
    IA_PROVEDOR_CHOICES = [
        ('gemini', 'Google Gemini'),
        ('nenhum', 'Sem API externa'),
    ]

    provedor = models.CharField(
        'Provedor meteorológico',
        max_length=20,
        choices=PROVEDOR_CHOICES,
        default='openweather',
        help_text='Escolha o provedor da API meteorológica.'
    )
    api_key = models.CharField(
        'Chave da API (API Key)',
        max_length=200,
        blank=True,
        help_text='Necessária para OpenWeatherMap. Deixe vazio se usar Open-Meteo.'
    )
    url_base = models.CharField(
        'URL base da API',
        max_length=200,
        blank=True,
        help_text='Opcional: URL customizada. Deixe vazio para usar a padrão.'
    )
    cidade_padrao = models.CharField(
        'Cidade padrão (para testes)',
        max_length=100,
        default='Luanda',
        help_text='Cidade usada por defeito ao testar a API.'
    )
    ativo = models.BooleanField('Configuração ativa', default=True)
    ia_provedor = models.CharField(
        'Provedor de IA',
        max_length=20,
        choices=IA_PROVEDOR_CHOICES,
        default='gemini',
        help_text='Provedor usado pelo assistente e pelas sugestões automáticas.',
    )
    ia_api_key = models.CharField(
        'Chave da API Google/Gemini',
        max_length=255,
        blank=True,
        help_text='Cole aqui a chave criada no Google AI Studio.',
    )
    ia_modelo = models.CharField(
        'Modelo de IA',
        max_length=80,
        default='gemini-1.5-flash',
        help_text='Exemplo: gemini-1.5-flash. Pode trocar conforme o modelo disponível na sua chave.',
    )
    ia_url_base = models.CharField(
        'URL base da API de IA',
        max_length=255,
        blank=True,
        help_text='Opcional. Deixe vazio para usar a URL padrão do Gemini.',
    )
    ia_ativo = models.BooleanField(
        'IA externa ativa',
        default=False,
        help_text='Quando desligado, o sistema usa apenas regras internas e respostas programadas.',
    )
    validar_nome_seguro = models.BooleanField('Bloquear nomes formados apenas por símbolos', default=True)
    login_exigir_identificador_valido = models.BooleanField('Bloquear login com identificador apenas de símbolos', default=True)
    login_exigir_senha_alfanumerica = models.BooleanField('Bloquear login com senha apenas de símbolos', default=True)
    cadastro_senha_exigir_letra = models.BooleanField('Exigir pelo menos uma letra na nova senha', default=True)
    cadastro_senha_exigir_numero = models.BooleanField('Exigir pelo menos um número na nova senha', default=True)
    permitir_login_por_nome = models.BooleanField('Permitir login por nome completo', default=True, help_text='Se desligado, o login será permitido somente por email.')
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Configuração da API'
        verbose_name_plural = 'Configuração da API'

    def __str__(self):
        return f"Configuração API - {self.get_provedor_display()}"

    def save(self, *args, **kwargs):
        """Garante que só existe uma instância (singleton)."""
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *_args, **_kwargs):
        """Não permite apagar a configuração."""
        return None

    @classmethod
    def carregar(cls):
        """Carrega a instância única de configuração (cria se não existir)."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
