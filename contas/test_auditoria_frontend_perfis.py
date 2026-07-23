from django.test import TestCase
from django.urls import reverse

from contas.models import Utilizador


class AuditoriaFrontendPorPerfilTests(TestCase):
    ROTAS = {
        'visitante': ['dashboard:home', 'solicitar_perfil', 'mensagens_suporte'],
        'admin': ['dashboard:home', 'lista_utilizadores', 'propriedades:lista'],
        'consultor': ['dashboard:home', 'consultoria:lista_recomendacoes', 'consultoria:lista_visitas'],
        'analista': ['dashboard:home', 'propriedades:lista', 'meteorologia:previsao'],
        'tecnico': ['dashboard:home', 'consultoria:lista_visitas', 'consultoria:lista_pragas'],
        'agricultor': ['dashboard:home', 'propriedades:lista', 'consultoria:consultoria_api_agricultor'],
        'cliente': ['dashboard:home', 'propriedades:mercado', 'mensagens_suporte'],
    }

    @classmethod
    def setUpTestData(cls):
        cls.utilizadores = {}
        for perfil in cls.ROTAS:
            cls.utilizadores[perfil] = Utilizador.objects.create_user(
                email=f'frontend.{perfil}@teste.ao', password='Teste123!',
                nome_completo=f'Frontend {perfil}', tipo_utilizador=perfil,
                is_staff=perfil == 'admin', is_superuser=perfil == 'admin',
            )

    def test_paginas_principais_renderizam_para_todos_os_perfis(self):
        for perfil, rotas in self.ROTAS.items():
            self.client.force_login(self.utilizadores[perfil])
            for rota in rotas:
                nome_rota = rota
                if rota in {
                    'solicitar_perfil',
                    'mensagens_suporte',
                    'lista_utilizadores',
                }:
                    nome_rota = f'contas:{rota}'
                resposta = self.client.get(reverse(nome_rota), follow=True)
                self.assertEqual(resposta.status_code, 200, f'{perfil}: {rota}')
                self.assertNotContains(resposta, 'Traceback')
                self.assertContains(resposta, 'AgroVision')

    def test_layout_interno_tem_acessibilidade_e_componentes_globais(self):
        for perfil, utilizador in self.utilizadores.items():
            self.client.force_login(utilizador)
            resposta = self.client.get(reverse('dashboard:home'))
            conteudo = resposta.content.decode('utf-8')
            self.assertIn('viewport', conteudo.lower(), perfil)
            self.assertIn('agro-chatbot-config', conteudo, perfil)
            self.assertIn('Sair', conteudo, perfil)
