# StockFlow

O StockFlow é uma ferramenta de previsão de demanda e reposição de estoque para pequenos negócios de varejo. A partir do histórico de vendas e de estoque, o objetivo é estimar a demanda futura dos produtos e indicar quando e quanto repor, ajudando a evitar falta ou excesso de mercadoria.

Projeto acadêmico desenvolvido em grupo na CESAR School.

## Integrantes

- Alan Matos
- Arthur Xavier
- Gabriela Monteiro
- João Lucas Veiga
- Julia Maria Teixeira
- Nathália de Mello

## Estrutura do repositório

```
stockflow/
├── data/
│   ├── bronze/   # dado original (CSV do Kaggle), nunca editado
│   ├── silver/   # dado tratado
│   └── gold/     # tabelas finais para modelos e dashboard
├── notebooks/    # notebooks de tratamento e análise
├── docs/         # documentação, incluindo o log de tratamento
└── experiments/
    ├── sprint4_previsao/   # comparação de métodos de previsão (Sprint 4)
    └── dashboard_inicial/  # dashboard em Streamlit, com a página de reposição (Sprint 6)
```

### Camadas de dados

Os dados seguem três camadas:

- **Bronze**: o dado original, exatamente como foi baixado. Não é alterado.
- **Silver**: o dado tratado (tipos corrigidos, duplicados e ausentes resolvidos, colunas padronizadas).
- **Gold**: tabelas finais, prontas para os modelos de previsão e para o dashboard.

Cada etapa lê da camada anterior e grava na seguinte. As decisões de tratamento ficam registradas em `docs/log_tratamento.md`.

## Documentação

- [docs/planejamento.md](docs/planejamento.md) — decisões, cronograma e etapas
- [docs/plano_preparacao_dados.md](docs/plano_preparacao_dados.md) — plano de preparação de dados
- [docs/requisitos_cc_sr2.md](docs/requisitos_cc_sr2.md) — requisitos da trilha de CC
- [docs/log_tratamento.md](docs/log_tratamento.md) — registro do tratamento dos dados
- [docs/pesquisa_metodos_previsao.md](docs/pesquisa_metodos_previsao.md) — métodos de previsão e sugestão de compra

## Stack

- **Dados e modelos**: Python e pandas no Google Colab
- **Dashboard**: Streamlit, lendo os Parquet da camada Gold
- **Publicação**: Streamlit Community Cloud
