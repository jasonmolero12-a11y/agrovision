from django.test import TestCase

from config_sistema.models import ConfiguracaoAPI
from contas.forms import FormLogin, FormRegisto
from contas.models import Utilizador


class RegrasSegurancaConfiguraveisTests(TestCase):
    def test_admin_pode_desligar_validacao_de_nome_e_numero(self):
        config = ConfiguracaoAPI.carregar()
        config.validar_nome_seguro = False
        config.cadastro_senha_exigir_numero = False
        config.save()
        form = FormRegisto(data={'email': 'ajuste@teste.ao', 'nome_completo': '@@@', 'telefone': '', 'password1': 'PalavraForte!', 'password2': 'PalavraForte!'})
        self.assertTrue(form.is_valid(), form.errors.as_json())

    def test_admin_pode_exigir_login_apenas_por_email(self):
        config = ConfiguracaoAPI.carregar()
        config.permitir_login_por_nome = False
        config.save()
        user = Utilizador.objects.create_user(email='restrito@teste.ao', nome_completo='Nome Restrito', password='Senha2026!', tipo_utilizador='cliente')
        por_nome = FormLogin(data={'username': user.nome_completo, 'password': 'Senha2026!'})
        por_email = FormLogin(data={'username': user.email, 'password': 'Senha2026!'})
        self.assertFalse(por_nome.is_valid())
        self.assertTrue(por_email.is_valid(), por_email.errors.as_json())

    def test_protecoes_ficam_ativas_por_padrao(self):
        config = ConfiguracaoAPI.carregar()
        self.assertTrue(config.validar_nome_seguro)
        self.assertTrue(config.login_exigir_identificador_valido)
        self.assertTrue(config.login_exigir_senha_alfanumerica)
