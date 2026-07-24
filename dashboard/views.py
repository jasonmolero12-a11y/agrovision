"""
Views da app dashboard - Painel principal por perfil.

Após login, o utilizador é redirecionado para cá. Conforme o tipo de
utilizador, é mostrado um dashboard diferente:
  - Admin      → visão geral do sistema + gestão
  - Consultor  → recomendações e visitas
  - Analista   → gráficos e estatísticas
  - Técnico    → inserção de dados de campo
  - Agricultor → consultas e alertas
  - Cliente    → relatórios, recomendações e histórico
  - Visitante  → solicita acesso
"""

import json
import re

from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from contas.models import Utilizador
from propriedades.models import Propriedade, Talhao, Cultura, RegistoProducao, PedidoCompra
from consultoria.models import Recomendacao, VisitaTecnica, PragaDoenca
from meteorologia.models import RegistroClima, Alerta
from config_sistema.ia import gerar_texto_ia
from .models import RespostaChatbot


def _contexto_limitado_chatbot(user):
    """Resumo seguro por perfil. Nao expõe dados fora do acesso do utilizador."""
    if user.is_admin or user.is_superuser:
        return {
            'perfil': 'Administrador',
            'resumo': {
                'utilizadores': Utilizador.objects.count(),
                'propriedades': Propriedade.objects.count(),
                'recomendacoes': Recomendacao.objects.count(),
                'alertas_ativos': Alerta.objects.filter(lido=False).count(),
            },
            'atalhos': ['utilizadores', 'configuracao da api', 'propriedades', 'relatorios'],
        }

    if user.is_visitante:
        return {
            'perfil': 'Visitante',
            'resumo': {
                'status_solicitacao': user.get_status_solicitacao_display(),
                'perfil_solicitado': user.get_perfil_solicitado_display() if user.perfil_solicitado else 'Nenhum',
            },
            'atalhos': ['solicitar perfil', 'cv em pdf', 'aguardar aprovacao'],
        }

    if user.is_consultor:
        propriedades = Propriedade.objects.filter(consultor_responsavel=user)
        return {
            'perfil': 'Consultor Agricola',
            'resumo': {
                'propriedades_atribuidas': propriedades.count(),
                'recomendacoes': Recomendacao.objects.filter(consultor=user).count(),
                'visitas': VisitaTecnica.objects.filter(responsavel=user).count(),
                'pragas_ativas': PragaDoenca.objects.filter(
                    resolvido=False,
                    talhao__propriedade__in=propriedades,
                ).count(),
            },
            'atalhos': ['recomendacoes', 'visitas', 'pragas', 'meteorologia'],
        }

    if user.is_agricultor:
        propriedades = Propriedade.objects.filter(proprietario=user)
        return {
            'perfil': 'Agricultor',
            'resumo': {
                'minhas_propriedades': propriedades.count(),
                'recomendacoes': Recomendacao.objects.filter(talhao__propriedade__in=propriedades).count(),
                'alertas_ativos': Alerta.objects.filter(propriedade__in=propriedades, lido=False).count(),
            },
            'atalhos': ['minhas propriedades', 'alertas', 'recomendacoes', 'meteorologia'],
        }

    if user.is_cliente:
        fornecedores = Propriedade.objects.filter(clientes_autorizados=user)
        return {
            'perfil': 'Cliente Comprador',
            'resumo': {
                'fornecedores_autorizados': fornecedores.count(),
                'lotes_producao': RegistoProducao.objects.filter(talhao__propriedade__in=fornecedores).count(),
            },
            'atalhos': ['mercado agrícola', 'ofertas', 'favoritos', 'pedidos de compra'],
        }

    if user.is_tecnico:
        return {
            'perfil': 'Tecnico de Campo',
            'resumo': {
                'minhas_visitas': VisitaTecnica.objects.filter(responsavel=user).count(),
                'pragas_registadas': PragaDoenca.objects.count(),
            },
            'atalhos': ['visitas', 'pragas', 'meteorologia'],
        }

    return {
        'perfil': 'Analista de Dados',
        'resumo': {
            'propriedades': Propriedade.objects.count(),
            'talhoes': Talhao.objects.count(),
            'culturas': Cultura.objects.count(),
            'registos_clima': RegistroClima.objects.count(),
        },
        'atalhos': ['dashboard', 'indicadores', 'meteorologia'],
    }


def _perfil_codigo(user):
    if user.is_admin or user.is_superuser:
        return 'admin'
    if user.is_visitante:
        return 'visitante'
    if user.is_consultor:
        return 'consultor'
    if user.is_agricultor:
        return 'agricultor'
    if user.is_cliente:
        return 'cliente'
    if user.is_tecnico:
        return 'tecnico'
    return 'analista'


def _normalizar_resposta_chatbot(texto):
    texto = str(texto or '')
    texto = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', texto)
    texto = re.sub(r'https?://\S+', '', texto)
    texto = re.sub(r'[\*#_~|^<>{}\[\]]+', ' ', texto)
    texto = re.sub(r'^[\s•●▪►▶✓✔✅⚠🌱🌾\-]+', '', texto, flags=re.MULTILINE)
    texto = re.sub(r'°\s*C\b', ' graus Celsius', texto, flags=re.IGNORECASE)
    texto = re.sub(r'km\s*/\s*h', ' quilómetros por hora', texto, flags=re.IGNORECASE)
    texto = re.sub(r'\bmm\b', ' milímetros', texto, flags=re.IGNORECASE)
    texto = re.sub(r'\bha\b', ' hectares', texto, flags=re.IGNORECASE)
    texto = re.sub(r'(\d+(?:[.,]\d+)?)\s*%', r'\1 por cento', texto)
    return re.sub(r'\s+', ' ', texto).strip()

def _resposta_editavel(pergunta, user):
    texto = pergunta.lower()
    perfil = _perfil_codigo(user)
    regras = RespostaChatbot.objects.filter(ativo=True, perfil__in=['todos', perfil])
    for regra in regras:
        palavras = [p.strip().lower() for p in regra.palavras_chave.split(',') if p.strip()]
        if any(palavra in texto for palavra in palavras):
            return regra.resposta
    return None


def _guia_agricola_programado(pergunta):
    """Guia básico disponível mesmo quando a IA externa não está configurada."""
    texto = pergunta.lower()
    for erro, correto in {
        'temote': 'tomate', 'tamate': 'tomate', 'tomati': 'tomate',
        'mandioka': 'mandioca', 'feijam': 'feijão', 'soia': 'soja',
    }.items():
        texto = texto.replace(erro, correto)
    termos = [
        'plantar', 'plantio', 'semear', 'semente', 'cultivar', 'cultivo',
        'solo', 'adubo', 'fertiliz', 'rega', 'irrig', 'colheita',
        'milho', 'mandioca', 'feijão', 'feijao', 'tomate', 'café', 'cafe',
        'soja', 'batata', 'cebola', 'arroz', 'banana', 'amendoim',
    ]
    if not any(t in texto for t in termos):
        return None
    culturas = {
        'milho': 'Passo 1: escolha uma área ensolarada e confirme que o solo drena bem. Passo 2: use sementes sadias e prepare o solo sem destruir toda a cobertura. Passo 3: plante no início das chuvas e siga o espaçamento indicado para a variedade. Passo 4: acompanhe falhas de germinação, ervas e necessidade de água. Passo 5: observe lagartas, ferrugem e manchas nas folhas. Passo 6: colha quando os grãos atingirem o ponto adequado ao uso pretendido.',
        'mandioca': 'Passo 1: escolha terreno solto, drenado e sem histórico recente de podridão. Passo 2: selecione manivas sadias de plantas produtivas. Passo 3: prepare e plante as manivas na época com humidade suficiente. Passo 4: controle ervas principalmente nos primeiros meses. Passo 5: observe mosaico, ácaros e podridão das raízes. Passo 6: planeie a colheita conforme a variedade e o mercado.',
        'feijão': 'Passo 1: escolha solo drenado e faça rotação de culturas. Passo 2: use sementes sadias da variedade adequada ao local. Passo 3: plante com humidade suficiente, sem encharcar. Passo 4: acompanhe ervas e água durante floração e formação das vagens. Passo 5: observe ferrugem, antracnose e insetos. Passo 6: colha quando as vagens estiverem maduras e seque os grãos corretamente.',
        'feijao': 'Passo 1: escolha solo drenado e faça rotação de culturas. Passo 2: use sementes sadias da variedade adequada ao local. Passo 3: plante com humidade suficiente, sem encharcar. Passo 4: acompanhe ervas e água durante floração e formação das vagens. Passo 5: observe ferrugem, antracnose e insetos. Passo 6: colha quando as vagens estiverem maduras e seque os grãos corretamente.',
        'tomate': 'Passo 1: escolha local ventilado, ensolarado e com boa drenagem. Passo 2: produza ou compre mudas sadias. Passo 3: transplante com cuidado e instale tutoramento. Passo 4: regue junto ao solo e evite molhar folhas no fim do dia. Passo 5: observe míldio, pinta-preta, murcha e insetos. Passo 6: colha os frutos no ponto exigido pelo mercado.',
        'café': 'Passo 1: avalie altitude, chuva, sombra e drenagem da área. Passo 2: escolha variedade e mudas sadias adequadas ao local. Passo 3: prepare covas e plante no início do período chuvoso. Passo 4: conserve a humidade, controle ervas e ajuste a sombra. Passo 5: observe ferrugem, broca e nutrição das plantas. Passo 6: colha apenas frutos no ponto adequado e faça o processamento com higiene.',
        'cafe': 'Passo 1: avalie altitude, chuva, sombra e drenagem da área. Passo 2: escolha variedade e mudas sadias adequadas ao local. Passo 3: prepare covas e plante no início do período chuvoso. Passo 4: conserve a humidade, controle ervas e ajuste a sombra. Passo 5: observe ferrugem, broca e nutrição das plantas. Passo 6: colha apenas frutos no ponto adequado e faça o processamento com higiene.',
        'soja': 'Passo 1: confirme drenagem e análise do solo. Passo 2: escolha semente certificada e variedade adaptada. Passo 3: plante no início da época chuvosa conforme profundidade e espaçamento da variedade. Passo 4: acompanhe germinação, ervas e água na floração. Passo 5: observe lagartas, percevejos, ferrugem e manchas. Passo 6: colha quando vagens e grãos atingirem maturidade.',
        'batata': 'Passo 1: escolha solo solto e drenado. Passo 2: use material de plantio sadio. Passo 3: prepare camalhões e plante com humidade moderada. Passo 4: faça amontoa e evite encharcamento. Passo 5: observe manchas, murcha, podridão e insetos. Passo 6: colha sem ferir os tubérculos.',
        'cebola': 'Passo 1: escolha terreno ensolarado e drenado. Passo 2: use sementes ou mudas sadias. Passo 3: transplante sem enterrar excessivamente. Passo 4: mantenha humidade regular e reduza a rega perto da colheita. Passo 5: observe tripes, manchas e podridões. Passo 6: colha quando as folhas tombarem e faça a cura.',
        'arroz': 'Passo 1: escolha variedade para sequeiro ou irrigado. Passo 2: prepare solo, água e drenagem. Passo 3: use sementes sadias e plante na época indicada. Passo 4: controle ervas e água nas fases críticas. Passo 5: observe brusone, manchas, aves e insetos. Passo 6: colha os grãos maduros e seque corretamente.',
        'banana': 'Passo 1: escolha local quente e sem encharcamento. Passo 2: use mudas sadias. Passo 3: prepare covas com matéria orgânica decomposta. Passo 4: mantenha cobertura, água e controle de rebentos. Passo 5: observe sigatoka, murchas e danos no caule. Passo 6: colha no ponto adequado ao transporte.',
        'amendoim': 'Passo 1: escolha solo leve e drenado. Passo 2: use sementes sadias. Passo 3: plante com boa humidade. Passo 4: controle ervas cedo. Passo 5: observe manchas, podridões e insetos. Passo 6: colha vagens maduras e seque com higiene.',
    }
    for nome, orientacao in culturas.items():
        if nome in texto:
            definicoes = {
                'tomate': 'O tomate é uma hortaliça de fruto cultivada para consumo fresco e processamento.',
                'mandioca': 'A mandioca é uma cultura tropical de raiz usada na alimentação, farinha, fécula e indústria.',
                'feijão': 'O feijão é uma leguminosa alimentar rica em proteína.',
                'feijao': 'O feijão é uma leguminosa alimentar rica em proteína.',
                'soja': 'A soja é uma leguminosa oleaginosa usada em alimentação, óleo, ração e indústria.',
            }
            introducao = definicoes.get(
                nome,
                f'{nome.capitalize()} é uma cultura cujo manejo deve ser adaptado ao clima, solo e variedade.',
            )
            return f'{introducao} Mentoria inicial para cultivar {nome}. {orientacao} Para adaptar estes passos à sua fazenda, diga a localização, o tamanho da área, o tipo de solo, a disponibilidade de água e a época em que pretende plantar. Antes de aplicar fertilizante ou defensivo, confirme a análise do solo e valide a decisão com o técnico ou consultor.'
    if 'solo' in texto or 'adubo' in texto or 'fertiliz' in texto:
        return 'Para conhecer o solo, recolha amostras em vários pontos e peça análise de acidez, matéria orgânica e nutrientes. Textura, drenagem e cultura determinam a correção. Não indique dose de calcário ou adubo sem análise laboratorial e área correta.'
    if 'rega' in texto or 'irrig' in texto:
        return 'A rega depende da cultura, fase, solo e clima. Verifique a humidade abaixo da superfície, regue de manhã quando necessário e evite encharcamento. Use a meteorologia do AgroVision e confirme a necessidade no talhão.'
    return 'Para orientar o plantio com segurança, informe a cultura, localização, tipo de solo, área, época, disponibilidade de água e se já existe análise do solo. O guia poderá então explicar preparação, semente, rega, cuidados e colheita.'


def _ajuda_funcional_por_perfil(pergunta, contexto):
    """Explica as funções efetivamente autorizadas para o perfil atual."""
    texto = (pergunta or '').casefold()
    gatilhos = (
        'o que posso fazer',
        'minhas funções',
        'minhas funcoes',
        'como usar o sistema',
        'como funciona meu painel',
        'ajuda no painel',
    )
    if not any(gatilho in texto for gatilho in gatilhos):
        return None

    perfil = str(contexto.get('perfil', 'Visitante')).casefold()
    orientacoes = {
        'visitante': (
            'Como visitante, pode conhecer o AgroVision, solicitar um perfil '
            'profissional e falar com a administração pelo atendimento.'
        ),
        'cliente comprador': (
            'Como cliente comprador, pode consultar o Mercado Agrícola, ver '
            'propriedades e colheitas publicadas, manifestar interesse de compra '
            'e acompanhar a autorização da administração.'
        ),
        'agricultor': (
            'Como agricultor, pode cadastrar e editar as suas propriedades e '
            'talhões, registar culturas e colheitas, consultar meteorologia, usar '
            'a Consultoria Inteligente AgroVision, enviar a análise ao consultor '
            'e acompanhar recomendações, alertas e a equipa atribuída.'
        ),
        'consultor agrícola': (
            'Como consultor, pode acompanhar agricultores atribuídos, avaliar '
            'análises da Consultoria Inteligente, consultar propriedades, visitas '
            'e pragas, e criar, rever e emitir recomendações agrícolas.'
        ),
        'técnico de campo': (
            'Como técnico de campo, pode consultar propriedades atribuídas, '
            'registar visitas com fotografias, comunicar pragas ou doenças e '
            'acompanhar alertas operacionais.'
        ),
        'analista de dados': (
            'Como analista de dados, pode analisar propriedades, talhões, produção, '
            'clima, solo, pragas e relatórios autorizados, apoiando a decisão da equipa.'
        ),
        'administrador': (
            'Como administrador, pode gerir utilizadores, perfis, permissões, equipas, '
            'atribuições, propriedades, pedidos comerciais, recomendações, alertas, '
            'mensagens e os serviços externos e APIs do AgroVision.'
        ),
    }
    return orientacoes.get(perfil, orientacoes['visitante'])


def _resposta_programada(pergunta, contexto):
    ajuda_perfil = _ajuda_funcional_por_perfil(pergunta, contexto)
    if ajuda_perfil:
        return ajuda_perfil
    texto = pergunta.lower()
    perfil = contexto['perfil']
    resumo = contexto['resumo']

    guia = _guia_agricola_programado(pergunta)
    if guia:
        return guia

    if any(p in texto for p in ['ola', 'olá', 'bom dia', 'boa tarde', 'boa noite', 'ajuda']):
        return (
            f"Ola. Sou o assistente AgroVision. O seu perfil atual e {perfil}. "
            "Posso explicar o seu painel, orientar sobre propriedades, recomendacoes, visitas, meteorologia, alertas e solicitacao de perfil."
        )

    if 'perfil' in texto or 'solicita' in texto or 'aprova' in texto:
        if perfil == 'Visitante':
            return (
                f"O seu estado e {resumo.get('status_solicitacao')}. "
                "Para ganhar acesso, abra Solicitar Perfil, escolha o perfil, responda a validacao profissional e anexe o CV em PDF. "
                "Depois aguarde a aprovacao do administrador."
            )
        return f"O seu perfil aprovado e {perfil}. As informacoes do sistema sao limitadas ao seu nivel de acesso."

    if 'mercado' in texto or 'comprar' in texto or 'oferta' in texto:
        if perfil == 'Cliente Comprador':
            return 'Abra Mercado Agrícola para ver, em cartões com fotografia, apenas as propriedades publicadas para compradores. Pode pesquisar por produto ou localização, consultar colheitas e enviar uma mensagem de interesse.'
        return 'O Mercado Agrícola apresenta aos clientes somente propriedades que o administrador marcou como expostas. Dados privados e técnicos permanecem protegidos.'

    if 'produção' in texto or 'producao' in texto or 'colheita' in texto:
        return 'Os registos de produção guardam campanha, data de colheita, quantidade, unidade, qualidade, observações e fotografia. Cada perfil vê apenas os dados autorizados.'

    if 'mensagem' in texto or 'reclama' in texto or 'suporte' in texto:
        return 'Na área Mensagens pode enviar uma solicitação ou reclamação e acompanhar a resposta da administração.'

    if 'foto' in texto or 'imagem' in texto:
        return 'As fotografias comprovam o estado da propriedade, talhão, colheita, visita e ocorrência de praga. Envie imagens nítidas e atuais.'

    if 'propriedade' in texto or 'talhao' in texto or 'talhão' in texto:
        valor = resumo.get('minhas_propriedades', resumo.get('propriedades_atribuidas', resumo.get('propriedades', 0)))
        return f"Com o seu perfil {perfil}, o sistema mostra {valor} propriedade(s) dentro do seu acesso autorizado."

    if 'recomend' in texto:
        return f"No seu acesso atual existem {resumo.get('recomendacoes', 0)} recomendacao(oes) relacionadas ao seu perfil."

    if 'relatorio' in texto or 'relatório' in texto or 'cliente' in texto:
        if perfil == 'Cliente Comprador':
            return (
                f"Como cliente comprador, tem {resumo.get('fornecedores_autorizados', 0)} fornecedor ou fornecedores autorizados, "
                f"{resumo.get('lotes_producao', 0)} registos de produção disponíveis. "
                "Pode avaliar ofertas, qualidade e enviar pedidos de compra, mas não pode alterar dados técnicos da fazenda."
            )
        return "Os relatórios ficam limitados ao perfil aprovado e aos dados autorizados para esse utilizador."

    if 'visita' in texto:
        return f"No seu acesso atual existem {resumo.get('visitas', resumo.get('minhas_visitas', 0))} visita(s) tecnica(s) relacionadas ao seu perfil."

    if 'alerta' in texto:
        return f"Existem {resumo.get('alertas_ativos', 0)} alerta(s) ativo(s) dentro do seu acesso."

    if 'clima' in texto or 'meteor' in texto or 'chuva' in texto:
        return "Use o modulo Meteorologia para consultar previsao. O sistema pode guardar historico climatico e gerar alertas simples por regras."

    if 'risco' in texto or 'inteligente' in texto or 'sugest' in texto or 'automatica' in texto or 'automática' in texto:
        return (
            "O sistema possui um motor de regras inicial. Ele cruza clima, alertas e pragas para estimar risco agronomico "
            "e preencher uma recomendacao preliminar que o consultor deve rever antes de emitir."
        )

    if 'grafico' in texto or 'gráfico' in texto or 'historico' in texto or 'histórico' in texto:
        return "No historico de clima existe um grafico com temperatura, humidade e vento dos registos climaticos autorizados para o seu perfil."

    if 'api' in texto or 'inteligente' in texto or 'ia' in texto:
        return (
            "O chatbot ja esta preparado para uma API externa, mas a integracao deve receber apenas um resumo limitado pelo perfil. "
            "Isso impede que uma API veja dados de outros utilizadores."
        )

    return (
        f"Entendi a pergunta, mas so posso responder com dados autorizados para o perfil {perfil}. "
        f"Pode perguntar sobre: {', '.join(contexto['atalhos'])}."
    )


@login_required
def chatbot_responder(request):
    """Endpoint interno do chatbot com contexto limitado por perfil."""
    if request.method != 'POST':
        return JsonResponse({'erro': 'Metodo nao permitido.'}, status=405)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'erro': 'Pedido invalido.'}, status=400)

    pergunta = (payload.get('mensagem') or '').strip()
    historico = payload.get('historico') or []
    if not isinstance(historico, list):
        historico = []
    historico = [str(item)[:500] for item in historico[-6:]]
    if not pergunta:
        return JsonResponse({'resposta': 'Escreva uma pergunta para eu ajudar.'})

    contexto = _contexto_limitado_chatbot(request.user)
    contexto_texto = json.dumps(contexto, ensure_ascii=False)
    historico_texto = ' | '.join(historico) or 'Sem conversa anterior.'
    resposta_ia = gerar_texto_ia(
        pergunta,
        contexto=(
            "Você é o assistente interno atualizado do AgroVision, uma plataforma de gestão e inteligência agrícola. "
            "Converse de forma acolhedora, social, respeitosa e explicativa. Reconheça a dúvida, responda em etapas curtas e termine com uma pergunta útil quando faltar contexto. "
            "Não use Markdown, asteriscos, cardinal, sublinhados, listas com símbolos, emojis ou sinais técnicos. "
            "Escreva unidades por extenso para leitura por voz. Explique apenas funções permitidas ao perfil. "
            "O cliente é comprador: consulta mercado, fornecedores, produção e qualidade e envia pedidos de compra, sem alterar dados técnicos. "
            "Responda perguntas gerais sobre agricultura e agronomia, mesmo quando o assunto não estiver registado no AgroVision. Use informação pública atual quando a pesquisa estiver disponível. "
            "Atue também como mentor agrícola educativo. Quando perguntarem como plantar alguma cultura, dê uma pequena mentoria numerada: escolha da área, preparação do solo, material de plantio, plantio, rega e manejo, prevenção de pragas e colheita. Responda sobre solo, rega, culturas e prevenção de doenças. Peça localização, cultura, solo e fase quando faltarem dados. Não invente doses de produtos, não confirme doenças sem inspeção e recomende validação do técnico ou consultor. "
            "Use os dados resumidos abaixo apenas para personalizar funções e informações privadas, respeitando sempre o perfil do utilizador.\n"
            f"{contexto_texto}\nConversa recente: {historico_texto}"
        ),
        pesquisa_web=True,
    )
    resposta = resposta_ia or _resposta_editavel(pergunta, request.user) or _resposta_programada(pergunta, contexto)
    resposta = _normalizar_resposta_chatbot(resposta)
    return JsonResponse({
        'resposta': resposta,
        'perfil': contexto['perfil'],
        'modo': 'ia' if resposta_ia else 'programado',
    })


@login_required
def dashboard_home(request):
    """
    Dashboard principal - mostra estatísticas e dados conforme o perfil.
    """
    user = request.user

    # ====================================================================
    # ADMINISTRADOR → visão geral total do sistema
    # ====================================================================
    if user.is_admin or user.is_superuser:
        context = {
            'total_utilizadores': Utilizador.objects.count(),
            'total_propriedades': Propriedade.objects.count(),
            'total_recomendacoes': Recomendacao.objects.count(),
            'total_visitas': VisitaTecnica.objects.count(),
            'alertas_ativos': Alerta.objects.filter(lido=False).count(),
            'ultimos_utilizadores': Utilizador.objects.order_by('-data_registro')[:5],
            'ultimas_propriedades': Propriedade.objects.order_by('-data_criacao')[:5],
        }
        return render(request, 'dashboard/admin.html', context)

    if user.is_visitante:
        return render(request, 'dashboard/generico.html', {
            'status_solicitacao': user.get_status_solicitacao_display(),
            'perfil_solicitado': user.get_perfil_solicitado_display() if user.perfil_solicitado else '',
        })

    # ====================================================================
    # CONSULTOR AGRÍCOLA → recomendações e visitas
    # ====================================================================
    elif user.is_consultor:
        propriedades_consultadas = Propriedade.objects.filter(
            consultor_responsavel=user
        )
        visitas_da_equipa = VisitaTecnica.objects.filter(
            propriedade__in=propriedades_consultadas
        ).order_by('-data')
        context = {
            'minhas_recomendacoes': Recomendacao.objects.filter(consultor=user).order_by('-data')[:5],
            'total_recomendacoes': Recomendacao.objects.filter(consultor=user).count(),
            'minhas_visitas': visitas_da_equipa[:5],
            'total_visitas': visitas_da_equipa.count(),
            'propriedades_consultadas': propriedades_consultadas,
            'pragas_ativas': PragaDoenca.objects.filter(resolvido=False, talhao__propriedade__consultor_responsavel=user).count(),
        }
        return render(request, 'dashboard/consultor.html', context)

    # ====================================================================
    # ANALISTA DE DADOS → gráficos e estatísticas
    # ====================================================================
    elif user.is_analista:
        propriedades = Propriedade.objects.filter(analista_responsavel=user)
        talhoes = Talhao.objects.filter(propriedade__in=propriedades)
        culturas = Cultura.objects.filter(talhao__in=talhoes).distinct()
        recomendacoes = Recomendacao.objects.filter(talhao__in=talhoes)
        context = {
            'total_propriedades': propriedades.count(),
            'total_talhoes': talhoes.count(),
            'total_culturas': culturas.count(),
            'recomendacoes_por_prioridade': {
                'baixa': recomendacoes.filter(prioridade='baixa').count(),
                'media': recomendacoes.filter(prioridade='media').count(),
                'alta': recomendacoes.filter(prioridade='alta').count(),
                'urgente': recomendacoes.filter(prioridade='urgente').count(),
            },
            'culturas': culturas,
            'registros_clima_recentes': RegistroClima.objects.filter(
                propriedade__in=propriedades
            ).order_by('-data')[:10],
        }
        return render(request, 'dashboard/analista.html', context)

    # ====================================================================
    # TÉCNICO DE CAMPO → inserção de dados
    # ====================================================================
    elif user.is_tecnico:
        propriedades = Propriedade.objects.filter(tecnico_responsavel=user)
        context = {
            'minhas_visitas': VisitaTecnica.objects.filter(responsavel=user).order_by('-data')[:5],
            'total_visitas': VisitaTecnica.objects.filter(responsavel=user).count(),
            'pragas_registadas': PragaDoenca.objects.filter(
                talhao__propriedade__in=propriedades
            ).count(),
            'propriedades': propriedades[:6],
        }
        return render(request, 'dashboard/tecnico.html', context)

    # ====================================================================
    # AGRICULTOR → consultas e alertas das suas propriedades
    # ====================================================================
    elif user.is_agricultor:
        minhas_propriedades = Propriedade.objects.filter(proprietario=user)
        context = {
            'minhas_propriedades': minhas_propriedades,
            'total_propriedades': minhas_propriedades.count(),
            'minhas_recomendacoes': Recomendacao.objects.filter(
                talhao__propriedade__in=minhas_propriedades,
                status__in=['emitida', 'aplicada'],
            ).order_by('-data')[:5],
            'alertas_ativos': Alerta.objects.filter(propriedade__in=minhas_propriedades, lido=False).count(),
            'alertas': Alerta.objects.filter(propriedade__in=minhas_propriedades).order_by('-data')[:5],
        }
        return render(request, 'dashboard/agricultor.html', context)

    # ====================================================================
    # CLIENTE → relatórios personalizados, recomendações e histórico
    # ====================================================================
    elif user.is_cliente:
        fornecedores = Propriedade.objects.filter(clientes_autorizados=user)
        producoes = RegistoProducao.objects.filter(
            talhao__propriedade__in=fornecedores
        ).select_related('talhao', 'talhao__propriedade', 'talhao__cultura').order_by('-data_colheita')
        context = {
            'fornecedores': fornecedores,
            'total_fornecedores': fornecedores.count(),
            'producoes_disponiveis': producoes[:8],
            'total_lotes': producoes.count(),
            'total_ofertas': Propriedade.objects.filter(exposta_para_clientes=True).count(),
            'total_favoritas': Propriedade.objects.filter(favoritada_por=user, exposta_para_clientes=True).count(),
            'total_pedidos': PedidoCompra.objects.filter(cliente=user).count(),
        }
        return render(request, 'dashboard/cliente.html', context)

    # Fallback - não deveria chegar aqui
    return render(request, 'dashboard/generico.html')
