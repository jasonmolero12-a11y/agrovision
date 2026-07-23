# Funcionamento do Projeto AgroVision

## 1. Objetivo

O AgroVision e uma plataforma web de consultoria agricola inteligente criada para apoiar a gestao de propriedades, talhoes, culturas, visitas tecnicas, recomendacoes agronomicas, meteorologia e alertas.

Na defesa, o projeto deve ser apresentado como um MVP funcional. A versao atual demonstra os principais fluxos do sistema e deixa recursos avancados, como analise preditiva completa, dados de mercado e integracoes laboratoriais, como evolucao futura.

## 2. Tecnologias usadas

- Back-end: Python com Django.
- Base de dados: MySQL.
- Front-end: HTML, CSS e JavaScript nos templates Django.
- PDF: ReportLab.
- Upload de imagens: Pillow.
- Meteorologia: OpenWeatherMap ou Open-Meteo.
- Configuracoes: python-decouple e ficheiro `.env`.

## 3. Perfis de utilizador

O sistema trabalha com controlo de acesso por perfil:

- Administrador: gere utilizadores, configuracoes, propriedades e dados gerais.
- Consultor Agricola: acompanha propriedades atribuídas, cria recomendacoes e visitas.
- Analista de Dados: consulta indicadores, registos e informacao consolidada.
- Tecnico de Campo: regista visitas tecnicas e ocorrencias de campo.
- Agricultor: consulta as suas propriedades, recomendacoes, visitas e alertas.
- Cliente: consumidor final dos servicos; recebe relatorios personalizados, acompanha recomendacoes e consulta historico de producao.
- Visitante: conta recem-criada, ainda sem acesso aos modulos internos.

O registo publico cria apenas visitantes. Depois do login, o visitante solicita o perfil pretendido: agricultor, cliente, consultor, analista ou tecnico. O administrador aprova ou recusa o pedido no painel admin.

## 4. Login

O login aceita email ou nome completo.

Administrador de defesa:

```text
Nome: Jason Molero
Email: jason@agrovision.local
Senha: AD251215
```

Exemplos de entrada:

- `jason@agrovision.local` + `AD251215`
- `Jason Molero` + `AD251215`

## 5. Modulos principais

### Portal publico

Mostra apresentacao da plataforma, servicos, informacoes sobre a empresa e contacto.

### Contas

Controla login, logout, registo publico, perfil, solicitacao de perfil e lista de utilizadores. O registo publico foi limitado para visitante, evitando que qualquer pessoa crie conta com permissao operacional.

Fluxo de aprovacao:

1. Utilizador cria conta publica.
2. Sistema atribui perfil `Visitante`.
3. Utilizador entra no dashboard pendente.
4. Utilizador preenche o formulario de solicitacao de perfil.
5. Utilizador responde a validacao profissional conforme o perfil solicitado.
6. Utilizador anexa o CV em PDF.
7. Administrador abre o painel admin.
8. Administrador verifica justificativa, validacao profissional e CV.
9. Administrador filtra pedidos pendentes e usa a acao `Aprovar perfil solicitado`.
10. O sistema muda o perfil do utilizador para o perfil solicitado.

Perguntas de validacao profissional:

- Consultor: qual e o numero de carteira profissional, certificacao ou principal area de consultoria agricola?
- Agricultor: qual e o nome da propriedade e a localizacao?
- Cliente: que relatorios pretende receber e que propriedade, producao ou servico quer acompanhar?
- Tecnico/Analista: qual e a formacao, experiencia tecnica ou area de analise?

### Atendimento e reclamações

- Todos os utilizadores não administradores podem enviar mensagens ou reclamações.
- O administrador recebe notificações, consulta a caixa de atendimento e responde dentro do sistema.
- As respostas ficam privadas e visíveis apenas ao autor e à administração.
- Solicitações de perfil informam prazo máximo de 48 horas e oferecem atendimento quando o prazo termina.

### Dashboard

Mostra um painel diferente conforme o perfil do utilizador:

- Admin ve totais gerais.
- Consultor ve recomendacoes, visitas e propriedades sob sua responsabilidade.
- Analista ve indicadores e estatisticas.
- Tecnico ve dados de campo.
- Agricultor ve propriedades, recomendacoes e alertas proprios.
- Cliente ve relatorios personalizados, recomendacoes, visitas e historico das propriedades associadas ao seu acesso.

### Propriedades

Permite gerir propriedades, talhoes e culturas. A visibilidade e filtrada por perfil para proteger dados de outros utilizadores.

### Consultoria

Permite criar recomendacoes agronomicas, visitas tecnicas, fotos de visitas e registos de pragas/doencas. Recomendacoes podem ser exportadas em PDF.

O modulo de consultoria tambem possui um motor de regras inicial:

- Calcula risco agronomico por talhao numa escala de 0 a 100.
- Usa historico climatico, alertas ativos e pragas/doencas nao resolvidas.
- Classifica o risco como Baixo, Medio, Alto ou Critico.
- Sugere prioridade da recomendacao automaticamente.
- Preenche uma recomendacao preliminar para o consultor rever antes de emitir.

### Meteorologia

Permite consultar previsao meteorologica externa. Quando existe propriedade associada ao utilizador, o sistema pode guardar um registo climatico e gerar alertas simples, como calor extremo e vento forte.

O historico de clima apresenta uma tabela e um grafico com temperatura, humidade e vento dos registos permitidos ao utilizador.

### Configuracao do sistema

Permite configurar a API meteorologica. Esta area e reservada ao administrador.

Para Open-Meteo, usar:

```text
Provedor: Open-Meteo
URL base: https://api.open-meteo.com/v1
API key: vazio
```

O sistema completa automaticamente a rota `/forecast`.

### Gestao de senhas

O administrador pode alterar a senha de qualquer utilizador pelo painel admin. No detalhe do utilizador existe o botao "Alterar senha deste utilizador".

### Chatbot interno

O dashboard possui um assistente flutuante com perguntas programadas. Ele responde conforme o perfil autenticado e usa apenas um resumo permitido pelo sistema.

Funcionalidades:

- Guia de voz opcional com seleção automática da voz feminina em português mais natural disponível no navegador.
- Ritmo, tom e pausas ajustados para reduzir o efeito robótico; fallback automático quando a voz preferida não estiver instalada.
- Respostas programadas sobre perfil, propriedades, recomendacoes, visitas, meteorologia e alertas.
- Botao para ligar/desligar a voz.
- Leitura das respostas por sintese de fala do navegador.
- Entrada por microfone quando o navegador suporta reconhecimento de voz.
- Endpoint interno `/dashboard/chatbot/` com contexto limitado por perfil.
- Preparado para futura API externa, mas sem enviar dados brutos ou dados de outros utilizadores.
- Explica o motor de regras, o risco agronomico e o grafico climatico.
- O administrador pode editar respostas programadas em Admin Django > Dashboard > Respostas do Chatbot.

Regra de seguranca do chatbot:

- Visitante ve apenas estado da solicitacao.
- Agricultor ve apenas resumo das suas propriedades.
- Cliente ve apenas relatorios, recomendacoes e historico ligados ao seu acesso.
- Consultor ve apenas propriedades atribuidas a ele.
- Tecnico ve apenas dados operacionais permitidos.
- Analista ve indicadores agregados.
- Admin ve resumo geral do sistema.

## 6. Regras de seguranca implementadas

- Registo publico cria apenas visitante.
- Visitante so recebe acesso depois de aprovacao do administrador.
- Chatbot responde com contexto limitado pelo perfil autenticado.
- Motor de regras usa apenas dados visiveis/autorizados ao perfil.
- Configuracao da API e restrita ao administrador.
- Agricultor ve apenas os seus dados.
- Consultor ve dados associados as propriedades sob sua responsabilidade.
- Detalhes e PDF de recomendacoes respeitam permissao por perfil.
- Criacao de visitas e pragas e limitada a perfis tecnicos.
- Alertas e registos climaticos sao filtrados por propriedade visivel.

## 7. O que defender como pronto

- Autenticacao por perfil.
- Gestao de propriedades, talhoes e culturas.
- Consultoria agricola com recomendacoes.
- Registo de visitas tecnicas.
- Gestao de pragas e doencas.
- Consulta meteorologica com historico.
- Alertas simples gerados por regras.
- Exportacao de recomendacao em PDF.
- Dashboard por perfil.
- Central interna de mensagens, reclamações e respostas administrativas.
- Página profissional de solicitação de perfil com prazo de 48 horas.
- Voz feminina natural selecionada automaticamente entre as vozes disponíveis.

## 8. O que defender como evolucao futura

- Analise preditiva completa.
- Dados de mercado agricola.
- Integracao com laboratorios.
- Notificacoes por email, SMS ou WhatsApp.
- Aplicacao movel.
- Dashboards com graficos mais avancados.
- Testes automatizados mais amplos.
- Deploy em servidor com HTTPS.
