import json, os, sys
from datetime import date, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','agrovision.settings')
import django
django.setup()
from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS: settings.ALLOWED_HOSTS.append('testserver')
from django.core.files import File
from django.db import transaction
from django.test import Client
from django.urls import reverse
from contas.models import Utilizador
from propriedades.models import Propriedade,Talhao,Cultura,RegistoProducao
from consultoria.models import Recomendacao,VisitaTecnica,FotoVisita,PragaDoenca
from meteorologia.models import RegistroClima,Alerta
from meteorologia.views import obter_previsao_api
BASE=Path(__file__).resolve().parents[1]
IMG=BASE/'static'/'img'
def anexar(campo, origem, nome):
    with open(IMG/origem,'rb') as f: campo.save(nome,File(f),save=False)
def status(resp): return {'http':resp.status_code,'destino':getattr(resp,'url','')}
users={n:Utilizador.objects.get(nome_completo__iexact=n) for n in ['Enock','Ado','Priscila','Garcia']}
with transaction.atomic():
    Propriedade.objects.filter(nome__icontains='teste').delete()
    Cultura.objects.filter(nome__icontains='teste').delete()
    RegistoProducao.objects.filter(campanha__icontains='demonstra').update(campanha='2025/2026',qualidade='Classe A',observacoes='Colheita registada com fotografia de campo.')
    prop=Propriedade.objects.filter(nome='Fazenda Horizonte do Kwanza').first()
    if prop: prop.delete()
    milho=Cultura.objects.get(nome='Milho')
    prop=Propriedade(nome='Fazenda Horizonte do Kwanza',proprietario=users['Enock'],consultor_responsavel=users['Ado'],localizacao='Cacuaco, Luanda',latitude='-8.775000',longitude='13.365000',area_total='24.50',exposta_para_clientes=True,descricao_comercial='Produção de milho com acompanhamento técnico, registo de colheita e controlo fitossanitário.')
    anexar(prop.foto_capa,'tst1.jpg','fazenda_horizonte_kwanza.jpg');prop.save()
    talhao=Talhao(propriedade=prop,nome='Talhão Nascente',cultura=milho,area='8.00',tipo_solo='Franco-arenoso',data_plantio=date.today()-timedelta(days=75),estadio_fenologico='Desenvolvimento vegetativo')
    anexar(talhao.foto_atual,'tst2.jpg','talhao_nascente.jpg');talhao.save()
    producao=RegistoProducao(talhao=talhao,campanha='2025/2026',data_colheita=date.today()-timedelta(days=30),quantidade='18.40',unidade='t',qualidade='Classe A',observacoes='Lote armazenado em local seco e ventilado.')
    anexar(producao.foto_colheita,'tst3.jpg','colheita_milho_2026.jpg');producao.save()
    praga=PragaDoenca(talhao=talhao,nome='Lagarta-do-cartucho',severidade='media',data_deteccao=date.today(),tratamento_sugerido='Monitorar a incidência, remover focos críticos e aplicar manejo integrado conforme orientação agronómica.',resolvido=False)
    anexar(praga.foto_diagnostico,'tst5.jpg','diagnostico_lagarta_cartucho.jpg');praga.save()
    visita=VisitaTecnica.objects.create(propriedade=prop,responsavel=users['Garcia'],data=date.today(),tipo='monitoramento',observacoes='Inspeção do desenvolvimento do milho, humidade do solo e presença de danos foliares.',recomendacao_campo='Repetir a contagem de plantas afetadas em 72 horas e manter rega conforme a condição meteorológica.')
    fv=FotoVisita(visita=visita,legenda='Vista geral observada durante a visita técnica');anexar(fv.imagem,'tst2.jpg','visita_talhao_nascente.jpg');fv.save()
    rec=Recomendacao(talhao=talhao,consultor=users['Ado'],dados_solo='Solo franco-arenoso. Confirmar pH e nutrientes com análise laboratorial antes da adubação corretiva.',dados_clima='Usar a consulta meteorológica atual e a previsão de sete dias antes de rega ou aplicação.',texto_recomendacao='Monitorar a lagarta-do-cartucho por amostragem. Priorizar manejo integrado, registar a evolução e reavaliar em 72 horas. Evitar aplicação com vento forte ou chuva prevista.',prioridade='media',status='emitida')
    anexar(rec.foto_evidencia,'tst4.jpg','evidencia_recomendacao_milho.jpg');rec.save()
    Alerta.objects.create(propriedade=prop,tipo='praga',severidade='aviso',mensagem='Foi detetada lagarta-do-cartucho no Talhão Nascente. Acompanhar a evolução e cumprir a recomendação emitida.',lido=False)
# Meteorologia real via provedor configurado
meteo=obter_previsao_api('Luanda')
meteo_ok=bool(meteo and not meteo.get('erro') and meteo.get('temperatura') is not None)
if meteo_ok:
    RegistroClima.objects.create(propriedade=prop,temperatura=meteo.get('temperatura'),humidade=meteo.get('humidade'),precipitacao=meteo.get('precipitacao'),vento_velocidade=meteo.get('vento'),descricao=meteo.get('descricao',''))
client=Client();resultado={'cenario':{'propriedade':prop.nome,'talhao':talhao.nome,'producao':producao.pk,'praga':praga.pk,'visita':visita.pk,'recomendacao':rec.pk},'meteorologia':{'real':meteo_ok,'provedor':meteo.get('provedor') if meteo else None,'cidade':meteo.get('cidade') if meteo else None,'erro':meteo.get('erro') if meteo else 'Sem resposta'},'perfis':{}}
rotas_leitura=['dashboard:home','propriedades:lista','propriedades:lista_talhoes','consultoria:lista_recomendacoes','consultoria:lista_visitas','consultoria:lista_pragas','meteorologia:previsao','meteorologia:lista_alertas','meteorologia:lista_registros','contas:mensagens_suporte']
for nome,user in users.items():
    client.logout();client.force_login(user)
    leituras={r:status(client.get(reverse(r))) for r in rotas_leitura}
    chatbot=client.post(reverse('dashboard:chatbot'),data=json.dumps({'mensagem':'Como posso usar as funções do meu perfil?'}),content_type='application/json')
    resultado['perfis'][nome]={'tipo':user.tipo_utilizador,'leituras':leituras,'chatbot':status(chatbot)}
# validações específicas
client.force_login(users['Enock']);resultado['perfis']['Enock']['propriedade_propria']=status(client.get(reverse('propriedades:detalhe',args=[prop.pk])));resultado['perfis']['Enock']['bloqueio_criar_recomendacao']=status(client.get(reverse('consultoria:nova_recomendacao')))
client.force_login(users['Ado']);resultado['perfis']['Ado']['criar_recomendacao']=status(client.get(reverse('consultoria:nova_recomendacao')));resultado['perfis']['Ado']['pdf']=status(client.get(reverse('consultoria:pdf_recomendacao',args=[rec.pk])))
client.force_login(users['Priscila']);resultado['perfis']['Priscila']['leitura_propriedade']=status(client.get(reverse('propriedades:detalhe',args=[prop.pk])));resultado['perfis']['Priscila']['bloqueio_edicao']=status(client.get(reverse('consultoria:nova_recomendacao')))
client.force_login(users['Garcia']);resultado['perfis']['Garcia']['criar_visita']=status(client.get(reverse('consultoria:nova_visita')));resultado['perfis']['Garcia']['criar_praga']=status(client.get(reverse('consultoria:nova_praga')));resultado['perfis']['Garcia']['bloqueio_recomendacao']=status(client.get(reverse('consultoria:nova_recomendacao')))
resultado['limpeza']={'propriedades_com_teste':Propriedade.objects.filter(nome__icontains='teste').count(),'culturas_com_teste':Cultura.objects.filter(nome__icontains='teste').count(),'campanhas_com_teste':RegistoProducao.objects.filter(campanha__icontains='teste').count(),'campanhas_demonstracao':RegistoProducao.objects.filter(campanha__icontains='demonstra').count()}
relatorio=BASE/'scripts'/'relatorio_validacao_sistema.json';relatorio.write_text(json.dumps(resultado,ensure_ascii=False,indent=2,default=str),encoding='utf-8');print(json.dumps(resultado,ensure_ascii=False,indent=2,default=str))
