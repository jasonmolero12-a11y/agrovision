"""
Modelos da app contas - Sistema de Utilizadores e Perfis da AgroVision.

Hierarquia de acessos:
  - Administrador   (acesso total)
  - Consultor       (acesso técnico)
  - Analista        (acesso analítico)
  - Técnico Campo   (acesso operacional)
  - Agricultor      (acesso operacional)
  - Cliente         (acesso de consulta)
  - Visitante       (sem login - portal público)
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone


class UtilizadorManager(BaseUserManager):
    """Gestor compatível com autenticação baseada exclusivamente em email."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('O email é obrigatório.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('tipo_utilizador', 'admin')
        if extra_fields.get('is_staff') is not True:
            raise ValueError('O superutilizador deve ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('O superutilizador deve ter is_superuser=True.')
        return self._create_user(email, password, **extra_fields)


class Utilizador(AbstractUser):
    """Modelo de utilizador personalizado da AgroVision."""

    # Tipos de utilizador disponíveis no sistema
    TIPO_CHOICES = [
        ('visitante', 'Visitante'),
        ('admin', 'Administrador'),
        ('consultor', 'Consultor Agrícola'),
        ('analista', 'Analista de Dados'),
        ('tecnico', 'Técnico de Campo'),
        ('agricultor', 'Agricultor'),
        ('cliente', 'Cliente'),
    ]
    STATUS_SOLICITACAO_CHOICES = [
        ('sem_pedido', 'Sem pedido'),
        ('pendente', 'Pendente'),
        ('aprovado', 'Aprovado'),
        ('recusado', 'Recusado'),
    ]

    # Campos personalizados
    nome_completo = models.CharField('Nome completo', max_length=150, blank=True)
    telefone = models.CharField('Telefone', max_length=20, blank=True)
    foto_perfil = models.ImageField(
        'Foto de perfil',
        upload_to='fotos_perfil/',
        blank=True,
        null=True,
    )
    tipo_utilizador = models.CharField(
        'Tipo de utilizador',
        max_length=20,
        choices=TIPO_CHOICES,
        default='visitante'
    )
    perfil_solicitado = models.CharField(
        'Perfil solicitado',
        max_length=20,
        choices=[c for c in TIPO_CHOICES if c[0] != 'admin'],
        blank=True,
    )
    justificativa_solicitacao = models.TextField('Justificativa da solicitação', blank=True)
    validacao_profissional = models.TextField('Validação profissional', blank=True)
    cv_solicitacao = models.FileField(
        'CV em PDF',
        upload_to='cv_solicitacoes/',
        blank=True,
        null=True,
    )
    status_solicitacao = models.CharField(
        'Estado da solicitação',
        max_length=20,
        choices=STATUS_SOLICITACAO_CHOICES,
        default='sem_pedido',
    )
    data_solicitacao = models.DateTimeField('Data da solicitação', blank=True, null=True)
    data_registro = models.DateTimeField('Data de registo', auto_now_add=True)
    ativo_sistema = models.BooleanField('Ativo no sistema', default=True)

    # Login por email em vez de username
    email = models.EmailField('Email', unique=True)
    username = None

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome_completo', 'tipo_utilizador']
    objects = UtilizadorManager()

    class Meta:
        verbose_name = 'Utilizador'
        verbose_name_plural = 'Utilizadores'
        ordering = ['nome_completo']

    def save(self, *args, **kwargs):
        # Um perfil Administrador deve conseguir abrir o Centro de Gestão Completa.
        if self.tipo_utilizador == 'admin':
            self.is_staff = True
            self.is_superuser = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nome_completo or self.email} ({self.get_tipo_utilizador_display()})"

    # ==========================================================================
    # MÉTODOS AUXILIARES PARA VERIFICAÇÃO DE PERFIL
    # ==========================================================================
    @property
    def is_admin(self):
        """Verifica se o utilizador é Administrador."""
        return self.tipo_utilizador == 'admin' or self.is_superuser

    @property
    def is_visitante(self):
        """Verifica se o utilizador ainda não tem perfil aprovado."""
        return self.tipo_utilizador == 'visitante'

    @property
    def is_consultor(self):
        """Verifica se o utilizador é Consultor Agrícola."""
        return self.tipo_utilizador == 'consultor'

    @property
    def is_analista(self):
        """Verifica se o utilizador é Analista de Dados."""
        return self.tipo_utilizador == 'analista'

    @property
    def is_tecnico(self):
        """Verifica se o utilizador é Técnico de Campo."""
        return self.tipo_utilizador == 'tecnico'

    @property
    def is_agricultor(self):
        """Verifica se o utilizador é Agricultor."""
        return self.tipo_utilizador == 'agricultor'

    @property
    def is_cliente(self):
        """Verifica se o utilizador é Cliente."""
        return self.tipo_utilizador == 'cliente'

    @property
    def tem_acesso_tecnico(self):
        """Administrador e Consultor têm acesso técnico; Analista é somente leitura."""
        return self.tipo_utilizador in ['admin', 'consultor'] or self.is_superuser

    @property
    def tem_acesso_operacional(self):
        """Técnico e Agricultor têm acesso operacional."""
        return self.tipo_utilizador in ['tecnico', 'agricultor']

    @property
    def prazo_solicitacao_expirado(self):
        if self.status_solicitacao != 'pendente' or not self.data_solicitacao:
            return False
        return timezone.now() >= self.data_solicitacao + timezone.timedelta(hours=48)


class MensagemSuporte(models.Model):
    STATUS_CHOICES = [('aberta', 'Aberta'), ('em_analise', 'Em análise'), ('respondida', 'Respondida'), ('encerrada', 'Encerrada')]
    CATEGORIA_CHOICES = [('solicitacao', 'Solicitação de perfil'), ('acesso', 'Acesso ao sistema'), ('dados', 'Dados ou informação'), ('tecnico', 'Problema técnico'), ('outro', 'Outro assunto')]

    utilizador = models.ForeignKey(Utilizador, on_delete=models.CASCADE, related_name='mensagens_suporte')
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='outro')
    assunto = models.CharField(max_length=160)
    mensagem = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aberta')
    resposta_admin = models.TextField('Resposta da administração', blank=True)
    respondido_por = models.ForeignKey(Utilizador, on_delete=models.SET_NULL, related_name='respostas_suporte', blank=True, null=True)
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)
    respondida_em = models.DateTimeField(blank=True, null=True)
    resposta_lida = models.BooleanField(default=False)

    class Meta:
        ordering = ['-atualizada_em']
        verbose_name = 'Mensagem de suporte'
        verbose_name_plural = 'Mensagens de suporte'

    def __str__(self):
        return f'{self.assunto} — {self.utilizador.nome_completo or self.utilizador.email}'
