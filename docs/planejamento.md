# Planejamento do Projeto — StockFlow

## Sobre o projeto

O StockFlow é uma ferramenta de previsão de demanda e apoio à reposição de estoque para pequenos negócios de varejo. A persona de referência é a Renata Souza, gestora de uma loja de produtos físicos que registra as vendas no sistema, mas decide a reposição pela experiência.

Projeto da disciplina Projetos 5 (CESAR School, 2026.2), trilha de Ciência da Computação — Análise e Visualização de Dados.

**Integrantes:** Alan Matos, Arthur Xavier, Gabriela Monteiro, João Lucas Veiga, Julia Maria Teixeira e Nathália de Mello.

## Documentos de referência

Todas as etapas seguem estes documentos:

- **[Plano de Preparação de Dados](plano_preparacao_dados.md)** (`docs/plano_preparacao_dados.md`) — fonte de dados, tratamento, transformações e pipeline.
- **[Requisitos CC — Projeto 5 (SR2)](requisitos_cc_sr2.md)** (`docs/requisitos_cc_sr2.md`) — entregáveis oficiais da trilha.
- **Restrições de CC** — limites técnicos definidos pelo grupo.
- **Seleção de Ideias** — funcionalidades priorizadas e fluxo da solução.
- **Matriz CSD** — pesquisa que sustenta as decisões.

## Decisões já tomadas

| Tema | Decisão |
|------|---------|
| Base de dados | Retail Store Inventory and Demand Forecasting (Kaggle), dado simulado, ~76 mil linhas, uma linha por data × loja × produto |
| Pipeline | Arquitetura medallion: Bronze (dado bruto) → Silver (dado tratado) → Gold (dado pronto para análise, modelos e dashboard) |
| Formatos | Bronze em CSV; Silver e Gold em Parquet; banco de dados entra com a aplicação (Sprints 7 e 8) |
| Modelagem | Apenas regressão simples (previsão de demanda e sugestão de compra) e classificação simples (alerta de ruptura) |
| Explicabilidade | O modelo precisa permitir mostrar quais variáveis pesam na sugestão de compra |
| Divisão treino/teste | Por data, nunca aleatória |
| Avaliação da classificação | Precisão, recall e F1, além da acurácia, porque a ruptura é minoria |
| Dashboard | Valores sempre na escala original (unidades e reais), com filtros por categoria, loja e período |
| Fora do escopo do MVP | RFM (não há identificação de cliente), fontes externas reais (INMET, Sebrae), escala de equipe por turno |
| Ferramentas | Google Colab + Python (pandas) para os dados; aplicação web com Next.js, TypeScript e Tailwind; banco Postgres (Neon); publicação na Vercel; GitHub para versionamento |

## Fluxo da solução

Planilha → Banco de dados → Previsão → Estoque → Dashboard/Alertas

Os notebooks fazem o tratamento e os modelos e geram as tabelas da camada Gold. A aplicação lê essas tabelas do banco e mostra os resultados. Não há API própria para os modelos.

## Cronograma

| Sprint | Período | Etapa | Entrega no repositório | Requisito CC relacionado |
|--------|---------|-------|------------------------|--------------------------|
| 1 | 05/10 a 11/10 | Dado bruto (Bronze) | `data/bronze/` | 2. Plano de Preparação de Dados |
| 2 | 12/10 a 18/10 | Tratamento dos dados (Silver) e pesquisa de métodos de previsão | `notebooks/01_tratamento.ipynb`, `data/silver/`, `docs/log_tratamento.md` | 2. Plano de Preparação de Dados |
| 3 | 19/10 a 25/10 | Análise exploratória e variáveis derivadas (Gold — análise) | `notebooks/02_eda.ipynb`, `data/gold/` | 3. Análise Exploratória de Dados |
| 4 | 26/10 a 01/11 | Modelos (Gold — modelos) | notebooks de modelagem | Bônus — Modelagem Preditiva |
| 5 | 02/11 a 08/11 | Modelos + estrutura inicial do sistema e funcionalidades básicas | notebooks de modelagem, `app/` | Bônus — Modelagem Preditiva |
| 6 | 09/11 a 15/11 | Modelos e sugestão de compra | notebooks de modelagem, `data/gold/` | Bônus — Modelagem Preditiva |
| 7 | 16/11 a 22/11 | Telas e painel de estoque | `app/`, `db/` | 4. Dashboard Interativo — Versão Inicial; 5. Proposta de Integração e Publicação |
| 8 | 23/11 a 29/11 | Integração com a previsão e o cálculo de reposição | `app/`, `db/` | 6. Dashboard Consolidado |
| — | 30/11 a 06/12 | Preparação para o SR2 | `docs/` | 7. Versão Quase Final; 8. Storytelling e Pitch |
| — | 07/12 | Status Report 2 | `docs/` | 9. Documentação Final |

O Plano de Análise de Dados (requisito 1) foi entregue no ciclo anterior ao início das sprints.

## Detalhamento por etapa

### Sprint 1 — Bronze
- CSV original do Kaggle salvo em `data/bronze/`, sem nenhuma alteração.

### Sprint 2 — Silver
Seções 3 e 4 do Plano de Preparação:
- conferência da base (período, classes, colunas Demand e Epidemic);
- verificação de dados faltantes: nulos, linhas ausentes, zeros que escondem faltante e mecanismo de falta;
- análise da venda censurada (dias em que o estoque limitou a venda);
- correção de tipos, duplicados, valores impossíveis e padronização de texto;
- marcação de valores extremos por loja × produto (IQR), sem remoção — o mesmo `produto_id` tem categoria diferente em cada loja, então o item é o par loja × produto;
- log com tudo que foi alterado e por quê;
- base tratada salva em `data/silver/vendas_tratadas.parquet`.

### Sprint 3 — Gold (análise) e EDA
Seção 5 do Plano de Preparação e requisito 3:
- variáveis derivadas: dia da semana, mês, fim de semana, venda dos dias anteriores (1 e 7 dias) e média móvel de 7 dias, calculadas por loja × produto em ordem de data; diferença de preço para o concorrente, preço com desconto, cobertura de estoque e rótulo de ruptura;
- EDA com padrões, distribuições, correlações e agrupamentos, cada gráfico com interpretação em texto;
- avaliação de outliers univariados e bivariados;
- escolha entre Seasonality e mês (manter só uma).

### Sprints 4 a 6 — Gold (modelos)
- one-hot das categóricas (Category, Weather Condition, Seasonality, Region);
- padronização (z-score) calculada só no treino;
- divisão treino/teste por data;
- regressão: dispersão, linha de tendência e análise de resíduos;
- classificação do alerta de ruptura: matriz de confusão, acurácia, precisão, recall, F1, curvas ROC e precision-recall;
- teste dos modelos com e sem o período de epidemia;
- cálculo da quantidade sugerida de compra.

### Sprints 7 e 8 — Aplicação e dashboard
- estrutura da aplicação, organização das páginas e ferramenta de publicação (requisito 5);
- carga das tabelas Gold no banco;
- dashboard com visualizações integradas, filtros e narrativa visual (requisitos 4 e 6);
- integração da previsão e da sugestão de reposição.

### Preparação para o SR2
- ajustes a partir de testes de uso e feedback (requisito 7);
- peça narrativa para a apresentação (requisito 8);
- documentação final com histórico de decisões, capturas de tela e principais insights (requisito 9).

## Pendências

- **Alvo da regressão:** a venda passa da demanda em 27,6% das linhas. O Plano de Preparação prevê, nesse caso, treinar sem os dias de ruptura ou mantê-los com marcador e comparar os resultados.
- **Regra da ruptura:** não há venda acima do estoque, o que indica que o estoque registrado é o do início do dia. Definir se a regra será "demanda > estoque" ou "venda ≥ estoque ou demanda > estoque".
