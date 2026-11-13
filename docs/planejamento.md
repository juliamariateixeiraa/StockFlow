# Planejamento do Projeto — StockFlow

## Sobre o projeto

O StockFlow é uma ferramenta de previsão de demanda e apoio à reposição de estoque para pequenos negócios de varejo. A persona de referência é a Renata Souza, gestora de uma loja de produtos físicos que registra as vendas no sistema, mas decide a reposição pela experiência.

Projeto da disciplina Projetos 5 (CESAR School, 2026.2), trilha de Ciência da Computação — Análise e Visualização de Dados.

**Integrantes:** Alan Matos, Arthur Xavier, Gabriela Monteiro, João Lucas Veiga, Julia Maria Teixeira e Nathália de Mello.

## Documentos de referência

Todas as etapas seguem estes documentos:

- **[Plano de Preparação de Dados](plano_preparacao_dados.md)** (`docs/plano_preparacao_dados.md`) — fonte de dados, tratamento, transformações e pipeline.
- **[Requisitos CC — Projeto 5 (SR2)](requisitos_cc_sr2.md)** (`docs/requisitos_cc_sr2.md`) — entregáveis oficiais da trilha.
- **[Pesquisa de Métodos de Previsão](pesquisa_metodos_previsao.md)** (`docs/pesquisa_metodos_previsao.md`) — métodos de previsão, métricas e cálculo da sugestão de compra.
- **Restrições de CC** — limites técnicos definidos pelo grupo.
- **Seleção de Ideias** — funcionalidades priorizadas e fluxo da solução.
- **Matriz CSD** — pesquisa que sustenta as decisões.

## Decisões já tomadas

| Tema | Decisão |
|------|---------|
| Base de dados | Retail Store Inventory and Demand Forecasting (Kaggle), dado simulado, ~76 mil linhas, uma linha por data × loja × produto |
| Pipeline | Arquitetura medallion: Bronze (dado bruto) → Silver (dado tratado) → Gold (dado pronto para análise, modelos e dashboard) |
| Formatos | Bronze em CSV; Silver e Gold em Parquet. O dashboard lê os Parquet da Gold diretamente |
| Modelagem | Regressão linear com calendário para a previsão de demanda (menor erro na comparação da Sprint 4). O alerta de ruptura é uma regra do cálculo de reposição (estoque abaixo do ponto de pedido), sem classificador — decidido na Sprint 6 |
| Explicabilidade | O modelo precisa permitir mostrar quais variáveis pesam na sugestão de compra |
| Divisão treino/teste | Por data, nunca aleatória |
| Avaliação da classificação | Precisão, recall e F1, além da acurácia, porque a ruptura é minoria |
| Dashboard | Valores sempre na escala original (unidades e reais), com filtros por categoria, loja e período |
| Rótulo de ruptura | Venda ≥ estoque ou demanda > estoque (14,7% dos dias) — decidido na EDA (Sprint 3) |
| Alvo da regressão | `demanda`, com a venda sem os dias de ruptura como teste de robustez — decidido na EDA (Sprint 3) |
| Variáveis dos modelos | Estação no lugar do mês; sem dia da semana; promoção no lugar de desconto; preço do dia fora do modelo principal (artefato do dado sintético) — ver `docs/log_tratamento.md` |
| Reposição | Prazo de entrega padrão de 1 dia (o comportamento da base), revisão semanal e nível de serviço de 95%, os três ajustáveis no dashboard; estoque de segurança com ajuste para erros autocorrelacionados — decidido na Sprint 6, ver `docs/log_tratamento.md` |
| Fora do escopo do MVP | RFM (não há identificação de cliente), fontes externas reais (INMET, Sebrae), escala de equipe por turno, classificador de ruptura |
| Ferramentas | Google Colab + Python (pandas) para os dados; dashboard em Streamlit (`experiments/dashboard_inicial/`), publicado no Streamlit Community Cloud; GitHub para versionamento. Substitui o plano inicial com Next.js, Neon e Vercel — decidido na Sprint 6 |

## Fluxo da solução

Planilha → Gold → Previsão → Estoque → Dashboard/Alertas

Os notebooks fazem o tratamento e os modelos e geram as tabelas da camada Gold. O dashboard em Streamlit lê essas tabelas e mostra os resultados. Não há API própria para os modelos.

## Cronograma

| Sprint | Período | Etapa | Entrega no repositório | Requisito CC relacionado |
|--------|---------|-------|------------------------|--------------------------|
| 1 | 05/10 a 11/10 | Pesquisa e seleção do dataset | `data/bronze/`, `docs/planejamento.md` | 2. Plano de Preparação de Dados |
| 2 | 12/10 a 18/10 | Tratamento dos dados | `notebooks/01_tratamento.ipynb`, `data/silver/`, `docs/log_tratamento.md`, `docs/pesquisa_metodos_previsao.md` | 2. Plano de Preparação de Dados |
| 3 | 19/10 a 25/10 | Análise exploratória | `notebooks/02_eda.ipynb`, `data/gold/` | 3. Análise Exploratória de Dados |
| 4 | 26/10 a 01/11 | Modelo inicial de previsão | `experiments/sprint4_previsao/` | Bônus — Modelagem Preditiva |
| 5 | 02/11 a 08/11 | Avaliação do modelo e início do sistema | `experiments/sprint4_previsao/`, `experiments/dashboard_inicial/` | Bônus — Modelagem Preditiva; 5. Proposta de Integração e Publicação |
| 6 | 09/11 a 15/11 | Cálculo de reposição de estoque | `notebooks/03_reposicao.ipynb`, `data/gold/`, página de reposição do dashboard | Bônus — Modelagem Preditiva |
| 7 | 16/11 a 22/11 | Desenvolvimento da interface | `experiments/dashboard_inicial/` | 4. Dashboard Interativo — Versão Inicial |
| 8 | 23/11 a 29/11 | Integração do sistema | `experiments/dashboard_inicial/` | 6. Dashboard Consolidado |
| 9 | 30/11 a 06/12 | Testes e correções | `experiments/dashboard_inicial/`, `docs/` | 7. Versão Quase Final; 9. Documentação Final |
| 10 | 07/12 a 11/12 | Finalização e entrega (entrega final em 11/12/2026) | `docs/` | 8. Storytelling e Pitch; 9. Documentação Final |

O Plano de Análise de Dados (requisito 1) foi entregue no ciclo anterior ao início das sprints.

## Detalhamento por sprint

### Sprint 1 — Pesquisa e seleção do dataset (05/10 a 11/10)
- Pesquisa e seleção do dataset.
- Análise inicial das informações disponíveis.
- Elaboração do cronograma de desenvolvimento.

No repositório: CSV original do Kaggle salvo em `data/bronze/`, sem nenhuma alteração.

### Sprint 2 — Tratamento dos dados (12/10 a 18/10)
- Verificação de dados ausentes e inconsistências.
- Organização e preparação inicial da base de dados.
- Pesquisa de métodos de previsão de demanda.

No repositório (seções 3 e 4 do Plano de Preparação):
- conferência da base (período, classes, colunas Demand e Epidemic);
- verificação de dados faltantes: nulos, linhas ausentes, zeros que escondem faltante e mecanismo de falta;
- análise da venda censurada (dias em que o estoque limitou a venda);
- correção de tipos, duplicados, valores impossíveis e padronização de texto;
- marcação de valores extremos por loja × produto (IQR), sem remoção — o mesmo `produto_id` tem categoria diferente em cada loja, então o item é o par loja × produto;
- log com tudo que foi alterado e por quê;
- base tratada salva em `data/silver/vendas_tratadas.parquet`;
- pesquisa de métodos em `docs/pesquisa_metodos_previsao.md`.

### Sprint 3 — Análise exploratória (19/10 a 25/10)
- Análise dos históricos de vendas.
- Identificação de padrões de consumo.
- Criação de gráficos e indicadores.
- Análises estatísticas e probabilísticas.

No repositório (seção 5 do Plano de Preparação e requisito 3):
- variáveis derivadas (Gold — análise): dia da semana, mês, fim de semana, venda dos dias anteriores (1 e 7 dias) e média móvel de 7 dias, calculadas por loja × produto em ordem de data; diferença de preço para o concorrente, preço com desconto, cobertura de estoque e rótulo de ruptura;
- EDA com padrões, distribuições, correlações e agrupamentos, cada gráfico com interpretação em texto;
- indicadores: cobertura de estoque, taxa de ruptura, curva ABC e variabilidade da demanda por item;
- análises estatísticas e probabilísticas, cada uma com interpretação em texto:
  - estatística descritiva da venda e da demanda por loja × produto, categoria e região (média, mediana, desvio padrão, assimetria);
  - ajuste de distribuição para a demanda diária (normal, Poisson ou binomial negativa), base para o estoque de segurança;
  - probabilidade de ruptura, geral e condicional (por categoria, clima, desconto, promoção, epidemia e cobertura), com intervalo de confiança;
  - testes de hipótese: diferença de demanda entre fim de semana e dia útil, entre climas e entre estações (t/Mann-Whitney, ANOVA/Kruskal-Wallis) e associação entre ruptura e variáveis categóricas (qui-quadrado);
  - correlação de Pearson e Spearman com teste de significância;
- avaliação de outliers univariados e bivariados;
- escolha entre Seasonality e mês (manter só uma);
- decisões registradas em `docs/log_tratamento.md`.

### Sprint 4 — Modelo inicial de previsão (26/10 a 01/11)
- Escolha e implementação do modelo inicial de previsão de demanda.
- Realização das primeiras previsões.
- Testes e avaliação dos resultados utilizando dados históricos.

No repositório (Gold — modelos):
- one-hot das categóricas (categoria, clima, estação);
- padronização (z-score) calculada só no treino;
- divisão treino/teste por data;
- previsões de referência e regressão linear (pesquisa de métodos, seções 2 e 3).

### Sprint 5 — Avaliação do modelo e início do sistema (02/11 a 08/11)
- Avaliação dos resultados e ajustes no modelo de previsão.
- Definição da estrutura inicial do sistema.
- Início do desenvolvimento das funcionalidades básicas.

No repositório:
- regressão: dispersão, linha de tendência e análise de resíduos;
- estrutura da aplicação, organização das páginas e ferramenta de publicação (requisito 5): Streamlit.

A classificação do alerta de ruptura saiu do plano na Sprint 6: o bônus de modelagem pede regressão **ou** classificação, e o alerta virou uma regra do cálculo de reposição.

### Sprint 6 — Cálculo de reposição de estoque (09/11 a 15/11)
- Implementação do cálculo da quantidade recomendada para compra.
- Consideração do estoque disponível, demanda prevista e estoque de segurança.
- Testes iniciais do cálculo de reposição.

No repositório (`notebooks/03_reposicao.ipynb`):
- erro do modelo no teste (σ) por loja × produto, com checagem de normalidade e de autocorrelação;
- estoque de segurança, ponto de pedido, quantidade sugerida e alerta (crítico, pedir agora, ok), seguindo a seção 6 da pesquisa de métodos com revisão periódica;
- teste da regra (o estoque de segurança cumpre os 95%?) e backtest contra a reposição real da base;
- tabelas `data/gold/reposicao.parquet` e `data/gold/reposicao_previsao_diaria.parquet`;
- página "Reposição" no dashboard, com prazo, revisão e nível de serviço ajustáveis.

### Sprint 7 — Desenvolvimento da interface (16/11 a 22/11)
- Desenvolvimento das telas principais do sistema.
- Criação do painel de visualização de estoque.
- Implementação da exibição das previsões e recomendações de compra.

No repositório: primeira versão do dashboard, com ao menos um filtro e narrativa visual (requisito 4).

### Sprint 8 — Integração do sistema (23/11 a 29/11)
- Integração do modelo de previsão e do cálculo de reposição com a interface.
- Conexão entre as funcionalidades desenvolvidas.
- Testes básicos do funcionamento do sistema.

No repositório: dashboard consolidado, com dados e visualizações funcionando de ponta a ponta (requisito 6).

### Sprint 9 — Testes e correções (30/11 a 06/12)
- Realização de testes das funcionalidades principais.
- Identificação e correção de erros críticos.
- Organização da documentação desenvolvida.

No repositório: ajustes a partir de testes de uso e feedback (requisito 7).

### Sprint 10 — Finalização e entrega (07/12 a 11/12)
- Revisão final do sistema.
- Organização dos arquivos e da documentação.
- Preparação da apresentação do projeto.
- Entrega final em 11/12/2026.

No repositório: peça narrativa para a apresentação (requisito 8) e documentação final com histórico de decisões, capturas de tela e principais insights (requisito 9).

## Pendências

Nenhuma em aberto. Prazo de entrega (1 dia) e nível de serviço (95%) foram definidos na Sprint 6.
