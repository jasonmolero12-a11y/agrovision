# Relatório de Atualização — AgroVision

**Data:** 17/07/2026

## Entregas concluídas

- Recuperação do ambiente Python 3.12 e ligação à base MySQL 8.4.3 do Laragon.
- Preservação integral dos utilizadores, permissões e dados existentes.
- Aplicação da migração `contas.0005_utilizador_data_solicitacao_mensagemsuporte`.
- Redesenho profissional da solicitação de perfil.
- Comunicação de prazo máximo de 48 horas.
- Central interna de mensagens e reclamações para utilizadores não administradores.
- Caixa de atendimento, notificações e respostas para administradores.
- Proteção de privacidade entre utilizadores.
- Voz aprimorada: seleção automática de narradora portuguesa, ritmo 0,89–0,90 e tom 1,08.

## Validação

- `manage.py check`: sem problemas.
- Migrações: todas aplicadas.
- Testes automatizados: 6 aprovados.
- Portal, login, dashboard, propriedades, consultoria, meteorologia, atendimento e administração: rotas operacionais.

## Observação sobre voz

A aplicação utiliza Web Speech API. A naturalidade final depende das vozes instaladas no Windows e disponibilizadas pelo Edge/Chrome. O sistema prioriza nomes femininos e vozes online/naturais em português, com fallback automático.


## Correção da administração de senhas — 18/07/2026

- Corrigido o botão **Alterar senha deste utilizador** no Django Admin: o endereço relativo apontava para uma rota inválida.
- O botão agora usa a rota oficial `admin:auth_user_password_change` gerada pelo Django.
- Adicionado um gestor de utilizadores baseado em email, permitindo criar utilizadores e superutilizadores sem o campo antigo `username`.
- Aplicada a migração `contas.0006_alter_utilizador_managers`.
- Verificações: `manage.py check` sem erros; rota real de senha com HTTP 200; 8 testes automáticos aprovados.
- As senhas e permissões dos administradores existentes foram preservadas.


## Interface, acessibilidade e permissões — 18/07/2026

- Substituídos os ícones principais da navegação pelos arquivos fornecidos em `static/img`.
- Criadas 21 versões WebP otimizadas em `static/img/icons`, preservando os originais e reduzindo cada ícone para cerca de 3–6 KB.
- Corrigido o campo de cidade da meteorologia, que estava comprimido pelo botão de pesquisa; agora possui rótulo, contraste, largura e exemplo visíveis.
- Adicionada opção acessível Mostrar/Ocultar palavra-passe no login.
- Adicionada barreira central contra acesso direto de visitantes a módulos operacionais.
- Confirmadas restrições de gestão de utilizadores e criação de propriedade para cargos não autorizados.
- Verificação final: `manage.py check` sem erros e 13 testes aprovados.
- Avaliação de inteligência e proposta de fotografias documentadas em `docs/PLANO_INTELIGENCIA_E_FOTOGRAFIAS.md`.


## Fotografias e previsão real — 18/07/2026

- Ícones do menu ajustados novamente para 24 × 24 px, equivalentes ao tamanho visual anterior.
- Fotografias implementadas para propriedade, talhão, cultura, praga/doença, recomendação e produção/colheita; as múltiplas fotos de visita técnica foram preservadas.
- Criado o modelo de registo de produção por talhão e campanha.
- Aplicadas as migrações propriedades.0002 e consultoria.0003.
- Inseridas imagens de demonstração provenientes de static/img e um registo claramente identificado como DEMONSTRAÇÃO FOTOGRÁFICA.
- Implementada previsão de produção explicável com média ponderada, tendência, clima recente, pragas ativas, número de amostras e grau de confiança.
- Resultado: página real HTTP 200, previsão visível, Django check sem erros e 15 testes aprovados.


## Normalização final do frontend — 18/07/2026

- Ícones de botões limitados rigidamente a 22 px e ícones do menu a 22 px.
- Botões, inputs, selects, textareas e uploads normalizados em todos os formulários.
- Adicionado versionamento do CSS para impedir cache de estilos antigos.
- Imagem de capa “Fazenda” substituída por fotografia agrícola.
- Django check sem erros e 15 testes aprovados.
- Fontes oficiais documentadas em docs/FONTES_DADOS_AGRICOLAS_OFICIAIS.md.
