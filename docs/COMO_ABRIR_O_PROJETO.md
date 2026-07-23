# Como Abrir o Projeto AgroVision

## 1. Caminho do projeto

```text
C:\Users\jason\Documents\Codex\2026-07-17\mano-eu-acabei-de-troca-o\projetos\agrovision
```

## 2. Pre-requisitos

- Laragon ou MySQL ligado.
- Python do ambiente virtual do projeto.
- Base de dados MySQL chamada `agrovision`.

## 3. Abrir terminal na pasta do projeto

No PowerShell:

```powershell
cd C:\Users\jason\Documents\Codex\2026-07-17\mano-eu-acabei-de-troca-o\projetos\agrovision
```

## 4. Verificar configuracao da base de dados

O ficheiro `.env` deve ter estes dados para ambiente local:

```text
DB_NAME=agrovision
DB_USER=root
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=3306
```

Se o MySQL tiver senha, preencher `DB_PASSWORD`.

## 5. Aplicar migracoes

```powershell
.\.venv\Scripts\python.exe manage.py migrate
```

## 6. Criar ou atualizar o administrador da defesa

```powershell
.\.venv\Scripts\python.exe manage.py criar_admin_defesa
```

Credenciais:

```text
Nome: Jason Molero
Email: jason@agrovision.local
Senha: AD251215
```

O login aceita tanto o email como o nome `Jason Molero`.

## 7. Verificar se o projeto esta correto

```powershell
.\.venv\Scripts\python.exe manage.py check
```

Resultado esperado:

```text
System check identified no issues (0 silenced).
```

## 8. Rodar testes principais

```powershell
.\.venv\Scripts\python.exe manage.py test contas
```

Resultado esperado:

```text
OK
```

## 9. Iniciar servidor

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

Abrir no navegador:

```text
http://127.0.0.1:8000/
```

Login:

```text
http://127.0.0.1:8000/login/
```

Dashboard:

```text
http://127.0.0.1:8000/dashboard/
```

## 10. Ordem recomendada para demonstracao

1. Abrir o portal publico.
2. Entrar com o administrador `Jason Molero`.
3. Mostrar dashboard do administrador.
4. Mostrar lista de utilizadores.
5. Mostrar uma conta visitante e a tela de solicitacao de perfil.
6. Mostrar os campos de validacao profissional e anexo de CV em PDF.
7. Mostrar no admin como aprovar o perfil solicitado.
8. Mostrar no admin como alterar a senha de um utilizador.
9. Mostrar no admin a area Dashboard > Respostas do Chatbot para editar frases.
10. Mostrar propriedades, talhoes e culturas.
11. Abrir Nova Recomendacao e mostrar o risco agronomico automatico.
12. Mostrar recomendacao preliminar preenchida pelo motor de regras.
13. Mostrar recomendacoes e exportar PDF.
14. Mostrar visitas tecnicas.
15. Mostrar pragas/doencas.
16. Mostrar meteorologia.
17. Mostrar alertas e grafico de registos climaticos.
18. Abrir o chatbot flutuante e fazer perguntas como:
    - Como funciona o meu perfil?
    - Mostra o meu resumo.
    - Como usar meteorologia?
    - Como funciona o risco agronomico?
19. Demonstrar o botao de voz e a saudacao falada.

## 11. Frase curta para explicar na defesa

O AgroVision e um MVP em Django e MySQL para consultoria agricola. Ele centraliza propriedades, culturas, visitas, recomendacoes, meteorologia e alertas, com fluxo de aprovacao de perfil pelo administrador, controlo de acesso por perfil e exportacao de recomendacoes em PDF.

## 12. Chatbot na demonstracao

O chatbot aparece no canto inferior direito do dashboard. Ele usa respostas programadas e respeita o perfil do utilizador. Para a defesa, explique que a futura integracao com API externa sera feita apenas com contexto filtrado pelo sistema, mantendo a confidencialidade dos dados.

Para modificar respostas:

1. Entrar como administrador.
2. Abrir `/admin/`.
3. Abrir Dashboard > Respostas do Chatbot.
4. Editar titulo, palavras-chave e resposta.

## 13. API Open-Meteo

No painel Config. API, usar:

```text
Provedor: Open-Meteo
URL base: https://api.open-meteo.com/v1
API key: vazio
Cidade padrão: Luanda
```

O sistema monta automaticamente a chamada final:

```text
https://api.open-meteo.com/v1/forecast
```

com latitude, longitude e variaveis atuais de temperatura, humidade, vento, precipitacao e codigo meteorologico.

## 14. Motor de regras

Na tela de nova recomendacao, o sistema calcula uma pontuacao de risco com base em clima, alertas e pragas/doencas. A recomendacao gerada e preliminar: o consultor deve rever, ajustar e emitir. Esta abordagem permite defender o sistema como inteligente sem prometer uma IA completa nesta versao.


## 15. Atualização de 17/07/2026

- Central de mensagens e reclamações disponível em `/atendimento/`.
- Respostas administrativas e notificações internas ativadas.
- Solicitação de perfil redesenhada com prazo de resposta de 48 horas.
- Voz do assistente ajustada para priorizar narradora feminina em português.
- Migração `contas.0005` aplicada.
- Seis testes automatizados aprovados.
