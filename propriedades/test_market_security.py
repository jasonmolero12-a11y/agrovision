from django.test import TestCase
from django.urls import reverse

from contas.forms import FormLogin, FormRegisto
from contas.models import Utilizador
from propriedades.models import Propriedade, PedidoCompra
from dashboard.views import _normalizar_resposta_chatbot


class SegurancaEntradaTests(TestCase):
    def test_registo_rejeita_nome_so_com_simbolos(self):
        form = FormRegisto(data={'email': 'simbolos@teste.ao', 'nome_completo': '@@@###', 'telefone': '', 'password1': 'Agro2026!', 'password2': 'Agro2026!'})
        self.assertFalse(form.is_valid())
        self.assertIn('nome_completo', form.errors)

    def test_registo_rejeita_senha_so_com_simbolos(self):
        form = FormRegisto(data={'email': 'senha@teste.ao', 'nome_completo': 'Pessoa Teste', 'telefone': '', 'password1': '!@#$%^&*()_+', 'password2': '!@#$%^&*()_+'})
        self.assertFalse(form.is_valid())
        self.assertIn('password1', form.errors)

    def test_login_rejeita_identificador_e_senha_so_com_simbolos(self):
        form = FormLogin(data={'username': '@@@', 'password': '###'})
        self.assertFalse(form.is_valid())

    def test_resposta_chatbot_remove_marcacao_e_expande_unidades(self):
        resposta = _normalizar_resposta_chatbot('## **Clima**: 32°C, vento 8 km/h e humidade 70% ✅')
        self.assertNotIn('#', resposta)
        self.assertNotIn('*', resposta)
        self.assertIn('32 graus Celsius', resposta)
        self.assertIn('quilómetros por hora', resposta)
        self.assertIn('70 por cento', resposta)


class MercadoAgricolaTests(TestCase):
    def setUp(self):
        self.cliente = Utilizador.objects.create_user(email='cliente@teste.ao', password='Cliente2026!', nome_completo='Cliente Teste', tipo_utilizador='cliente')
        self.agricultor = Utilizador.objects.create_user(email='agricultor@teste.ao', password='Agro2026!', nome_completo='Agricultor Teste', tipo_utilizador='agricultor')
        self.publica = Propriedade.objects.create(nome='Fazenda Pública', proprietario=self.agricultor, localizacao='Bengo', exposta_para_clientes=True, descricao_comercial='Milho de qualidade')
        self.privada = Propriedade.objects.create(nome='Fazenda Privada', proprietario=self.agricultor, exposta_para_clientes=False)

    def test_cliente_ve_apenas_propriedade_exposta(self):
        self.client.force_login(self.cliente)
        response = self.client.get(reverse('propriedades:mercado'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Fazenda Pública')
        self.assertNotContains(response, 'Fazenda Privada')

    def test_agricultor_nao_acede_ao_mercado_de_cliente(self):
        self.client.force_login(self.agricultor)
        response = self.client.get(reverse('propriedades:mercado'))
        self.assertEqual(response.status_code, 302)

    def test_cliente_pode_favoritar_e_remover_favorito(self):
        self.client.force_login(self.cliente)
        url = reverse('propriedades:mercado_favoritar', args=[self.publica.pk])
        self.client.post(url, {'next': reverse('propriedades:mercado')})
        self.assertTrue(self.publica.favoritada_por.filter(pk=self.cliente.pk).exists())
        self.client.post(url, {'next': reverse('propriedades:mercado')})
        self.assertFalse(self.publica.favoritada_por.filter(pk=self.cliente.pk).exists())

    def test_comparacao_ignora_propriedade_privada(self):
        self.client.force_login(self.cliente)
        response = self.client.get(reverse('propriedades:mercado_comparar'), {'itens': [self.publica.pk, self.privada.pk]})
        self.assertContains(response, 'Fazenda Pública')
        self.assertNotContains(response, 'Fazenda Privada')

    def test_filtro_por_localizacao(self):
        self.client.force_login(self.cliente)
        response = self.client.get(reverse('propriedades:mercado'), {'provincia': 'Bengo'})
        self.assertContains(response, 'Fazenda Pública')
        response = self.client.get(reverse('propriedades:mercado'), {'provincia': 'Huambo'})
        self.assertNotContains(response, 'Fazenda Pública')

    def test_pedido_compra_abre_formulario_comercial(self):
        self.client.force_login(self.cliente)
        response = self.client.get(reverse('propriedades:mercado_comprar', args=[self.publica.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pedido para Fazenda Pública')
        self.assertNotContains(response, 'Mensagem ou reclamação')

    def test_pedido_compra_cria_pedido_pendente(self):
        self.client.force_login(self.cliente)
        response = self.client.post(reverse('propriedades:mercado_comprar', args=[self.publica.pk]), {
            'quantidade': '500 quilogramas', 'contacto': '923000000', 'observacoes': 'Entrega no Bengo',
        })
        pedido = PedidoCompra.objects.get(cliente=self.cliente)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(pedido.status, 'pendente')
        self.assertEqual(pedido.quantidade_pretendida, '500 quilogramas')

    def test_fluxo_exige_confirmacao_do_agricultor(self):
        admin = Utilizador.objects.create_user(email='admin.compra@teste.ao', password='Admin123!', nome_completo='Admin Compra', tipo_utilizador='admin', is_staff=True)
        pedido = PedidoCompra.objects.create(cliente=self.cliente, propriedade=self.publica, contacto='923000000')
        self.client.force_login(admin)
        url = reverse('propriedades:responder_pedido_compra', args=[pedido.pk])
        self.client.post(url, {'acao': 'aprovar'})
        pedido.refresh_from_db()
        self.assertEqual(pedido.status, 'pendente')
        self.client.post(url, {'acao': 'contactar'})
        pedido.refresh_from_db()
        self.assertEqual(pedido.status, 'aguarda_agricultor')
        self.client.force_login(self.agricultor)
        self.client.post(url, {'acao': 'confirmar', 'nota': 'Produto disponível'})
        pedido.refresh_from_db()
        self.assertEqual(pedido.status, 'confirmado')
        self.client.force_login(admin)
        self.client.post(url, {'acao': 'aprovar'})
        pedido.refresh_from_db()
        self.assertEqual(pedido.status, 'aprovado')
        self.assertTrue(self.publica.clientes_autorizados.filter(pk=self.cliente.pk).exists())

    def test_pedido_compra_bloqueia_propriedade_privada(self):
        self.client.force_login(self.cliente)
        response = self.client.get(reverse('propriedades:mercado_comprar', args=[self.privada.pk]))
        self.assertEqual(response.status_code, 404)

    def test_favorito_nao_aceita_redirecionamento_externo(self):
        self.client.force_login(self.cliente)
        response = self.client.post(reverse('propriedades:mercado_favoritar', args=[self.publica.pk]), {'next': 'https://exemplo-malicioso.invalid/'})
        self.assertEqual(response.url, reverse('propriedades:mercado'))

