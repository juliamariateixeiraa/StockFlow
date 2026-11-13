# StockFlow — Dashboard Interativo (Versão Inicial)

Dashboard **descritivo**, desenvolvido para atender ao entregável "Dashboard Interativo — Versão Inicial" da disciplina. **Não** calcula modelos de previsão: o laboratório de sete métodos continua separado em `experiments/sprint4_previsao/`.

## Instalação no repositório original

Copie toda esta pasta para `StockFlow/experiments/dashboard_inicial/`, mantendo o arquivo original em `StockFlow/data/gold/vendas_analise.parquet`.

Estrutura esperada:

```text
StockFlow/
├── data/gold/vendas_analise.parquet
└── experiments/
    ├── sprint4_previsao/
    └── dashboard_inicial/
        ├── app.py              # navegação entre as páginas
        ├── tema.py             # cores, fontes e estilo dos gráficos
        ├── paginas/
        │   ├── panorama.py     # visão histórica (dashboard inicial)
        │   └── reposicao.py    # o que comprar hoje (Sprint 6)
        ├── requirements.txt
        ├── README.md
        └── .streamlit/config.toml
```

## Executar (PowerShell, na pasta dashboard_inicial)

```powershell
py -3.12 -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Se você já possui um ambiente virtual com as dependências, pode reutilizá-lo, mas confirme o interpretador com `python -c "import sys; print(sys.executable)"`.

## O que o dashboard responde

1. **Panorama:** indicadores de demanda estimada, unidades vendidas, número de lojas e produtos.
2. **Evolução:** como demanda estimada e vendas variam no tempo, com agrupamento semanal ou mensal.
3. **Distribuição:** categorias e lojas com maior demanda no período filtrado.
4. **Padrões semanais:** demanda média observada por dia da semana.
5. **Síntese:** interpretação contextual e cuidados com dados sintéticos.

Filtros: loja, categoria, produto e período. A camada Gold é lida diretamente do repositório. Todas as visualizações respeitam a seleção. Não há dados artificiais adicionados pelo dashboard. A simulação de reposição fica na página própria (abaixo).

## Página de reposição (Sprint 6)

A página **Reposição** (`paginas/reposicao.py`) aparece no menu lateral, ao lado do Panorama. Ela lê as tabelas geradas por `notebooks/03_reposicao.ipynb`:

- `data/gold/reposicao.parquet`: erro do modelo, estoque atual e recomendação padrão por loja × produto;
- `data/gold/reposicao_previsao_diaria.parquet`: previsão diária dos próximos 30 dias.

A página mostra o que comprar em 30/01/2024: itens abaixo do ponto de pedido, lista de compras com quantidade e valor, a conta de cada item e o resultado do backtest. O prazo de entrega, o período de revisão e o nível de serviço são ajustáveis, e a conta é refeita na hora com as mesmas fórmulas do notebook. Se a base mudar, rode o notebook de novo antes de abrir o dashboard.

## Correspondência com o entregável

- **Dashboard funcional:** aplicativo Streamlit executável.
- **Visualizações integradas:** gráficos de série temporal, categoria, loja e dia da semana usam a mesma seleção.
- **Filtros:** loja, categoria, produto, período e agrupamento temporal.
- **Narrativa visual:** panorama → evolução → distribuição → comportamento semanal → conclusões.
- **Clareza e usabilidade:** unidades nomeadas, filtros em uma única barra lateral, informações sobre limitação dos dados.
- **Identidade própria:** tema claro com verde StockFlow (`#1f6b4f`) na interface. Nos gráficos, verde para demanda e azul para vendas, um par validado para daltonismo. Vermelho e âmbar ficam reservados para os alertas de estoque, sempre com rótulo. Tudo está centralizado em `tema.py`.

## Cuidados analíticos

- `demanda` é uma **estimativa disponibilizada pelo dataset**, não observação direta de todos os clientes interessados.
- `unidades_vendidas` são as vendas registradas; a diferença entre ambas não prova vendas perdidas.
- Dados são **sintéticos**.
- Totais diários, semanais e mensais são *somados*; produtos e lojas são *contados de modo distinto*; médias por dia da semana são calculadas sobre **totais diários** para evitar viés de contagem de registros.
- Os gráficos da página principal **não são previsões**. As previsões ficam na página de reposição.
