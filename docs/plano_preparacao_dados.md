# Plano de Preparação de Dados

## 1. Fonte de dados

A base do projeto é o dataset **Retail Store Inventory and Demand Forecasting** (Kaggle, licença Apache 2.0), com cerca de 76 mil registros e 16 colunas, em CSV. É um dado **simulado**: não substitui o histórico real de uma loja, mas traz o mesmo tipo de informação que um PDV costuma registrar: venda, estoque e pedido por produto e por dia.

|Item|Detalhe|
|---|---|
|Tipo|Simulado (sintético), fonte aberta|
|Formato|CSV único, uma linha por data × loja × produto|
|Granularidade|Diária, por loja e por produto|
|Período|01/01/2022 a 30/01/2024 (760 dias)|
|Link|kaggle.com/dsv/11895299|

**Por que foi validada para o projeto:**

- Tem as variáveis que as duas entregas técnicas exigem: quantidade contínua para a regressão (venda/demanda) e estoque + venda para derivar o rótulo de ruptura da classificação.

- Já inclui dois fatores externos levantados na Matriz CSD, clima e sazonalidade, além de promoção e preço do concorrente, sem precisar integrar outra fonte agora.

- Permite filtros por loja, categoria, região e período, que o dashboard final precisa.

### Limitações assumidas:

- Por ser sintético, os padrões podem ser mais "limpos" que os de uma loja real. Os resultados servem como prova de conceito, não como acurácia esperada no uso real.

- Tem várias lojas e regiões, enquanto a persona tem um único negócio. Para simular o cenário da Renata, as análises de produto podem ser feitas recortando uma loja só.

- Não há identificação de cliente, então RFM fica fora do escopo, como já previsto nas restrições de CC.

- Fontes externas reais (INMET, calendário Sebrae) não entram no MVP: a base já traz equivalentes, e cada fonte nova aumentaria o pré-processamento sem ganho claro agora.

## 2. Variáveis e características

As 16 colunas se dividem em chaves, numéricas contínuas, numéricas discretas, categóricas e indicadores binários. O tipo de cada uma define o tratamento das seções 4 e 5.

|Variável|Tipo|Papel no projeto|Observação|
|---|---|---|---|
|Date|Data|Eixo de tempo, filtros, variáveis de calendário|Vem como texto; converter para data|
|Store ID|Categórica (chave)|Recorte por loja, agrupamento|Não entra no modelo como número|
|Product ID|Categórica (chave)|Recorte por produto, agrupamento|Alta cardinalidade; usar como chave, não como variável|
|Category|Categórica nominal|Filtro e variável explicativa|Poucas categorias (ex.: Groceries, Toys)|
|Region|Categórica nominal|Filtro do dashboard|Pouco útil para a persona de loja única|
|Inventory Level|Numérica discreta|Estoque disponível; base do rótulo de ruptura|Não pode ser negativa|
|Units Sold|Numérica discreta|Venda observada; alvo candidato da regressão|Limitada pelo estoque (ver seção 3)|
|Units Ordered|Numérica discreta|Pedido de reposição; comparação com a sugestão|Zero = não houve pedido, não é dado faltante|
|Demand|Numérica contínua|Demanda real; alvo preferido da regressão|Presente na base. A venda passa da demanda em 27,6% das linhas (ver log de tratamento)|
|Price|Numérica contínua|Variável explicativa|Positiva|
|Discount|Numérica discreta|Variável explicativa|Valores em degraus (0, 5, 10…)|
|Weather Condition|Categórica nominal|Variável explicativa (clima)|Quatro classes: Cloudy, Rainy, Snowy e Sunny (confirmado na Sprint 2)|
|Promotion|Binária (0/1)|Variável explicativa|Já pronta para o modelo|
|Competitor Pricing|Numérica contínua|Variável explicativa|Melhor usada como diferença para o próprio preço|
|Seasonality|Categórica nominal|Variável explicativa|Pode repetir a informação do mês|
|Epidemic|Binária (0/1)|Marca o período de pandemia|Avaliar se distorce o padrão normal de venda|

## 3. Dados faltantes e mecanismo de falta

Antes de limpar qualquer coisa, o grupo vai checar **se** falta dado e **por que** falta. A causa decide o tratamento: apagar ou preencher sem entender o motivo pode distorcer o modelo.

### Passo 1 — Verificar o que falta

- Contar valores nulos por coluna.

- Checar se toda combinação data × loja × produto existe. Uma linha ausente também é dado faltante, mesmo sem nenhum nulo no arquivo.

- Checar zeros e valores impossíveis (estoque negativo, preço zero), que podem estar "escondendo" um faltante.

### Passo 2 — Classificar o mecanismo

|Mecanismo|O que significa|Tratamento previsto|
|---|---|---|
|MCAR (completamente aleatório)|A falta não tem relação com nenhuma variável|Remover a linha, se for pouca coisa|
|MAR (depende de outra variável observada)|A falta acompanha outra coluna (ex.: uma loja ou categoria)|Preencher usando o grupo: mediana do mesmo produto e loja|
|MNAR (depende do próprio valor)|O valor falta justamente por causa do que ele seria|Não preencher às cegas; marcar com uma coluna indicadora|

Para saber se a falta é aleatória, o grupo vai comparar a taxa de nulos entre lojas, categorias e meses. Se ela se concentrar em algum grupo, não é MCAR.

### Passo 3 — O mecanismo que já sabemos que existe: venda censurada

Mesmo sem nulos, há uma falta "invisível" importante. Quando o estoque acaba, a loja só vende o que tinha, e a demanda que sobrou não aparece. Ou seja, nos dias de ruptura, `Units Sold` mostra menos do que o cliente queria comprar. Na prática, isso funciona como um dado faltante não aleatório (MNAR): a informação some justamente nos dias de demanda alta.

Como o grupo vai lidar com isso:

- Usar `Demand` como alvo da regressão, e não `Units Sold`, se a coluna estiver disponível e consistente.

- Criar a coluna `ruptura` (1 quando a venda bate no estoque, ou a demanda passa do estoque). Ela serve como rótulo da classificação e como marcador de dia com venda censurada.

- Se `Demand` não for confiável, treinar a regressão sem os dias de ruptura, ou manter esses dias com o marcador, e comparar os dois resultados.

Como a base é sintética, a expectativa é encontrar poucos ou nenhum nulo. Mesmo assim, os três passos ficam registrados, porque a importação de planilhas prevista na seleção de ideias vai receber dados reais, que podem chegar incompletos.

## 4. Estratégias de limpeza

A limpeza corrige erros sem apagar sinal real. Por isso, valores extremos são marcados e investigados antes de qualquer remoção.

|Problema|Como identificar|Decisão|Justificativa|
|---|---|---|---|
|Tipos errados|Conferir o tipo de cada coluna ao carregar|Data como data; IDs e categóricas como texto; quantidades como inteiro|Evita cálculo errado (ex.: ID tratado como número)|
|Linhas duplicadas|Mesma data, loja e produto repetidos|Manter só uma|A chave data × loja × produto deve ser única|
|Texto inconsistente|Valores distintos de cada categórica|Padronizar escrita (espaços, maiúsculas)|Evita que "Rainy" e "rainy " virem classes diferentes|
|Valores impossíveis|Estoque, venda ou preço negativos; desconto acima de 100|Corrigir se o erro for óbvio; senão, remover a linha e registrar|São erros, não sinal|
|Venda acima do estoque|`Units Sold` > `Inventory Level`|Investigar antes de agir; pode indicar reposição no mesmo dia|Define como o rótulo de ruptura será calculado|
|Valores extremos|Regra do IQR por loja × produto, não na base toda (o mesmo produto_id tem categoria diferente em cada loja)|Marcar, não remover|Picos em promoção ou feriado são justamente o que o modelo precisa aprender|
|Dados faltantes|Seção 3|Conforme o mecanismo identificado|Tratamento depende da causa|
|Período de epidemia|Coluna `Epidemic`|Manter, com a coluna como variável; testar o modelo com e sem esse período|Pode distorcer o padrão normal de venda|

Toda linha removida ou corrigida fica registrada em um log simples (quantas, por quê), para mostrar no relatório o quanto a base mudou.

## 5. Normalização e transformações

Cada transformação parte do tipo da variável e do uso que ela terá. O objetivo é deixar os dados prontos para regressão simples, classificação simples e dashboard, mantendo o modelo explicável.

### Variáveis novas (derivadas)

|Nova variável|Como é criada|Para que serve|
|---|---|---|
|Dia da semana, mês, fim de semana|Extraídos de `Date`|Captar padrão semanal e mensal sem modelo de série temporal|
|Venda dos dias anteriores (1 e 7 dias) e média móvel de 7 dias|Calculadas por loja e produto, em ordem de data|Dar à regressão linear a venda recente, sem usar modelo de série temporal (fora das restrições de CC)|
|Diferença de preço para o concorrente|`Price` − `Competitor Pricing`|Mostra se o produto está mais caro ou mais barato que o concorrente, o que é mais fácil de explicar. Se as duas colunas forem muito correlacionadas na EDA, também evita repetir informação no modelo|
|Preço com desconto|`Price` × (1 − `Discount`/100)|Preço que o cliente de fato pagou|
|Cobertura de estoque|`Inventory Level` ÷ média móvel de venda|Quantos dias o estoque dura; base do alerta|
|`ruptura` (0/1)|Venda ≥ estoque, ou demanda > estoque. A regra final depende de confirmar se o estoque é do início ou do fim do dia|Rótulo da classificação|

### Codificação das categóricas

- `Category`, `Weather Condition`, `Seasonality` e `Region`: one-hot. São nominais (não têm ordem) e têm poucas classes, então não geram muitas colunas.

- `Store ID` e `Product ID`: não entram como variável do modelo. Ficam como chave para agrupar, filtrar e montar uma série por produto.

- `Seasonality` e mês dizem quase a mesma coisa. Na EDA, o grupo mantém só uma das duas, para não repetir informação.

### Escala das numéricas

- Padronização (z-score) de preço, desconto, estoque e das defasagens. Na regressão linear, isso deixa os coeficientes comparáveis entre si, o que sustenta a sugestão de compra com explicação.

- A média e o desvio usados na padronização são calculados só nos dados de treino e aplicados no teste, para não vazar informação do futuro.

- Se a venda tiver distribuição muito assimétrica (poucos dias com venda muito alta), aplicar log(1 + x) no alvo e voltar à escala original na hora de mostrar a previsão.

- O dashboard usa sempre os valores originais, sem padronização, para a Renata ler unidades e reais.

### Divisão treino/teste

A divisão é feita por data (ex.: últimos meses como teste), nunca de forma aleatória. Com dado ao longo do tempo, uma divisão aleatória deixaria o modelo "ver o futuro" e daria uma acurácia falsamente alta.

### Desbalanceamento da ruptura

Dias de ruptura tendem a ser minoria: a taxa média mundial levantada na Matriz CSD é de 8,3%. Por isso, a classificação será avaliada por precisão, recall e F1, e não só por acurácia. Um modelo que nunca dispara alerta teria acurácia alta e não ajudaria a Renata em nada.

## 6. Pipeline de dados

O pipeline segue a arquitetura medallion, em três camadas, e acompanha o fluxo definido na seleção de ideias: planilha → banco de dados → previsão → estoque → dashboard e alertas. O arquivo bruto nunca é alterado, então qualquer etapa pode ser refeita do zero.

1. **Entrada — Bronze (dado bruto):** o CSV do Kaggle é guardado exatamente como veio. No produto, é aqui que entra a planilha exportada do PDV da Renata.

2. **Tratamento — Silver (dado tratado):** tipos corrigidos, duplicados e erros removidos, faltantes tratados conforme o mecanismo (seção 3), categorias padronizadas e extremos marcados. Tudo que muda fica no log. O resultado é salvo em Parquet. A carga no banco de dados acontece junto com a integração da aplicação (Sprints 7 e 8), quando as tabelas da camada Gold também estiverem prontas.

3. **Preparação analítica — Gold:** variáveis derivadas, rótulo de ruptura, codificação, padronização e divisão treino/teste por data (seção 5).

4. **Uso:** a camada Gold alimenta a regressão (previsão de demanda e sugestão de compra), a classificação (alerta de ruptura) e o dashboard (valores na escala original, com filtros).

|Camada|Conteúdo|Formato|Sprint|
|---|---|---|---|
|Bronze|CSV original do Kaggle|CSV|Sprint 1 (05/10 a 11/10)|
|Silver|Base limpa, uma linha por data × loja × produto|Parquet|Sprint 2 (12/10 a 18/10)|
|Gold — análise|Tabela com variáveis derivadas para a EDA|Parquet|Sprint 3 (19/10 a 25/10)|
|Gold — modelos|Tabelas de regressão e de classificação, já divididas em treino e teste|Parquet|Sprints 4 a 6 (26/10 a 15/11)|
|Gold — dashboard|Tabela agregada com venda, previsão, estoque e alertas|Banco de dados|Sprints 7 e 8 (16/11 a 29/11)|

Cada camada é gerada por um notebook próprio. A Bronze fica em CSV por ser o formato original; Silver e Gold usam Parquet porque o formato guarda os tipos (data, categoria) e evita refazer a conversão em cada notebook. Quando o sistema receber uma planilha real, ela entra na Bronze e passa pelas mesmas etapas, sem passo manual no meio.

## 7. Visualizações previstas

Lista inicial, a ser refinada depois da EDA.

|Pergunta|Visualização|
|---|---|
|Como a venda evolui no tempo?|Linha por período, com filtro de produto e categoria|
|Como a venda se distribui e onde estão os extremos?|Histograma e boxplot por categoria|
|Que fatores mais se relacionam com a venda?|Mapa de calor de correlação|
|Promoção, clima e fim de semana mudam a venda?|Barras comparando médias por grupo|
|Quais produtos estão em risco de faltar?|Barras horizontais de cobertura de estoque, com cor de alerta|
|O modelo de regressão está bom?|Dispersão real × previsto, linha de tendência e resíduos|
|O alerta de ruptura acerta?|Matriz de confusão, curva ROC e precision-recall|
|A previsão acompanha a venda real?|Linha de real × previsto no dashboard|
