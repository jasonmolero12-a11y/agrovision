"""
Modelos da app consultoria - Recomendações, Visitas Técnicas e Pragas/Doenças.
"""

from django.db import models
from django.conf import settings
from propriedades.models import Propriedade, Talhao


class Recomendacao(models.Model):
    """Recomendação agronómica personalizada gerada pelo consultor."""
    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]
    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('emitida', 'Emitida'),
        ('aplicada', 'Aplicada pelo agricultor'),
    ]

    talhao = models.ForeignKey(Talhao, on_delete=models.CASCADE, related_name='recomendacoes', verbose_name='Talhão')
    consultor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recomendacoes_criadas',
        verbose_name='Consultor'
    )
    data = models.DateTimeField('Data da recomendação', auto_now_add=True)
    dados_solo = models.TextField('Dados do solo', blank=True, help_text='pH, nutrientes, matéria orgânica...')
    dados_clima = models.TextField('Dados do clima', blank=True, help_text='Temperatura, precipitação, humidade...')
    texto_recomendacao = models.TextField('Recomendação técnica')
    prioridade = models.CharField('Prioridade', max_length=10, choices=PRIORIDADE_CHOICES, default='media')
    status = models.CharField('Estado', max_length=10, choices=STATUS_CHOICES, default='emitida')
    foto_evidencia = models.ImageField('Foto de evidência', upload_to='recomendacoes/evidencias/', blank=True, null=True)
    foto_resultado = models.ImageField('Foto do resultado', upload_to='recomendacoes/resultados/', blank=True, null=True)

    class Meta:
        verbose_name = 'Recomendação'
        verbose_name_plural = 'Recomendações'
        ordering = ['-data']

    def __str__(self):
        return f"Recomendação para {self.talhao} - {self.data.strftime('%d/%m/%Y')}"


class VisitaTecnica(models.Model):
    """Registo de visita técnica a uma propriedade."""
    TIPO_CHOICES = [
        ('rotineira', 'Rotineira'),
        ('urgente', 'Urgente'),
        ('avaliacao', 'Avaliação'),
        ('monitoramento', 'Monitoramento'),
    ]

    propriedade = models.ForeignKey(Propriedade, on_delete=models.CASCADE, related_name='visitas', verbose_name='Propriedade')
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='visitas_realizadas',
        verbose_name='Responsável (Consultor/Técnico)'
    )
    data = models.DateField('Data da visita')
    tipo = models.CharField('Tipo de visita', max_length=20, choices=TIPO_CHOICES, default='rotineira')
    observacoes = models.TextField('Observações técnicas')
    recomendacao_campo = models.TextField('Recomendações de campo', blank=True)

    class Meta:
        verbose_name = 'Visita Técnica'
        verbose_name_plural = 'Visitas Técnicas'
        ordering = ['-data']

    def __str__(self):
        return f"Visita a {self.propriedade.nome} - {self.data.strftime('%d/%m/%Y')}"


class FotoVisita(models.Model):
    """Fotografias anexadas a uma visita técnica (upload de campo)."""
    visita = models.ForeignKey(VisitaTecnica, on_delete=models.CASCADE, related_name='fotos', verbose_name='Visita')
    imagem = models.ImageField('Imagem', upload_to='fotos_visitas/')
    legenda = models.CharField('Legenda', max_length=200, blank=True)
    data_upload = models.DateTimeField('Data de upload', auto_now_add=True)

    class Meta:
        verbose_name = 'Foto da Visita'
        verbose_name_plural = 'Fotos das Visitas'

    def __str__(self):
        return f"Foto: {self.legenda or 'sem legenda'} ({self.visita})"


class PragaDoenca(models.Model):
    """Registo de praga ou doença detectada num talhão."""
    SEVERIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    ]

    talhao = models.ForeignKey(Talhao, on_delete=models.CASCADE, related_name='pragas_doencas', verbose_name='Talhão')
    nome = models.CharField('Nome da praga/doença', max_length=200)
    severidade = models.CharField('Severidade', max_length=10, choices=SEVERIDADE_CHOICES, default='baixa')
    data_deteccao = models.DateField('Data de deteção')
    tratamento_sugerido = models.TextField('Tratamento sugerido', blank=True)
    resolvido = models.BooleanField('Resolvido', default=False)
    foto_diagnostico = models.ImageField('Foto do diagnóstico', upload_to='pragas/diagnosticos/', blank=True, null=True)
    foto_resultado = models.ImageField('Foto após tratamento', upload_to='pragas/resultados/', blank=True, null=True)

    class Meta:
        verbose_name = 'Praga/Doença'
        verbose_name_plural = 'Pragas/Doenças'
        ordering = ['-data_deteccao']

    def __str__(self):
        return f"{self.nome} ({self.talhao}) - {self.get_severidade_display()}"
