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
        ├── app.py
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

Filtros: loja, categoria, produto e período. A camada Gold é lida diretamente do repositório. Todas as visualizações respeitam a seleção. Não há dados artificiais adicionados pelo dashboard nem simulação de reposição.

## Correspondência com o entregável

- **Dashboard funcional:** aplicativo Streamlit executável.
- **Visualizações integradas:** gráficos de série temporal, categoria, loja e dia da semana usam a mesma seleção.
- **Filtros:** loja, categoria, produto, período e agrupamento temporal.
- **Narrativa visual:** panorama → evolução → distribuição → comportamento semanal → conclusões.
- **Clareza e usabilidade:** unidades nomeadas, filtros em uma única barra lateral, informações sobre limitação dos dados.
- **Identidade própria:** azul-marinho, verde-petróleo, turquesa e dourado, distinta do painel da professora.

## Cuidados analíticos

- `demanda` é uma **estimativa disponibilizada pelo dataset**, não observação direta de todos os clientes interessados.
- `unidades_vendidas` são as vendas registradas; a diferença entre ambas não prova vendas perdidas.
- Dados são **sintéticos**.
- Totais diários, semanais e mensais são *somados*; produtos e lojas são *contados de modo distinto*; médias por dia da semana são calculadas sobre **totais diários** para evitar viés de contagem de registros.
- Os gráficos **não são previsões**. Isso é intencional nesta entrega.
