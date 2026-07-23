from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from contas.models import Utilizador
from meteorologia.models import RegistroClima
from propriedades.models import Cultura, Propriedade, Talhao


class ConsultoriaAPIAgricultorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.agricultor = Utilizador.objects.create_user(email='agricultor.api@teste.ao', password='Teste123!', nome_completo='Agricultor API', tipo_utilizador='agricultor')
        cls.outro = Utilizador.objects.create_user(email='outro.api@teste.ao', password='Teste123!', nome_completo='Outro Agricultor', tipo_utilizador='agricultor')
        cls.cliente = Utilizador.objects.create_user(email='cliente.api@teste.ao', password='Teste123!', nome_completo='Cliente API', tipo_utilizador='cliente')
        cls.cultura = Cultura.objects.create(nome='Milho API', ciclo='Anual')
        cls.propriedade = Propriedade.objects.create(nome='Fazenda API', proprietario=cls.agricultor, localizacao='Luanda')
        cls.talhao = Talhao.objects.create(propriedade=cls.propriedade, nome='Talhão API', cultura=cls.cultura, tipo_solo='Argiloso')
        cls.alheia = Propriedade.objects.create(nome='Fazenda Alheia API', proprietario=cls.outro, localizacao='Bengo')
        cls.talhao_alheio = Talhao.objects.create(propriedade=cls.alheia, nome='Talhão Alheio API', cultura=cls.cultura)

    @patch('consultoria.views._sugestao_recomendacao_automatica', return_value='Orientação segura para revisão.')
    @patch('consultoria.views.obter_previsao_api')
    def test_agricultor_gera_orientacao_com_clima_real(self, api_mock, _sugestao):
        api_mock.return_value = {
            'provedor': 'Open-Meteo', 'cidade': 'Luanda', 'provincia': 'Luanda',
            'temperatura': 31, 'humidade': 70, 'vento': 12, 'precipitacao': 0,
            'descricao': 'Parcialmente nublado', 'consultado_em': '22/07/2026 10:00',
            'resumo_7_dias': {'chuva_total': 4},
        }
        self.client.force_login(self.agricultor)
        resposta = self.client.post(reverse('consultoria:consultoria_api_agricultor'), {'talhao': self.talhao.pk, 'acao': 'consultar'})
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Orientação preliminar AgroVision')
        self.assertContains(resposta, 'resultado-agrovision-voz')
        self.assertContains(resposta, 'agrovision-auto-speech')
        self.assertTrue(RegistroClima.objects.filter(propriedade=self.propriedade).exists())

    def test_consultoria_mostra_possiveis_doencas_sem_confirmar_diagnostico(self):
        from consultoria.views import _possiveis_doencas_api
        itens = _possiveis_doencas_api(self.talhao, {'temperatura': 29, 'humidade': 88, 'precipitacao': 8})
        self.assertTrue(any('ferrugem' in item['nome'] for item in itens))
        self.assertTrue(all('acao' in item for item in itens))

    @patch('consultoria.views._sugestao_recomendacao_automatica', return_value='Orientação AgroVision para revisão.')
    @patch('consultoria.views.obter_previsao_api')
    def test_analise_agrovision_vira_rascunho_sem_nova_consulta(self, api_mock, _sugestao):
        from consultoria.models import Recomendacao
        consultor = Utilizador.objects.create_user(email='consultor.api@teste.ao', password='Teste123!', nome_completo='Consultor AgroVision', tipo_utilizador='consultor')
        self.propriedade.consultor_responsavel = consultor
        self.propriedade.save(update_fields=['consultor_responsavel'])
        RegistroClima.objects.create(propriedade=self.propriedade, temperatura=30, humidade=75, vento_velocidade=12, descricao='Parcialmente nublado')
        self.client.force_login(self.agricultor)
        resposta = self.client.post(reverse('consultoria:enviar_analise_consultor', args=[self.talhao.pk]))
        self.assertEqual(resposta.status_code, 302)
        api_mock.assert_not_called()
        rec = Recomendacao.objects.get(talhao=self.talhao, consultor=consultor)
        self.assertEqual(rec.status, 'rascunho')
        self.assertTrue(rec.texto_recomendacao.startswith('Análise AgroVision solicitada'))
        estado = self.client.get(
            reverse('consultoria:consultoria_api_agricultor'),
            {'talhao': self.talhao.pk},
        )
        self.assertContains(estado, 'Aguardando resposta do consultor')
        lista_agricultor = self.client.get(reverse('consultoria:lista_recomendacoes'))
        self.assertNotContains(lista_agricultor, 'Análise AgroVision solicitada')
        self.client.force_login(consultor)
        lista_consultor = self.client.get(reverse('consultoria:lista_recomendacoes'))
        self.assertContains(lista_consultor, self.talhao.nome)
        painel_consultor = self.client.get(reverse('dashboard:home'))
        self.assertContains(painel_consultor, 'Avaliar e responder')
        self.assertContains(
            painel_consultor,
            reverse('consultoria:responder_recomendacao', args=[rec.pk]),
        )
        self.assertNotContains(
            painel_consultor,
            reverse('consultoria:pdf_recomendacao', args=[rec.pk]),
        )

        self.client.force_login(self.agricultor)
        pdf_rascunho = self.client.get(reverse('consultoria:pdf_recomendacao', args=[rec.pk]))
        self.assertRedirects(pdf_rascunho, reverse('consultoria:lista_recomendacoes'))

    def test_agricultor_nao_consulta_talhao_alheio(self):
        self.client.force_login(self.agricultor)
        resposta = self.client.post(reverse('consultoria:consultoria_api_agricultor'), {'talhao': self.talhao_alheio.pk})
        self.assertEqual(resposta.status_code, 404)

    @patch('consultoria.views._sugestao_recomendacao_automatica', return_value='Orientação localizada.')
    @patch('consultoria.views.obter_previsao_api')
    def test_consultoria_tenta_localizacao_com_angola(self, api_mock, _sugestao):
        api_mock.side_effect = [None, {
            'provedor': 'Open-Meteo', 'cidade': 'Cacuaco', 'provincia': 'Luanda',
            'temperatura': 30, 'humidade': 72, 'vento': 10, 'precipitacao': 0,
            'descricao': 'Céu parcialmente nublado', 'consultado_em': '23/07/2026 10:00',
            'resumo_7_dias': {'chuva_total': 1},
        }]
        self.propriedade.localizacao = 'Cacuaco'
        self.propriedade.save(update_fields=['localizacao'])
        self.client.force_login(self.agricultor)
        resposta = self.client.post(
            reverse('consultoria:consultoria_api_agricultor'),
            {'talhao': self.talhao.pk, 'acao': 'consultar'},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Orientação localizada')
        self.assertEqual(api_mock.call_args_list[1].args[0], 'Cacuaco, Angola')

    def test_consultor_responde_emite_e_agricultor_recebe(self):
        from consultoria.models import Recomendacao
        consultor = Utilizador.objects.create_user(
            email='resposta@teste.ao', password='Teste123!',
            nome_completo='Consultor Resposta', tipo_utilizador='consultor',
        )
        self.propriedade.consultor_responsavel = consultor
        self.propriedade.save(update_fields=['consultor_responsavel'])
        rec = Recomendacao.objects.create(
            talhao=self.talhao, consultor=consultor, status='rascunho',
            texto_recomendacao='Análise AgroVision solicitada pelo agricultor para revisão.',
        )
        self.client.force_login(consultor)
        resposta = self.client.post(
            reverse('consultoria:responder_recomendacao', args=[rec.pk]),
            {
                'dados_solo': 'Solo revisto pelo consultor.',
                'dados_clima': 'Clima revisto pelo consultor.',
                'prioridade': 'alta',
                'texto_recomendacao': 'Resposta técnica final para o agricultor.',
            },
        )
        self.assertRedirects(resposta, reverse('consultoria:detalhe_recomendacao', args=[rec.pk]))
        rec.refresh_from_db()
        self.assertEqual(rec.status, 'rascunho')
        self.assertEqual(rec.texto_recomendacao, 'Resposta técnica final para o agricultor.')

        emissao = self.client.post(reverse('consultoria:emitir_recomendacao', args=[rec.pk]))
        self.assertRedirects(emissao, reverse('consultoria:detalhe_recomendacao', args=[rec.pk]))
        rec.refresh_from_db()
        self.assertEqual(rec.status, 'emitida')

        self.client.force_login(self.agricultor)
        estado = self.client.get(
            reverse('consultoria:consultoria_api_agricultor'),
            {'talhao': self.talhao.pk},
        )
        self.assertContains(estado, 'O consultor já respondeu')
        self.assertContains(estado, reverse('consultoria:pdf_recomendacao', args=[rec.pk]))

    def test_cliente_nao_acede_consultoria_do_agricultor(self):
        self.client.force_login(self.cliente)
        resposta = self.client.get(reverse('consultoria:consultoria_api_agricultor'))
        self.assertEqual(resposta.status_code, 302)
