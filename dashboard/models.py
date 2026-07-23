from django.db import models


class RespostaChatbot(models.Model):
    """Resposta programada editavel pelo administrador."""

    PERFIL_CHOICES = [
        ('todos', 'Todos'),
        ('visitante', 'Visitante'),
        ('admin', 'Administrador'),
        ('consultor', 'Consultor Agricola'),
        ('analista', 'Analista de Dados'),
        ('tecnico', 'Tecnico de Campo'),
        ('agricultor', 'Agricultor'),
        ('cliente', 'Cliente'),
    ]

    titulo = models.CharField('Titulo', max_length=120)
    palavras_chave = models.CharField(
        'Palavras-chave',
        max_length=255,
        help_text='Separe por virgulas. Ex: clima, chuva, meteorologia',
    )
    resposta = models.TextField('Resposta')
    perfil = models.CharField('Perfil', max_length=20, choices=PERFIL_CHOICES, default='todos')
    ativo = models.BooleanField('Ativo', default=True)
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Resposta do Chatbot'
        verbose_name_plural = 'Respostas do Chatbot'
        ordering = ['perfil', 'titulo']

    def __str__(self):
        return f'{self.titulo} ({self.get_perfil_display()})'
