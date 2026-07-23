"""
Formulários da app contas - Registo e edição de utilizadores.
"""

from django import forms
import re
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import MensagemSuporte, Utilizador


def _seguranca():
    try:
        from config_sistema.models import ConfiguracaoAPI
        return ConfiguracaoAPI.carregar()
    except Exception:
        return None


class FormRegisto(UserCreationForm):
    """Formulário de registo de novo utilizador."""
    email = forms.EmailField(label='Email', required=True)
    nome_completo = forms.CharField(label='Nome completo', max_length=150, required=True)
    telefone = forms.CharField(label='Telefone', max_length=20, required=False)

    class Meta:
        model = Utilizador
        fields = ('email', 'nome_completo', 'telefone')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Utilizador.objects.filter(email=email).exists():
            raise forms.ValidationError('Este email já está registado.')
        return email

    def clean_nome_completo(self):
        nome = ' '.join((self.cleaned_data.get('nome_completo') or '').split())
        letras = re.findall(r'[^\W\d_]', nome, flags=re.UNICODE)
        config = _seguranca()
        if (not config or config.validar_nome_seguro) and len(letras) < 2:
            raise forms.ValidationError('Informe um nome válido com pelo menos duas letras.')
        if (not config or config.validar_nome_seguro) and re.search(r"[^\wÀ-ÖØ-öø-ÿ' -]", nome, flags=re.UNICODE):
            raise forms.ValidationError('O nome pode conter apenas letras, espaços, hífen e apóstrofo.')
        return nome

    def clean_password1(self):
        password = self.cleaned_data.get('password1') or ''
        config = _seguranca()
        exigir_letra = not config or config.cadastro_senha_exigir_letra
        exigir_numero = not config or config.cadastro_senha_exigir_numero
        if exigir_letra and not re.search(r'[^\W_]', password, flags=re.UNICODE):
            raise forms.ValidationError('A palavra-passe deve conter pelo menos uma letra.')
        if exigir_numero and not re.search(r'\d', password):
            raise forms.ValidationError('A palavra-passe deve conter pelo menos um número.')
        return password

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remover o campo username (não usamos)
        if 'username' in self.fields:
            del self.fields['username']
        # Estilização dos campos
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class FormLogin(AuthenticationForm):
    """Formulário de login personalizado (login por email ou nome)."""
    username = forms.CharField(
        label='Email ou nome',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email ou nome completo'})
    )
    password = forms.CharField(
        label='Palavra-passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'})
    )

    def clean_username(self):
        identificador = (self.cleaned_data.get('username') or '').strip()
        config = _seguranca()
        if (not config or config.login_exigir_identificador_valido) and not re.search(r'[^\W_]', identificador, flags=re.UNICODE):
            raise forms.ValidationError('Informe um email ou nome válido, não apenas símbolos.')
        if config and not config.permitir_login_por_nome and '@' not in identificador:
            raise forms.ValidationError('O administrador configurou o acesso somente por email.')
        return identificador

    def clean_password(self):
        password = self.cleaned_data.get('password') or ''
        config = _seguranca()
        if (not config or config.login_exigir_senha_alfanumerica) and not re.search(r'[^\W_]', password, flags=re.UNICODE):
            raise forms.ValidationError('A palavra-passe não pode conter apenas símbolos.')
        return password


class FormEditarPerfil(forms.ModelForm):
    """Formulário para o utilizador editar o seu próprio perfil."""
    class Meta:
        model = Utilizador
        fields = ('nome_completo', 'telefone', 'foto_perfil')
        widgets = {
            'nome_completo': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'foto_perfil': forms.FileInput(attrs={'class': 'form-control'}),
        }


class FormSolicitarPerfil(forms.ModelForm):
    """Formulario para visitante solicitar acesso a um perfil do sistema."""

    class Meta:
        model = Utilizador
        fields = (
            'perfil_solicitado',
            'justificativa_solicitacao',
            'validacao_profissional',
            'cv_solicitacao',
        )
        widgets = {
            'perfil_solicitado': forms.Select(attrs={'class': 'form-control'}),
            'justificativa_solicitacao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Explique por que precisa deste perfil no sistema.',
            }),
            'validacao_profissional': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Responda às perguntas de validação conforme o perfil solicitado.',
            }),
            'cv_solicitacao': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'application/pdf,.pdf',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['perfil_solicitado'].choices = [
            ('agricultor', 'Agricultor'),
            ('cliente', 'Cliente'),
            ('consultor', 'Consultor Agrícola'),
            ('analista', 'Analista de Dados'),
            ('tecnico', 'Técnico de Campo'),
        ]

    def clean_cv_solicitacao(self):
        ficheiro = self.cleaned_data.get('cv_solicitacao')
        if not ficheiro:
            raise forms.ValidationError('Anexe o CV em PDF.')
        if not ficheiro.name.lower().endswith('.pdf'):
            raise forms.ValidationError('O CV deve ser enviado em formato PDF.')
        if ficheiro.size > 5 * 1024 * 1024:
            raise forms.ValidationError('O CV deve ter no máximo 5 MB.')
        return ficheiro


class FormMensagemSuporte(forms.ModelForm):
    class Meta:
        model = MensagemSuporte
        fields = ('categoria', 'assunto', 'mensagem')
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'assunto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Resuma o motivo da sua mensagem'}),
            'mensagem': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Explique o que aconteceu e como podemos ajudar.'}),
        }


class FormRespostaSuporte(forms.ModelForm):
    class Meta:
        model = MensagemSuporte
        fields = ('status', 'resposta_admin')
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'resposta_admin': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Escreva uma resposta clara para o utilizador.'}),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('status') == 'respondida' and not cleaned.get('resposta_admin', '').strip():
            self.add_error('resposta_admin', 'Escreva a resposta antes de marcar como respondida.')
        return cleaned
