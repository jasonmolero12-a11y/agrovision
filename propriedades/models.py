"""
Modelos da app propriedades - Gestão de Propriedades, Talhões e Culturas.
"""

from django.db import models
from django.conf import settings


class Cultura(models.Model):
    """Culturas agrícolas disponíveis (soja, milho, cana-de-açúcar, café...)."""
    nome = models.CharField('Nome da cultura', max_length=100, unique=True)
    ciclo = models.CharField('Ciclo', max_length=50, help_text='Ex: Anual, Semestral')
    epoca_plantio = models.CharField('Época de plantio', max_length=100, blank=True)
    descricao = models.TextField('Descrição', blank=True)
    imagem_referencia = models.ImageField('Imagem de referência', upload_to='culturas/', blank=True, null=True)

    class Meta:
        verbose_name = 'Cultura'
        verbose_name_plural = 'Culturas'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Propriedade(models.Model):
    """Propriedade rural (fazenda) pertencente a um agricultor."""
    nome = models.CharField('Nome da propriedade', max_length=255)
    proprietario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='propriedades',
        verbose_name='Proprietário (Agricultor)'
    )
    clientes_autorizados = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='fornecedores_autorizados',
        blank=True,
        limit_choices_to={'tipo_utilizador': 'cliente'},
        verbose_name='Clientes compradores autorizados',
        help_text='Compradores que podem consultar produção e relatórios emitidos desta propriedade.',
    )
    consultor_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='propriedades_consultadas',
        verbose_name='Consultor responsável'
    )
    tecnico_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='propriedades_tecnicas', verbose_name='Técnico de campo responsável',
        limit_choices_to={'tipo_utilizador': 'tecnico'},
    )
    analista_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='propriedades_analisadas', verbose_name='Analista de dados responsável',
        limit_choices_to={'tipo_utilizador': 'analista'},
    )
    localizacao = models.CharField('Localização', max_length=200, blank=True)
    latitude = models.DecimalField('Latitude', max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField('Longitude', max_digits=9, decimal_places=6, null=True, blank=True)
    area_total = models.DecimalField('Área total (hectares)', max_digits=10, decimal_places=2, null=True, blank=True)
    foto_capa = models.ImageField('Foto de capa', upload_to='propriedades/', blank=True, null=True)
    exposta_para_clientes = models.BooleanField('Expor no Mercado Agrícola', default=False, help_text='Quando ativo, clientes podem ver a apresentação comercial desta propriedade.')
    descricao_comercial = models.TextField('Apresentação comercial', blank=True, help_text='Resumo público para compradores: culturas, capacidade, qualidade e condições de fornecimento.')
    favoritada_por = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='propriedades_favoritas', blank=True, limit_choices_to={'tipo_utilizador': 'cliente'}, verbose_name='Favoritada por clientes')
    data_criacao = models.DateTimeField('Data de registo', auto_now_add=True)

    class Meta:
        verbose_name = 'Propriedade'
        verbose_name_plural = 'Propriedades'
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.proprietario.nome_completo})"


class Talhao(models.Model):
    """Divisão interna de uma propriedade onde é cultivada uma cultura."""
    propriedade = models.ForeignKey(
        Propriedade,
        on_delete=models.CASCADE,
        related_name='talhoes',
        verbose_name='Propriedade'
    )
    nome = models.CharField('Nome do talhão', max_length=255)
    cultura = models.ForeignKey(Cultura, on_delete=models.SET_NULL, null=True, verbose_name='Cultura')
    area = models.DecimalField('Área (hectares)', max_digits=10, decimal_places=2, null=True, blank=True)
    tipo_solo = models.CharField('Tipo de solo', max_length=100, blank=True)
    data_plantio = models.DateField('Data de plantio', null=True, blank=True)
    estadio_fenologico = models.CharField('Estádio fenológico', max_length=100, blank=True)
    foto_atual = models.ImageField('Foto atual do talhão', upload_to='talhoes/', blank=True, null=True)

    class Meta:
        verbose_name = 'Talhão'
        verbose_name_plural = 'Talhões'
        ordering = ['propriedade', 'nome']

    def __str__(self):
        return f"{self.nome} - {self.propriedade.nome}"


class RegistoProducao(models.Model):
    """Produção/colheita real registada por talhão e campanha."""
    UNIDADE_CHOICES = [('kg', 'Quilogramas'), ('t', 'Toneladas'), ('sc', 'Sacos')]
    ESTADO_COMERCIAL_CHOICES = [('disponivel', 'Disponível'), ('reservado', 'Reservado'), ('vendido', 'Vendido')]

    talhao = models.ForeignKey(Talhao, on_delete=models.CASCADE, related_name='registos_producao', verbose_name='Talhão')
    campanha = models.CharField('Campanha', max_length=80, help_text='Ex.: 2025/2026')
    data_colheita = models.DateField('Data da colheita')
    quantidade = models.DecimalField('Quantidade', max_digits=12, decimal_places=2)
    unidade = models.CharField('Unidade', max_length=5, choices=UNIDADE_CHOICES, default='kg')
    estado_comercial = models.CharField('Estado comercial', max_length=12, choices=ESTADO_COMERCIAL_CHOICES, default='disponivel')
    qualidade = models.CharField('Qualidade/classificação', max_length=120, blank=True)
    observacoes = models.TextField('Observações', blank=True)
    foto_colheita = models.ImageField('Foto da produção/colheita', upload_to='colheitas/', blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_colheita']
        verbose_name = 'Registo de produção'
        verbose_name_plural = 'Registos de produção'

    def __str__(self):
        return f'{self.talhao} — {self.campanha}: {self.quantidade} {self.unidade}'


class PedidoCompra(models.Model):
    """Pedido comercial validado pelo agricultor antes da decisão administrativa."""
    STATUS_CHOICES = [
        ('pendente', 'Pendente na administração'),
        ('aguarda_agricultor', 'Aguardando confirmação do agricultor'),
        ('confirmado', 'Disponibilidade confirmada'),
        ('aprovado', 'Aprovado'),
        ('recusado', 'Recusado'),
    ]

    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pedidos_compra', limit_choices_to={'tipo_utilizador': 'cliente'})
    propriedade = models.ForeignKey(Propriedade, on_delete=models.CASCADE, related_name='pedidos_compra')
    producao = models.ForeignKey(RegistoProducao, on_delete=models.SET_NULL, null=True, blank=True, related_name='pedidos_compra')
    quantidade_pretendida = models.CharField(max_length=120, blank=True)
    contacto = models.CharField(max_length=160)
    observacoes = models.TextField(blank=True)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default='pendente')
    resposta_agricultor = models.BooleanField(null=True, blank=True)
    observacao_agricultor = models.TextField(blank=True)
    nota_administracao = models.TextField(blank=True)
    decidido_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='pedidos_compra_decididos')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-atualizado_em']
        verbose_name = 'Pedido de compra'
        verbose_name_plural = 'Pedidos de compra'

    def __str__(self):
        return f'{self.cliente} — {self.propriedade} — {self.get_status_display()}'
