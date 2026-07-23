# AgroVision — inteligência e fotografias

## Estado atual da inteligência

O AgroVision já tem uma base inteligente híbrida:

- consulta dados meteorológicos reais por API;
- cria alertas simples por regras;
- cruza dados de clima, pragas e propriedades para rascunhos de recomendação;
- possui chatbot com contexto limitado pelo perfil;
- pode usar Gemini quando a IA é ativada, mantendo um motor de regras como alternativa;
- mantém decisão humana: o consultor deve rever recomendações antes da emissão.

Isso torna o sistema assistivo e automatizado, mas ainda não um sistema agronómico preditivo validado. Para chegar a esse nível faltam dados históricos suficientes, indicadores de produção, validação agronómica das regras, modelos de previsão treinados e medição da qualidade das recomendações.

## Próximas camadas recomendadas

1. Histórico de produtividade por talhão e campanha.
2. Registos padronizados de solo, rega, adubação e aplicação de produtos.
3. Estádio fenológico e calendário de cada cultura.
4. Fotografias classificadas por cultura, problema, data e localização.
5. Diagnóstico visual de pragas/doenças com nível de confiança e confirmação humana.
6. Previsão de risco e produtividade comparada com o resultado real.
7. Auditoria da IA: origem dos dados, explicação da sugestão, aprovação do consultor e resultado.
8. Painel de qualidade com precisão, falsos alertas e recomendações aceites/rejeitadas.

## Onde colocar fotografias

O sistema já possui foto de perfil e múltiplas fotos nas visitas técnicas. Não é necessário duplicar isso.

Prioridade alta:

- **Propriedade:** uma foto de capa e uma galeria geral da fazenda.
- **Talhão:** galeria cronológica, com data, ponto GPS, cultura e estádio de crescimento.
- **Praga/Doença:** várias fotos do sintoma, planta inteira e área atingida; incluir estado antes/depois do tratamento.

Prioridade média:

- **Cultura:** imagem de referência para facilitar a identificação nas listas.
- **Recomendação:** fotografias usadas como evidência e fotografia do resultado após execução.
- **Produção/colheita:** fotos por campanha, lote e qualidade do produto.

A melhor primeira implementação é Talhão + Praga/Doença, porque cria histórico visual útil para acompanhamento e futura inteligência de imagem.
