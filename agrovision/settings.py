"""
Configurações do projeto AgroVision.
Plataforma de Consultoria Agrícola Inteligente para a empresa Hispatec.
"""

from pathlib import Path
from decouple import config
import agrovision.django_compat  # noqa: F401

# Caminho base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent


# ==========================================================================
# SEGURANÇA
# ==========================================================================
SECRET_KEY = config('SECRET_KEY', default='django-insecure-8f58+6!9zb1=48wc_iyw&%ec$i=31ycd@kqir5_ez*c6n0*hxk')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']


# ==========================================================================
# APLICAÇÕES INSTALADAS
# ==========================================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Apps do projeto AgroVision
    'contas',
    'propriedades',
    'consultoria',
    'meteorologia',
    'dashboard',
    'config_sistema',
    'publico',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'contas.middleware.RestringirVisitanteMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'agrovision.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'dashboard.context_processors.notificacoes_sistema',
            ],
        },
    },
]

WSGI_APPLICATION = 'agrovision.wsgi.application'


# ==========================================================================
# BASE DE DADOS - MySQL (Laragon)
# ==========================================================================
# Configuração padrão do Laragon: utilizador 'root' sem password
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME', default='agrovision'),
        'USER': config('DB_USER', default='root'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='127.0.0.1'),
        'PORT': config('DB_PORT', default='3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}


# ==========================================================================
# MODELO DE UTILIZADOR PERSONALIZADO
# ==========================================================================
AUTH_USER_MODEL = 'contas.Utilizador'
AUTHENTICATION_BACKENDS = ['contas.backends.EmailOuNomeBackend']


# ==========================================================================
# VALIDAÇÃO DE PALAVRAS-PASSE
# ==========================================================================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ==========================================================================
# INTERNACIONALIZAÇÃO - Português / Angola
# ==========================================================================
LANGUAGE_CODE = 'pt-pt'
TIME_ZONE = 'Africa/Luanda'
USE_I18N = True
USE_TZ = True


# ==========================================================================
# LOGIN / LOGOUT / REDIRECIONAMENTOS
# ==========================================================================
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'


# ==========================================================================
# FICHEIROS ESTÁTICOS (CSS, JS, Imagens)
# ==========================================================================
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'


# ==========================================================================
# FICHEIROS DE UPLOAD (fotos de visitas, perfis)
# ==========================================================================
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ==========================================================================
# TIPO DE CHAVE PRÁRIA PADRÃO
# ==========================================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
