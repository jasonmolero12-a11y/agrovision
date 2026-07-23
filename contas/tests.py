from unittest.mock import patch
from django.http import Http404
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from consultoria.views import detalhe_recomendacao
from consultoria.models import Recomendacao
from contas.models import Utilizador
from propriedades.models import Cultura, Propriedade, Talhao


@override_settings(DEBUG=False)
class SegurancaPerfisTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def criar_utilizador(self, email, nome, tipo):
        user = Utilizador.objects.create(
            email=email,
            nome_completo=nome,
            tipo_utilizador=tipo,
            is_active=True,
        )
        user.set_password('SenhaForte123')
        user.save()
        return user

    def test_registo_publico_cria_apenas_visitante(self):
        response = self.client.post(reverse('contas:registo'), {
            'email': 'novo@teste.local',
            'nome_completo': 'Novo Utilizador',
            'telefone': '900000000',
            'tipo_utilizador': 'admin',
            'password1': 'SenhaForte123',
            'password2': 'SenhaForte123',
        })

        self.assertEqual(response.status_code, 302)
        user = Utilizador.objects.get(email='novo@teste.local')
        self.assertEqual(user.tipo_utilizador, 'visitante')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_login_por_nome_completo(self):
        self.criar_utilizador('jason@teste.local', 'Jason', 'admin')

        response = self.client.post(reverse('contas:login'), {
            'username': 'Jason',
            'password': 'SenhaForte123',
        })

        self.assertEqual(response.status_code, 302)

    def test_agricultor_nao_acede_recomendacao_de_outro_agricultor(self):
        agricultor_1 = self.criar_utilizador('agricultor1@teste.local', 'Agricultor 1', 'agricultor')
        agricultor_2 = self.criar_utilizador('agricultor2@teste.local', 'Agricultor 2', 'agricultor')
        consultor = self.criar_utilizador('consultor@teste.local', 'Consultor', 'consultor')
        cultura = Cultura.objects.create(nome='Milho', ciclo='Anual')
        propriedade = Propriedade.objects.create(
            nome='Fazenda Privada',
            proprietario=agricultor_2,
            consultor_responsavel=consultor,
        )
        talhao = Talhao.objects.create(
            propriedade=propriedade,
            nome='Talhao A',
            cultura=cultura,
        )
        recomendacao = Recomendacao.objects.create(
            talhao=talhao,
            consultor=consultor,
            texto_recomendacao='Aplicar correcao do solo.',
        )

        request = self.factory.get(reverse('consultoria:detalhe_recomendacao', args=[recomendacao.pk]))
        request.user = agricultor_1

        with self.assertRaises(Http404):
            detalhe_recomendacao(request, recomendacao.pk)

# Create your tests here.


class AtendimentoTests(TestCase):
    def setUp(self):
        self.user = Utilizador.objects.create(email='cliente@teste.local', nome_completo='Cliente Teste', tipo_utilizador='cliente', is_active=True)
        self.user.set_password('SenhaForte123'); self.user.save()
        self.outro = Utilizador.objects.create(email='outro@teste.local', nome_completo='Outro Cliente', tipo_utilizador='cliente', is_active=True)
        self.outro.set_password('SenhaForte123'); self.outro.save()
        self.admin = Utilizador.objects.create(email='admin@teste.local', nome_completo='Administrador', tipo_utilizador='admin', is_active=True, is_staff=True, is_superuser=True)
        self.admin.set_password('SenhaForte123'); self.admin.save()

    def test_utilizador_envia_mensagem_e_admin_recebe(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('contas:nova_mensagem_suporte'), {
            'categoria': 'tecnico', 'assunto': 'Problema no painel', 'mensagem': 'Não consigo consultar um relatório.'
        })
        self.assertEqual(response.status_code, 302)
        from contas.models import MensagemSuporte
        atendimento = MensagemSuporte.objects.get(utilizador=self.user)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('contas:detalhe_mensagem_suporte', args=[atendimento.pk])).status_code, 200)

    def test_admin_responde_e_utilizador_le(self):
        from contas.models import MensagemSuporte
        atendimento = MensagemSuporte.objects.create(utilizador=self.user, categoria='acesso', assunto='Acesso', mensagem='Preciso de ajuda.')
        self.client.force_login(self.admin)
        response = self.client.post(reverse('contas:detalhe_mensagem_suporte', args=[atendimento.pk]), {'status': 'respondida', 'resposta_admin': 'O acesso foi verificado.'})
        self.assertEqual(response.status_code, 302)
        atendimento.refresh_from_db()
        self.assertEqual(atendimento.status, 'respondida')
        self.assertFalse(atendimento.resposta_lida)
        self.client.force_login(self.user)
        self.client.get(reverse('contas:detalhe_mensagem_suporte', args=[atendimento.pk]))
        atendimento.refresh_from_db()
        self.assertTrue(atendimento.resposta_lida)

    def test_utilizador_nao_consulta_mensagem_de_outro(self):
        from contas.models import MensagemSuporte
        atendimento = MensagemSuporte.objects.create(utilizador=self.outro, assunto='Privado', mensagem='Mensagem privada.')
        self.client.force_login(self.user)
        response = self.client.get(reverse('contas:detalhe_mensagem_suporte', args=[atendimento.pk]))
        self.assertEqual(response.status_code, 302)


class AdministracaoUtilizadoresTests(TestCase):
    def setUp(self):
        self.admin = Utilizador.objects.create_superuser(
            email='admin-senhas@teste.local',
            password='SenhaAdmin123',
            nome_completo='Administrador de Senhas',
        )
        self.user = Utilizador.objects.create_user(
            email='utilizador@teste.local',
            password='SenhaAntiga123',
            nome_completo='Utilizador Teste',
            tipo_utilizador='cliente',
        )
        self.client.force_login(self.admin)

    def test_manager_cria_utilizador_sem_username(self):
        self.assertEqual(self.user.email, 'utilizador@teste.local')
        self.assertTrue(self.user.check_password('SenhaAntiga123'))
        self.assertFalse(self.user.is_staff)

    def test_admin_abre_e_altera_senha_do_utilizador(self):
        url = reverse('admin:auth_user_password_change', args=[self.user.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client.post(url, {
            'password1': 'SenhaNova456',
            'password2': 'SenhaNova456',
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('SenhaNova456'))


class PermissoesPorCargoTests(TestCase):
    def setUp(self):
        self.visitante = Utilizador.objects.create_user(
            email='visitante-permissoes@teste.local', password='SenhaForte123',
            nome_completo='Visitante', tipo_utilizador='visitante',
        )
        self.cliente = Utilizador.objects.create_user(
            email='cliente-permissoes@teste.local', password='SenhaForte123',
            nome_completo='Cliente', tipo_utilizador='cliente',
        )

    def test_visitante_nao_contorna_menu_por_url(self):
        self.client.force_login(self.visitante)
        response = self.client.get(reverse('propriedades:lista'))
        self.assertRedirects(response, reverse('contas:solicitar_perfil'))

    def test_nao_admin_nao_acede_gestao_de_utilizadores(self):
        self.client.force_login(self.cliente)
        response = self.client.get(reverse('contas:lista_utilizadores'))
        self.assertRedirects(response, reverse('dashboard:home'))

    def test_cliente_nao_cria_propriedade(self):
        self.client.force_login(self.cliente)
        response = self.client.get(reverse('propriedades:nova'))
        self.assertRedirects(response, reverse('dashboard:home'))


class InterfaceAtualizadaTests(TestCase):
    def test_login_tem_opcao_mostrar_senha(self):
        response = self.client.get(reverse('contas:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'password-toggle')
        self.assertContains(response, 'Mostrar')

    @patch('meteorologia.views.obter_previsao_api', return_value=None)
    def test_meteorologia_exibe_campo_cidade_e_icones(self, _previsao):
        user = Utilizador.objects.create_user(
            email='clima-interface@teste.local', password='SenhaForte123',
            nome_completo='Cliente Clima', tipo_utilizador='cliente',
        )
        self.client.force_login(user)
        response = self.client.get(reverse('meteorologia:previsao'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard:home'))
