"""StockFlow | Dashboard exploratório inicial (sem modelagem preditiva)."""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="StockFlow | Panorama da demanda", page_icon="📦", layout="wide", initial_sidebar_state="expanded")

# Identidade visual independente do dashboard de aula.
MARINHO = "#10283F"
PETROLEO = "#137F78"
TURQUESA = "#46C9B7"
DOURADO = "#D9A441"
CLARO = "#E9F3F4"
CINZA = "#9FB7C1"
PALETA = [PETROLEO, DOURADO, "#7AA4DA", "#A994E8", "#E38B72", "#6DA9A3", "#B68DB9"]

st.markdown("""
<style>
:root { color-scheme: dark; }
.stApp { background: #0B1927; color: #EAF3F5; }
.block-container { max-width: 1450px; padding-top: 2rem; padding-bottom: 3rem; }
[data-testid="stSidebar"] { background: #10283F; border-right: 1px solid #23485A; }
[data-testid="stMetric"] { background: #122D40; border: 1px solid #285466; padding: 15px 18px; border-radius: 14px; }
[data-testid="stMetricLabel"] { color: #A9C5CE; }
[data-testid="stMetricValue"] { color: #F0F7F8; }
h1, h2, h3 { letter-spacing: -0.025em; }
section[data-testid="stSidebar"] hr { border-color: #31556A; }
.sf-eyebrow { color: #54D1BE; font-weight: 700; letter-spacing: 0.13em; font-size: 0.77rem; }
.sf-subtitle { color: #B3CAD2; font-size: 1rem; margin-top: -0.55rem; margin-bottom: 1.3rem; }
.sf-note { background: #142E40; border-left: 3px solid #D9A441; padding: 12px 16px; border-radius: 0 10px 10px 0; color: #D7E8EC; }
</style>
""", unsafe_allow_html=True)

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent.parent   # StockFlow/experiments/dashboard_inicial/app.py
DATA_PATH = ROOT / "data" / "gold" / "vendas_analise.parquet"
REQUIRED = {"data", "loja_id", "produto_id", "categoria", "demanda", "unidades_vendidas"}

@st.cache_data(show_spinner="Carregando a base Gold do StockFlow...")
def carregar(path: str, modified: int) -> pd.DataFrame:
    d = pd.read_parquet(path)
    faltantes = REQUIRED - set(d.columns)
    if faltantes:
        raise ValueError(f"Colunas obrigatórias ausentes: {', '.join(sorted(faltantes))}")
    d = d.copy()
    d["data"] = pd.to_datetime(d["data"], errors="coerce").dt.normalize()
    d = d.dropna(subset=["data"])
    for c in ("demanda", "unidades_vendidas"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    for c in ("loja_id", "produto_id", "categoria"):
        d[c] = d[c].fillna("Não informado").astype(str)
    return d


def fig_layout(fig, altura=380):
    fig.update_layout(
        height=altura, paper_bgcolor="#0B1927", plot_bgcolor="#0B1927",
        font=dict(color="#DAEBF0"), margin=dict(t=35, l=10, r=10, b=15),
        legend=dict(orientation="h", y=1.14),
        hovermode="x unified"
    )
    fig.update_xaxes(showgrid=False, linecolor="#345065")
    fig.update_yaxes(gridcolor="#243B4B", zerolinecolor="#345065")
    return fig


if not DATA_PATH.is_file():
    st.error("Não encontrei a base Gold do projeto.")
    st.code(str(DATA_PATH))
    st.info("Coloque esta pasta em StockFlow/experiments/dashboard_inicial/ e mantenha o arquivo em StockFlow/data/gold/vendas_analise.parquet.")
    st.stop()

try:
    df = carregar(str(DATA_PATH), DATA_PATH.stat().st_mtime_ns)
except Exception as e:
    st.error(f"Não foi possível ler a base Gold: {e}")
    st.stop()

if df.empty:
    st.warning("A base Gold não contém registros com datas válidas.")
    st.stop()

with st.sidebar:
    st.markdown("### 📦 StockFlow")
    st.caption("Dashboard inicial · Exploração de dados")
    st.divider()
    st.markdown("**Filtros da análise**")
    lojas = sorted(df["loja_id"].unique().tolist())
    loja = st.selectbox("Loja", ["Todas as lojas"] + lojas)
    base_f = df if loja == "Todas as lojas" else df[df["loja_id"] == loja]
    categorias = sorted(base_f["categoria"].unique().tolist())
    categoria = st.selectbox("Categoria", ["Todas as categorias"] + categorias)
    if categoria != "Todas as categorias":
        base_f = base_f[base_f["categoria"] == categoria]
    produtos = sorted(base_f["produto_id"].unique().tolist())
    produto = st.selectbox("Produto", ["Todos os produtos"] + produtos)
    if produto != "Todos os produtos":
        base_f = base_f[base_f["produto_id"] == produto]
    minimo = df["data"].min().date()
    maximo = df["data"].max().date()
    periodo = st.date_input("Período", value=(minimo, maximo), min_value=minimo, max_value=maximo, format="DD/MM/YYYY")
    if isinstance(periodo, (tuple, list)) and len(periodo) == 2:
        inicio, fim = periodo
        base_f = base_f[base_f["data"].between(pd.Timestamp(inicio), pd.Timestamp(fim))]
    elif isinstance(periodo, (tuple, list)) and len(periodo) == 1:
        st.info("Escolha a data final do intervalo.")
    st.divider()
    st.caption("Fonte: camada Gold do StockFlow · Dataset acadêmico sintético")
    st.caption("Os gráficos são descritivos: não realizam previsões.")

st.markdown('<div class="sf-eyebrow">STOCKFLOW  /  INTELIGÊNCIA DE DADOS</div>', unsafe_allow_html=True)
st.title("Panorama da demanda e das vendas")
st.markdown('<div class="sf-subtitle">O que os dados históricos mostram sobre o comportamento dos produtos e das lojas?</div>', unsafe_allow_html=True)

if base_f.empty:
    st.warning("Não existem registros para os filtros selecionados. Ajuste loja, categoria, produto ou período.")
    st.stop()

# Indicadores respeitam filtros. A variável demanda é estimativa fornecida pela base.
demanda = float(base_f["demanda"].sum())
vendas = float(base_f["unidades_vendidas"].sum())
lojas_ativas = int(base_f["loja_id"].nunique())
produtos_ativos = int(base_f["produto_id"].nunique())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Demanda estimada", f"{demanda:,.0f} un.")
c2.metric("Unidades vendidas", f"{vendas:,.0f} un.")
c3.metric("Lojas na seleção", str(lojas_ativas))
c4.metric("Produtos na seleção", str(produtos_ativos))
st.caption("Valores acumulados no período selecionado. Demanda estimada e unidades vendidas são indicadores distintos.")

# 1. Evolução temporal: leitura progressiva do comportamento ao longo do tempo.
st.subheader("01 · Como a demanda evoluiu?")
granularidade = st.segmented_control("Agrupamento temporal", options=["Mensal", "Semanal"], default="Mensal")
frequencia = "MS" if granularidade == "Mensal" else "W-MON"
serie = (base_f.set_index("data")[["demanda", "unidades_vendidas"]]
         .resample(frequencia).sum(min_count=1).reset_index())
fig = go.Figure()
fig.add_trace(go.Scatter(x=serie["data"], y=serie["demanda"], name="Demanda estimada", mode="lines+markers", line=dict(color=TURQUESA, width=3), marker=dict(size=5)))
fig.add_trace(go.Scatter(x=serie["data"], y=serie["unidades_vendidas"], name="Unidades vendidas", mode="lines+markers", line=dict(color=DOURADO, width=2), marker=dict(size=4)))
fig.update_yaxes(title="Unidades acumuladas no período")
st.plotly_chart(fig_layout(fig, 370), use_container_width=True)
if len(serie) > 1:
    primeiro, ultimo = serie["demanda"].iloc[0], serie["demanda"].iloc[-1]
    st.caption("Leitura: as linhas mostram os totais por intervalo, não previsões. Compare os períodos e observe possíveis oscilações.")
else:
    st.caption("Há apenas um intervalo visível. Amplie o período para analisar a evolução temporal.")

# 2. Distribuição por categoria e por loja. Usa demanda para manter narrativa coerente.
st.subheader("02 · Onde a demanda está concentrada?")
left, right = st.columns(2, gap="large")
with left:
    por_categoria = (base_f.groupby("categoria", as_index=False)["demanda"].sum()
                     .sort_values("demanda", ascending=False))
    fig_cat = px.bar(por_categoria, x="demanda", y="categoria", orientation="h", color_discrete_sequence=[PETROLEO], labels={"demanda":"Demanda total (un.)", "categoria":"Categoria"})
    fig_cat.update_yaxes(categoryorder="total ascending")
    st.markdown("**Demanda por categoria**")
    st.plotly_chart(fig_layout(fig_cat, 340), use_container_width=True)
with right:
    por_loja = (base_f.groupby("loja_id", as_index=False)["demanda"].sum()
                .sort_values("demanda", ascending=False))
    fig_loja = px.bar(por_loja, x="loja_id", y="demanda", color_discrete_sequence=[DOURADO], labels={"demanda":"Demanda total (un.)", "loja_id":"Loja"})
    st.markdown("**Demanda por loja**")
    st.plotly_chart(fig_layout(fig_loja, 340), use_container_width=True)
if len(por_categoria):
    topo_cat = por_categoria.iloc[0]["categoria"]
    st.markdown(f'<div class="sf-note"><b>Leitura dos dados:</b> na seleção atual, <b>{topo_cat}</b> é a categoria com maior demanda acumulada. Isso descreve o histórico observado, não garante o mesmo comportamento no futuro.</div>', unsafe_allow_html=True)

# 3. Padrões de semana — médias diárias, não volume agregado por número de ocorrências.
st.subheader("03 · O comportamento muda ao longo da semana?")
diario = base_f.groupby("data", as_index=False).agg(demanda=("demanda", "sum"), vendidas=("unidades_vendidas", "sum"))
diario["dia_semana"] = diario["data"].dt.dayofweek
nomes = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
semana = diario.groupby("dia_semana", as_index=False).agg(media_demanda=("demanda", "mean"), dias=("data", "nunique"))
semana = semana.set_index("dia_semana").reindex(range(7)).reset_index()
semana["dia"] = nomes
fig_sem = px.bar(semana, x="dia", y="media_demanda", color_discrete_sequence=[TURQUESA], labels={"dia":"Dia da semana", "media_demanda":"Demanda média diária (un.)"}, hover_data={"dias":True})
st.plotly_chart(fig_layout(fig_sem, 335), use_container_width=True)
st.caption("Média da demanda total por dia da semana, somente nos dias presentes na base filtrada. Diferenças observadas não comprovam causalidade nem sazonalidade consistente.")

st.subheader("04 · O que podemos concluir nesta primeira versão?")
if demanda > 0:
    diferenca = demanda - vendas
    pct = 100 * diferenca / demanda
    if diferenca >= 0:
        frase = f"As unidades vendidas ficaram {abs(diferenca):,.0f} unidades abaixo da demanda estimada ({pct:.1f}% da demanda acumulada)."
    else:
        frase = f"As unidades vendidas superaram a demanda estimada em {abs(diferenca):,.0f} unidades ({abs(pct):.1f}% da demanda acumulada)."
else:
    frase = "A demanda estimada total é zero nesta seleção; não é possível calcular a diferença percentual."
st.write(frase)
st.caption("A diferença entre vendas e demanda estimada não é, isoladamente, uma medida comprovada de vendas perdidas: depende de como a demanda foi construída no dataset.")
st.markdown("**Próximo passo do projeto:** usar os padrões identificados na análise exploratória para orientar o estudo separado de modelos estatísticos de previsão de demanda.")

with st.expander("Sobre os dados e as limitações"):
    st.write("Este dashboard usa o arquivo `data/gold/vendas_analise.parquet` preparado pelo grupo. Os valores são descritivos e respeitam os filtros selecionados. A base é sintética, portanto os padrões não devem ser generalizados automaticamente para estabelecimentos reais.")
    st.write("O objetivo é apresentar indicadores, distribuições e séries temporais de forma acessível. O laboratório de previsão com sete métodos permanece em `experiments/sprint4_previsao/`, como estudo independente.")
    st.caption(f"Registros na seleção: {len(base_f):,} · Datas: {base_f['data'].min():%d/%m/%Y} a {base_f['data'].max():%d/%m/%Y}")
