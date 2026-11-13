from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from tema import DEMANDA, VENDAS, aplicar_estilo, cabecalho

aplicar_estilo()


# ---------------------------------------------------
# FUNÇÕES
# ---------------------------------------------------
@st.cache_data
def carregar_dados():
    raiz = Path(__file__).resolve().parents[3]
    arquivo = raiz / "data" / "gold" / "vendas_analise.parquet"

    if not arquivo.exists():
        st.error("Não encontrei a base Gold do projeto.")
        st.code(str(arquivo))
        st.info("Mantenha esta pasta em StockFlow/experiments/dashboard_inicial/ e o arquivo em StockFlow/data/gold/vendas_analise.parquet.")
        st.stop()

    df = pd.read_parquet(arquivo)

    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df = df.dropna(subset=["data"]).copy()

    # Garantia de tipos
    for col in ["demanda", "unidades_vendidas"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


def filtrar_dados(df, loja, categoria, produto, periodo):
    dff = df.copy()

    if loja != "Todas":
        dff = dff[dff["loja_id"] == loja]

    if categoria != "Todas":
        dff = dff[dff["categoria"] == categoria]

    if produto != "Todos":
        dff = dff[dff["produto_id"] == produto]

    data_ini, data_fim = periodo
    dff = dff[(dff["data"] >= pd.to_datetime(data_ini)) & (dff["data"] <= pd.to_datetime(data_fim))]

    return dff


def formatar_numero(valor):
    return f"{valor:,.0f}".replace(",", ".")


def criar_grafico_evolucao(dff, freq_label):
    if freq_label == "Semanal":
        grp = (
            dff.set_index("data")
               .resample("W")[["demanda", "unidades_vendidas"]]
               .sum()
               .reset_index()
        )
    else:
        grp = (
            dff.set_index("data")
               .resample("M")[["demanda", "unidades_vendidas"]]
               .sum()
               .reset_index()
        )

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=grp["data"],
        y=grp["demanda"],
        mode="lines",
        name="Demanda estimada",
        line=dict(color=DEMANDA)
    ))

    fig.add_trace(go.Scatter(
        x=grp["data"],
        y=grp["unidades_vendidas"],
        mode="lines",
        name="Unidades vendidas",
        line=dict(color=VENDAS)
    ))

    fig.update_layout(
        title="Evolução de demanda estimada e vendas",
        xaxis_title="Data",
        xaxis_tickformat="%m/%Y",
        yaxis_title="Unidades",
        legend_title=""
    )

    return fig


def criar_barras_comparativas(grupo, x, titulo, orientacao="v"):
    long_df = grupo.melt(
        id_vars=[x],
        value_vars=["demanda", "unidades_vendidas"],
        var_name="Indicador",
        value_name="Valor"
    )

    mapa_nomes = {
        "demanda": "Demanda estimada",
        "unidades_vendidas": "Unidades vendidas"
    }
    long_df["Indicador"] = long_df["Indicador"].map(mapa_nomes)

    fig = px.bar(
        long_df,
        x=x if orientacao == "v" else "Valor",
        y="Valor" if orientacao == "v" else x,
        color="Indicador",
        barmode="group",
        orientation=orientacao,
        color_discrete_map={
            "Demanda estimada": DEMANDA,
            "Unidades vendidas": VENDAS
        },
        title=titulo
    )

    fig.update_layout(
        legend_title=""
    )

    return fig


def grafico_dia_semana(dff):
    dias_ordem = [
        "Segunda", "Terça", "Quarta", "Quinta",
        "Sexta", "Sábado", "Domingo"
    ]

    temp = dff.copy()
    temp["dia_semana_num"] = temp["data"].dt.dayofweek
    mapa = {
        0: "Segunda", 1: "Terça", 2: "Quarta", 3: "Quinta",
        4: "Sexta", 5: "Sábado", 6: "Domingo"
    }
    temp["dia_semana"] = temp["dia_semana_num"].map(mapa)

    grp = (
        temp.groupby("dia_semana")[["demanda", "unidades_vendidas"]]
        .mean()
        .reindex(dias_ordem)
        .reset_index()
    )

    long_df = grp.melt(
        id_vars=["dia_semana"],
        value_vars=["demanda", "unidades_vendidas"],
        var_name="Indicador",
        value_name="Média"
    )

    mapa_nomes = {
        "demanda": "Demanda estimada",
        "unidades_vendidas": "Unidades vendidas"
    }
    long_df["Indicador"] = long_df["Indicador"].map(mapa_nomes)

    fig = px.bar(
        long_df,
        x="dia_semana",
        y="Média",
        color="Indicador",
        barmode="group",
        title="Média por dia da semana",
        color_discrete_map={
            "Demanda estimada": DEMANDA,
            "Unidades vendidas": VENDAS
        }
    )

    fig.update_layout(
        xaxis_title="Dia da semana",
        yaxis_title="Média de unidades",
        legend_title=""
    )

    return fig


# ---------------------------------------------------
# DADOS
# ---------------------------------------------------
df = carregar_dados()

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------
st.sidebar.title("Filtros")

lojas = ["Todas"] + sorted(df["loja_id"].dropna().astype(str).unique().tolist())
categorias = ["Todas"] + sorted(df["categoria"].dropna().astype(str).unique().tolist())
produtos = ["Todos"] + sorted(df["produto_id"].dropna().astype(str).unique().tolist())

loja_sel = st.sidebar.selectbox("Loja", lojas)
categoria_sel = st.sidebar.selectbox("Categoria", categorias)
produto_sel = st.sidebar.selectbox("Produto", produtos)

data_min = df["data"].min().date()
data_max = df["data"].max().date()

periodo_sel = st.sidebar.date_input(
    "Período",
    value=(data_min, data_max),
    min_value=data_min,
    max_value=data_max
)

if len(periodo_sel) != 2:
    st.warning("Selecione uma data inicial e uma data final.")
    st.stop()

dff = filtrar_dados(df, loja_sel, categoria_sel, produto_sel, periodo_sel)

if dff.empty:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")
    st.stop()

# ---------------------------------------------------
# TÍTULO
# ---------------------------------------------------
cabecalho("Panorama da demanda e das vendas")
st.markdown("""
<div class="info-box">
Este dashboard inicial apresenta uma visão histórica dos dados do StockFlow, comparando a
<strong>demanda estimada</strong> com as <strong>unidades efetivamente vendidas</strong>.
A proposta é identificar padrões, diferenças entre procura e vendas e recortes por loja, categoria e produto.
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# KPIs
# ---------------------------------------------------
demanda_total = dff["demanda"].sum()
vendas_total = dff["unidades_vendidas"].sum()
gap_total = demanda_total - vendas_total
lojas_qtd = dff["loja_id"].nunique()
produtos_qtd = dff["produto_id"].nunique()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Demanda estimada total", formatar_numero(demanda_total))
c2.metric("Unidades vendidas", formatar_numero(vendas_total))
c3.metric("Diferença demanda - vendas", formatar_numero(gap_total))
c4.metric("Produtos na seleção", formatar_numero(produtos_qtd))

# ---------------------------------------------------
# 01 - EVOLUÇÃO
# ---------------------------------------------------
st.markdown("## Como demanda e vendas evoluem no tempo?")

freq = st.radio("Agrupamento temporal", ["Semanal", "Mensal"], horizontal=True)
fig_evolucao = criar_grafico_evolucao(dff, freq)
st.plotly_chart(fig_evolucao, use_container_width=True)

# ---------------------------------------------------
# 02 - CONCENTRAÇÃO
# ---------------------------------------------------
st.markdown("## Onde a demanda está concentrada?")

col1, col2 = st.columns(2)

with col1:
    grp_cat = (
        dff.groupby("categoria", as_index=False)[["demanda", "unidades_vendidas"]]
        .sum()
        .sort_values("demanda", ascending=False)
    )
    fig_cat = criar_barras_comparativas(
        grp_cat,
        "categoria",
        "Demanda estimada x vendas por categoria",
        orientacao="h"
    )
    fig_cat.update_layout(xaxis_title="Unidades", yaxis_title="Categoria")
    st.plotly_chart(fig_cat, use_container_width=True)

with col2:
    grp_loja = (
        dff.groupby("loja_id", as_index=False)[["demanda", "unidades_vendidas"]]
        .sum()
        .sort_values("demanda", ascending=False)
    )
    fig_loja = criar_barras_comparativas(
        grp_loja,
        "loja_id",
        "Demanda estimada x vendas por loja",
        orientacao="v"
    )
    fig_loja.update_layout(xaxis_title="Loja", yaxis_title="Unidades")
    st.plotly_chart(fig_loja, use_container_width=True)

# ---------------------------------------------------
# 03 - PADRÕES SEMANAIS
# ---------------------------------------------------
st.markdown("## Existem padrões ao longo da semana?")
fig_semana = grafico_dia_semana(dff)
st.plotly_chart(fig_semana, use_container_width=True)

# ---------------------------------------------------
# 04 - TOP PRODUTOS
# ---------------------------------------------------
st.markdown("## Quais produtos mais concentram demanda e vendas?")

grp_prod = (
    dff.groupby("produto_id", as_index=False)[["demanda", "unidades_vendidas"]]
    .sum()
    .sort_values("demanda", ascending=False)
    .head(10)
)

fig_prod = criar_barras_comparativas(
    grp_prod,
    "produto_id",
    "Top 10 produtos — demanda estimada x vendas",
    orientacao="v"
)
fig_prod.update_layout(xaxis_title="Produto", yaxis_title="Unidades")
st.plotly_chart(fig_prod, use_container_width=True)

# ---------------------------------------------------
# INTERPRETAÇÃO FINAL
# ---------------------------------------------------
st.markdown("## Leitura do recorte selecionado")

if demanda_total > 0:
    taxa_atendimento = (vendas_total / demanda_total) * 100
else:
    taxa_atendimento = 0

maior_cat = grp_cat.iloc[0]["categoria"] if not grp_cat.empty else "-"
maior_loja = grp_loja.iloc[0]["loja_id"] if not grp_loja.empty else "-"
maior_prod = grp_prod.iloc[0]["produto_id"] if not grp_prod.empty else "-"

st.markdown(f"""
<div class="info-box">
<ul>
    <li><strong>Demanda estimada total:</strong> {formatar_numero(demanda_total)} unidades.</li>
    <li><strong>Unidades vendidas:</strong> {formatar_numero(vendas_total)} unidades.</li>
    <li><strong>Diferença entre demanda e vendas:</strong> {formatar_numero(gap_total)} unidades.</li>
    <li><strong>Taxa de atendimento aproximada:</strong> {taxa_atendimento:.1f}% da demanda estimada foi convertida em vendas.</li>
    <li><strong>Categoria com maior demanda estimada:</strong> {maior_cat}.</li>
    <li><strong>Loja com maior demanda estimada:</strong> {maior_loja}.</li>
    <li><strong>Produto com maior demanda estimada no recorte:</strong> {maior_prod}.</li>
</ul>
<p>
Este dashboard não comprova, por si só, a ocorrência de ruptura de estoque, mas ajuda a identificar
recortes em que a demanda estimada supera as vendas, o que pode indicar situações relevantes para investigação.
</p>
</div>
""", unsafe_allow_html=True)