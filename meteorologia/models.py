"""
Modelos da app meteorologia - Registo de Clima e Alertas.
"""

from django.db import models
from propriedades.models import Propriedade


class RegistroClima(models.Model):
    """Registo de dados meteorológicos obtidos via API para uma propriedade."""
    propriedade = models.ForeignKey(
        Propriedade,
        on_delete=models.CASCADE,
        related_name='registos_clima',
        verbose_name='Propriedade'
    )
    data = models.DateTimeField('Data e hora', auto_now_add=True)
    temperatura = models.DecimalField('Temperatura (°C)', max_digits=5, decimal_places=2, null=True, blank=True)
    humidade = models.DecimalField('Humidade (%)', max_digits=5, decimal_places=2, null=True, blank=True)
    precipitacao = models.DecimalField('Precipitação (mm)', max_digits=6, decimal_places=2, null=True, blank=True)
    vento_velocidade = models.DecimalField('Vento (km/h)', max_digits=6, decimal_places=2, null=True, blank=True)
    descricao = models.CharField('Condição', max_length=200, blank=True)

    class Meta:
        verbose_name = 'Registo de Clima'
        verbose_name_plural = 'Registos de Clima'
        ordering = ['-data']

    def __str__(self):
        return f"{self.propriedade.nome} - {self.data.strftime('%d/%m/%Y %H:%M')}"


class Alerta(models.Model):
    """Alerta automático gerado pelo sistema para uma propriedade."""
    TIPO_CHOICES = [
        ('geada', 'Risco de Geada'),
        ('seca', 'Risco de Seca'),
        ('praga', 'Alerta de Praga'),
        ('chuva_excessiva', 'Chuva Excessiva'),
        ('calor_extremo', 'Calor Extremo'),
        ('vento_forte', 'Vento Forte'),
    ]
    SEVERIDADE_CHOICES = [
        ('info', 'Informativo'),
        ('aviso', 'Aviso'),
        ('urgente', 'Urgente'),
    ]

    propriedade = models.ForeignKey(
        Propriedade,
        on_delete=models.CASCADE,
        related_name='alertas',
        verbose_name='Propriedade'
    )
    tipo = models.CharField('Tipo de alerta', max_length=20, choices=TIPO_CHOICES)
    severidade = models.CharField('Severidade', max_length=10, choices=SEVERIDADE_CHOICES, default='aviso')
    mensagem = models.TextField('Mensagem do alerta')
    data = models.DateTimeField('Data do alerta', auto_now_add=True)
    lido = models.BooleanField('Lido', default=False)

    class Meta:
        verbose_name = 'Alerta'
        verbose_name_plural = 'Alertas'
        ordering = ['-data']

    def __str__(self):
        return f"[{self.get_severidade_display()}] {self.get_tipo_display()} - {self.propriedade.nome}"
