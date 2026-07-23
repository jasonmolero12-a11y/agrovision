from html import escape
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def _docx(destino, titulo, subtitulo, secoes):
    paragrafos = []

    def adicionar(texto, tipo='p'):
        tamanho = '38' if tipo == 'title' else '30' if tipo == 'h1' else '25' if tipo == 'h2' else '22'
        negrito = '<w:b/>' if tipo in {'title', 'h1', 'h2'} else ''
        centro = '<w:jc w:val="center"/>' if tipo in {'title', 'subtitle'} else ''
        paragrafos.append(
            f'<w:p><w:pPr>{centro}<w:spacing w:after="140"/></w:pPr><w:r><w:rPr>{negrito}'
            f'<w:sz w:val="{tamanho}"/></w:rPr><w:t xml:space="preserve">{escape(texto)}</w:t></w:r></w:p>'
        )

    adicionar(titulo, 'title')
    adicionar(subtitulo, 'subtitle')
    adicionar('AgroVision — Inteligência Agrícola | Atualizado em 23 de julho de 2026', 'subtitle')
    for numero, (nome, conteudos) in enumerate(secoes, 1):
        adicionar(f'{numero}. {nome}', 'h1')
        for item in conteudos:
            if isinstance(item, tuple):
                adicionar(item[0], 'h2')
                adicionar(item[1])
            else:
                adicionar(item)
    corpo = ''.join(paragrafos)
    documento = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f'<w:body>{corpo}<w:sectPr><w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134"/></w:sectPr></w:body></w:document>'
    )
    tipos = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '</Types>'
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        '</Relationships>'
    )
    with ZipFile(destino, 'w', ZIP_DEFLATED) as arquivo:
        arquivo.writestr('[Content_Types].xml', tipos)
        arquivo.writestr('_rels/.rels', rels)
        arquivo.writestr('word/document.xml', documento)
    return destino


def gerar_manuais(base_dir):
    pasta = Path(base_dir) / 'relatorios'
    pasta.mkdir(parents=True, exist_ok=True)

    utilizacao = [
        ('Antes de começar', [
            'Abra o Laragon e confirme que o MySQL está ligado. No terminal da pasta AgroVision, ative o ambiente virtual e execute python manage.py runserver. Depois abra http://127.0.0.1:8000/.',
            'Use uma janela anónima para trocar de utilizador durante os testes. Nunca compartilhe senhas ou chaves de API em relatórios e capturas públicas.',
        ]),
        ('Entrar e sair', [
            'Na página Entrar, informe email ou nome autorizado e senha. O ícone do olho mostra ou oculta a senha. Use Sair antes de trocar de conta.',
            'Se esquecer a senha, peça ao administrador para redefini-la no painel de utilizadores.',
        ]),
        ('Perfis e funções', [
            ('Visitante', 'Solicita um perfil e acompanha a aprovação. Não acessa dados técnicos.'),
            ('Administrador', 'Aprova perfis, atribui equipas, configura APIs e administra todos os registos.'),
            ('Agricultor', 'Cria propriedades e talhões, regista produção, executa consultoria e recebe recomendações.'),
            ('Consultor', 'Avalia análises, escreve a resposta técnica e emite recomendações.'),
            ('Técnico', 'Regista visitas, fotografias, pragas, sinais e ações de campo.'),
            ('Analista', 'Consulta indicadores, históricos e dados autorizados, sem alterar operações.'),
            ('Cliente', 'Consulta mercado e fotografias, favorita ofertas e envia pedidos de compra.'),
        ]),
        ('Criar propriedade e talhão', [
            'Entre como agricultor. Abra Propriedades, clique Nova propriedade e informe nome, localização no formato município, província, Angola, área e fotografia.',
            'Abra Talhões, clique Novo talhão, escolha a propriedade e escreva livremente a cultura. Informe área, tipo de solo, data de plantio e fotografia.',
        ]),
        ('Consultoria inteligente', [
            'Escolha o talhão e clique Analisar. Confira clima, risco, fatores, possíveis doenças e orientação. Clique Enviar análise ao consultor.',
            'O estado Aguardando resposta significa que o consultor recebeu um rascunho. Depois da emissão, o agricultor pode abrir a resposta e baixar o PDF.',
        ]),
        ('Chatbot e voz', [
            'Pergunte com linguagem normal: o que é tomate, como cultivar soja, como preparar o solo ou como reconhecer sinais de doença. Pequenos erros comuns de escrita são corrigidos.',
            'As respostas orientam, mas não substituem análise de solo, rótulo de produto, visita técnica ou diagnóstico profissional.',
        ]),
        ('Problemas comuns', [
            'Localização não encontrada: use município, província, Angola. Página não abre: confirme MySQL, ambiente virtual e runserver. Gemini indisponível: verifique chave, quota e internet; o modo interno continua funcionando.',
        ]),
    ]

    funcionamento = [
        ('Visão geral', [
            'O AgroVision reúne agricultores, consultores, técnicos, analistas, clientes e administradores numa aplicação web. Cada perfil enxerga somente as áreas necessárias ao seu trabalho.',
        ]),
        ('Ciclo da informação', [
            'O agricultor cria a fazenda e o talhão. A meteorologia fornece dados externos. O motor interno combina clima, solo, cultura, alertas e pragas. O consultor revê o resultado. O agricultor recebe a recomendação oficial.',
        ]),
        ('APIs', [
            ('Meteorologia', 'Open-Meteo ou OpenWeather devolve temperatura, humidade, vento, precipitação e previsão.'),
            ('Gemini', 'Responde perguntas e apoia explicações. A pesquisa Google pode fornecer informação pública atual. Se falhar, entram as respostas programadas.'),
            ('Fontes futuras', 'NASA POWER, SoilGrids, Sentinel-2 e FAOSTAT enriquecem clima histórico, solo, vegetação e estatísticas.'),
        ]),
        ('Regras e inteligência', [
            'A pontuação de risco é explicável: cada fator registado adiciona peso. O resultado automático é orientação preliminar. A recomendação oficial exige revisão humana.',
        ]),
        ('Segurança', [
            'Login, permissões por perfil, filtros por propriedade, proteção CSRF e chaves guardadas no servidor reduzem acesso indevido. Alterar o número de uma URL não deve revelar dados alheios.',
        ]),
        ('Teste completo', [
            'Use a ordem Visitante, Administrador, Agricultor, Consultor, Técnico, Analista, Cliente, Administrador e Agricultor. Assim se demonstra aprovação, produção, API, revisão e compra.',
        ]),
    ]

    programacao = [
        ('O que é um programa', [
            'Um programa é um conjunto de instruções. O navegador mostra telas; o servidor recebe pedidos; o banco guarda informação; as APIs trazem dados de outros serviços.',
        ]),
        ('Tecnologias do AgroVision', [
            ('Python', 'Linguagem usada para escrever regras e operações do servidor.'),
            ('Django', 'Organiza URLs, permissões, formulários, modelos, páginas e administração.'),
            ('MySQL', 'Banco de dados usado pelo Laragon para guardar utilizadores, propriedades e demais registos.'),
            ('HTML, CSS e JavaScript', 'HTML monta a página, CSS define aparência e JavaScript controla interações como chatbot e voz.'),
        ]),
        ('Mapa das pastas', [
            'contas cuida de login, utilizadores e mensagens. propriedades cuida de fazendas, talhões, culturas e produção. consultoria cuida de recomendações, visitas e pragas. meteorologia cuida da API e alertas. dashboard monta painéis e chatbot. config_sistema guarda configurações de APIs.',
            'templates contém páginas HTML. static contém CSS, JavaScript e imagens. media guarda fotografias enviadas. migrations registra mudanças do banco. tests e arquivos test_ verificam comportamento.',
        ]),
        ('Como uma página funciona', [
            'A URL identifica a rota. A view recebe o pedido, valida o utilizador, consulta models e devolve um template. O template vira HTML no navegador.',
        ]),
        ('Como uma API funciona', [
            'O servidor envia uma requisição HTTP. O provedor responde JSON. O código verifica erros, extrai campos, converte unidades e entrega um texto compreensível. Timeout, quota e fallback evitam que uma falha paralise tudo.',
        ]),
        ('Banco e migrações', [
            'Model é a definição de uma tabela. Migration é uma receita numerada que altera ou preenche o banco. Depois de mudar models, normalmente se executa makemigrations e migrate.',
        ]),
        ('Ambiente de desenvolvimento', [
            'Abra a pasta no VS Code, selecione .venv como interpretador e ative o ambiente. Instale requirements.txt. Nunca edite banco ou código sem cópia de segurança.',
        ]),
        ('Testes e diagnóstico', [
            'python manage.py check verifica configuração. python manage.py test executa testes. pip check verifica conflitos. Leia a última linha do erro e o primeiro arquivo do projeto indicado pelo traceback.',
        ]),
        ('Alteração segura', [
            'Entenda o requisito, localize o módulo, escreva teste, faça mudança pequena, execute testes e confira no navegador. Não coloque senha ou chave diretamente no código.',
        ]),
        ('Publicação', [
            'Para produção use DEBUG desligado, domínio permitido, HTTPS, servidor adequado, variáveis secretas, banco com backup e arquivos estáticos coletados. O runserver serve apenas ao desenvolvimento.',
        ]),
    ]

    arquivos = [
        _docx(pasta / 'Manual_de_Utilizacao_AgroVision.docx', 'Manual de Utilização do AgroVision', 'Guia passo a passo para utilizadores iniciantes', utilizacao),
        _docx(pasta / 'Manual_de_Funcionamento_AgroVision.docx', 'Como o AgroVision Funciona', 'Fluxos, perfis, APIs, inteligência e segurança', funcionamento),
        _docx(pasta / 'Manual_de_Programacao_AgroVision_para_Iniciantes.docx', 'Manual de Programação do AgroVision', 'Explicação técnica para quem está começando em informática', programacao),
    ]
    return arquivos


if __name__ == '__main__':
    gerar_manuais(Path(__file__).resolve().parents[1])
