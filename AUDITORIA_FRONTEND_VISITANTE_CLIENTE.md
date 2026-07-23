# Auditoria de front-end — Visitante e Cliente

Data: 18/07/2026

## Resultado executivo

- 7 páginas públicas verificadas, sem links quebrados.
- 13 rotas do Cliente verificadas, sem erros HTTP 4xx/5xx.
- Login, cadastro, dashboard, Mercado Agrícola, fornecedores, relatórios, mensagens e perfil carregam corretamente.
- A navegação do Cliente contém um atalho de notificações para Alertas que redireciona ao dashboard porque esse perfil não possui acesso ao módulo.

## Visitante

### Pontos positivos
- Portal institucional simples, imagens com texto alternativo e chamadas para login/cadastro.
- Páginas Início, Serviços, Sobre, Contacto, Login e Registo respondem corretamente.
- Visitante autenticado consegue solicitar perfil, editar dados pessoais e contactar a administração.

### Melhorias recomendadas
1. Usar um único título principal H1 por página. Login e Registo precisam de H1 semântico.
2. Criar um indicador visual de progresso no pedido de perfil: Dados pessoais, Perfil pretendido, Documentos, Estado.
3. Mostrar requisitos da senha antes da submissão e validação em tempo real.
4. Acrescentar botão claro para mostrar/ocultar senha também no Registo e confirmação.
5. Melhorar mensagens de erro junto ao campo, mantendo um resumo no topo.
6. Incluir menu móvel explícito e testar larguras de 320, 375 e 768 píxeis.
7. Adicionar ligação “Saltar para o conteúdo” para navegação por teclado.

## Cliente comprador

### Pontos positivos
- Separação entre Mercado Agrícola, fornecedores autorizados, relatórios e mensagens.
- Mercado usa cartões com fotografia, localização, culturas e chamada comercial.
- Páginas privadas e relatórios respeitam as permissões do Cliente.

### Melhorias recomendadas
1. Corrigir o botão Notificações: para Cliente deve abrir Mensagens/Atendimento ou uma central de notificações permitida, não Alertas técnicos.
2. Adicionar filtros no Mercado por cultura, província, quantidade disponível, unidade e data da colheita.
3. Mostrar estado comercial do lote: disponível, reservado ou vendido.
4. Nos cartões, destacar produto, quantidade, qualidade e última atualização antes do nome técnico da propriedade.
5. Criar lista de favoritos e comparação de duas ou três ofertas.
6. Mostrar confirmação visual depois de “Tenho interesse em comprar”.
7. Adicionar paginação ou carregamento progressivo quando houver muitas propriedades.
8. Melhorar estados vazios com ação direta: procurar ofertas, contactar administração ou limpar filtros.

## Acessibilidade e consistência

- O CSS possui 1.927 linhas, 54 larguras fixas e 22 regras com important; recomenda-se consolidar componentes e usar variáveis/tamanhos fluidos.
- Existem seis blocos responsivos, mas é necessário verificar tabelas, cabeçalho e cartões em ecrãs estreitos.
- O painel possui ícones decorativos com alt vazio. Isso é aceitável se forem realmente decorativos, mas botões só com ícone precisam de aria-label.
- Padronizar alturas, espaçamentos e estados hover, focus, disabled e loading de todos os botões.
- Mover estilos inline dos templates para classes reutilizáveis.

## Prioridade sugerida

1. Corrigir Notificações do Cliente e semântica H1.
2. Acessibilidade de teclado, nomes acessíveis e erros de formulário.
3. Filtros e informações comerciais do Mercado.
4. Responsividade em telemóvel.
5. Refatoração do CSS e padronização visual.
