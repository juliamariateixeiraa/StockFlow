from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# ---------------------------------------------------
st.set_page_config(
    page_title="StockFlow | Reposição de estoque",
    page_icon="📦",
    layout="wide"
)

st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .info-box {
        background-color: rgba(20, 60, 100, 0.55);
        border-radius: 12px;
        padding: 16px;
        margin-top: 10px;
        margin-bottom: 10px;
        color: #d9e6f2;
    }
</style>
""", unsafe_allow_html=True)

CORES_ALERTA = {"Crítico": "#e34948", "Pedir agora": "#d8a541", "OK": "#22b8b2"}
FUNDO = "#061a2b"

# z da normal para os níveis de serviço oferecidos (evita depender do scipy)
Z_NIVEL = {"90%": 1.2816, "95%": 1.6449, "98%": 2.0537, "99%": 2.3263}


# ---------------------------------------------------
# FUNÇÕES
# ---------------------------------------------------
@st.cache_data
def carregar_dados():
    gold = Path(__file__).resolve().parents[3] / "data" / "gold"
    arquivos = {
        "reposicao": gold / "reposicao.parquet",
        "previsao": gold / "reposicao_previsao_diaria.parquet",
        "historico": gold / "vendas_analise.parquet",
    }
    faltando = [str(a) for a in arquivos.values() if not a.exists()]
    if faltando:
        st.error("Não encontrei as tabelas Gold da reposição.")
        st.code("\n".join(faltando))
        st.info("Rode o notebook notebooks/03_reposicao.ipynb para gerar as tabelas.")
        st.stop()

    reposicao = pd.read_parquet(arquivos["reposicao"])
    previsao = pd.read_parquet(arquivos["previsao"])
    historico = pd.read_parquet(arquivos["historico"], columns=["data", "loja_id", "produto_id", "demanda", "estoque"])
    return reposicao, previsao, historico


def desvio_periodo(sigma, rho, n):
    """Desvio do erro somado em n dias, com erros diários AR(1) (notebook 03, seção 4.2)."""
    rho = np.clip(rho, 0, 0.95)
    k = np.arange(1, n)
    soma = n + 2 * np.sum((n - k)[None, :] * np.power.outer(np.atleast_1d(rho), k), axis=1)
    return np.atleast_1d(sigma) * np.sqrt(soma)


def calcular_reposicao(reposicao, previsao, prazo, revisao, z):
    """Mesma conta do notebook 03 (seção 8), refeita com os parâmetros escolhidos."""
    base = reposicao.set_index(["loja_id", "produto_id"]).copy()
    prevista = previsao.pivot_table(index=["loja_id", "produto_id"], columns="dia", values="demanda_prevista")
    base["demanda_prevista_L"] = prevista.loc[base.index, range(1, prazo + 1)].sum(axis=1)
    base["demanda_prevista_LR"] = prevista.loc[base.index, range(1, prazo + revisao + 1)].sum(axis=1)
    sigma, rho = base["sigma_erro"].to_numpy(), base["rho_erro"].to_numpy()
    base["estoque_seguranca"] = z * desvio_periodo(sigma, rho, prazo + revisao)
    base["ponto_pedido"] = base["demanda_prevista_L"] + z * desvio_periodo(sigma, rho, prazo)
    base["quantidade_sugerida"] = np.ceil(np.maximum(
        base["demanda_prevista_LR"] + base["estoque_seguranca"] - base["estoque_atual"], 0)).astype("int64")
    base["alerta"] = np.select(
        [base["estoque_atual"] < base["demanda_prevista_L"], base["estoque_atual"] < base["ponto_pedido"]],
        ["Crítico", "Pedir agora"], "OK")
    base["valor_compra"] = base["quantidade_sugerida"] * base["preco_atual"]
    return base.reset_index()


def formatar_numero(valor):
    return f"{valor:,.0f}".replace(",", ".")


def formatar_reais(valor):
    return "R$ " + f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def grafico_estoque_ponto(dff):
    fig = go.Figure()
    for alerta, cor in CORES_ALERTA.items():
        g = dff[dff["alerta"] == alerta]
        fig.add_trace(go.Scatter(
            x=g["ponto_pedido"], y=g["estoque_atual"], mode="markers", name=alerta,
            marker=dict(color=cor, size=9),
            customdata=np.stack([g["loja_id"], g["produto_id"], g["categoria"]], axis=-1) if len(g) else None,
            hovertemplate="%{customdata[0]} · %{customdata[1]} (%{customdata[2]})<br>"
                          "Ponto de pedido: %{x:.0f}<br>Estoque atual: %{y:.0f}<extra></extra>"
        ))
    limite = dff["ponto_pedido"].max() * 1.25
    fig.add_trace(go.Scatter(
        x=[0, limite], y=[0, limite], mode="lines", name="Estoque = ponto de pedido",
        line=dict(color="#8aa0b4", dash="dash", width=1), hoverinfo="skip"
    ))
    fig.update_layout(
        template="plotly_dark", title="Estoque atual × ponto de pedido",
        xaxis_title="Ponto de pedido (unidades)", yaxis_title="Estoque atual (unidades)",
        paper_bgcolor=FUNDO, plot_bgcolor=FUNDO, legend_title="", xaxis_range=[0, limite]
    )
    return fig


def grafico_item(hist, prev, linha, prazo, revisao):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hist["data"], y=hist["demanda"], mode="lines", name="Demanda registrada",
        line=dict(color="#d8a541", width=2)
    ))
    fig.add_trace(go.Scatter(
        x=prev["data"], y=prev["demanda_prevista"], mode="lines+markers", name="Demanda prevista",
        line=dict(color="#22b8b2", width=3)
    ))
    fim_entrega = prev["data"].iloc[prazo - 1]
    fim_cobertura = prev["data"].iloc[prazo + revisao - 1]
    fig.add_vrect(x0=prev["data"].iloc[0], x1=fim_entrega, fillcolor="#e34948", opacity=0.12, line_width=0,
                  annotation_text="até a entrega", annotation_position="top left")
    if revisao > 0:
        fig.add_vrect(x0=fim_entrega, x1=fim_cobertura, fillcolor="#22b8b2", opacity=0.10, line_width=0,
                      annotation_text="até a próxima entrega", annotation_position="top left")
    fig.update_layout(
        template="plotly_dark",
        title=f"{linha['loja_id']} · {linha['produto_id']}: últimos 60 dias e previsão",
        xaxis_title="Data", yaxis_title="Unidades por dia",
        paper_bgcolor=FUNDO, plot_bgcolor=FUNDO, legend_title=""
    )
    return fig


# ---------------------------------------------------
# DADOS
# ---------------------------------------------------
reposicao_base, previsao, historico = carregar_dados()
data_ref = pd.to_datetime(reposicao_base["data_referencia"].iloc[0])

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------
st.sidebar.title("Parâmetros da reposição")
prazo = st.sidebar.slider("Prazo de entrega do fornecedor (dias)", 1, 14, 1,
                          help="Dias entre fazer o pedido e a mercadoria chegar. Na base, o pedido chega no dia seguinte.")
revisao = st.sidebar.slider("Período de revisão (dias)", 1, 14, 7,
                            help="De quantos em quantos dias você revisa e faz o pedido.")
nivel = st.sidebar.select_slider("Nível de serviço", options=list(Z_NIVEL), value="95%",
                                 help="Chance de não faltar produto até a próxima entrega.")
if nivel in ("98%", "99%"):
    st.sidebar.caption("Acima de 95% o valor é aproximado: o erro do modelo tem a cauda um pouco mais pesada que a normal.")

st.sidebar.title("Filtros")
lojas = ["Todas"] + sorted(reposicao_base["loja_id"].astype(str).unique().tolist())
categorias = ["Todas"] + sorted(reposicao_base["categoria"].astype(str).unique().tolist())
loja_sel = st.sidebar.selectbox("Loja", lojas)
categoria_sel = st.sidebar.selectbox("Categoria", categorias)
alertas_sel = st.sidebar.multiselect("Alerta", list(CORES_ALERTA), default=list(CORES_ALERTA))

reposicao = calcular_reposicao(reposicao_base, previsao, prazo, revisao, Z_NIVEL[nivel])

dff = reposicao.copy()
if loja_sel != "Todas":
    dff = dff[dff["loja_id"] == loja_sel]
if categoria_sel != "Todas":
    dff = dff[dff["categoria"] == categoria_sel]
dff = dff[dff["alerta"].isin(alertas_sel)]

if dff.empty:
    st.warning("Nenhum item encontrado para os filtros selecionados.")
    st.stop()

# ---------------------------------------------------
# TÍTULO
# ---------------------------------------------------
st.title("📦 StockFlow | O que comprar hoje")
st.markdown(f"""
<div class="info-box">
Recomendação de compra para <strong>{data_ref:%d/%m/%Y}</strong>, o último dia da base. Para cada loja × produto, a
previsão de demanda (regressão com calendário, escolhida na Sprint 4) vira um <strong>ponto de pedido</strong> e uma
<strong>quantidade sugerida</strong>, com um estoque de segurança que cobre o erro do modelo. Mude o prazo, a revisão
e o nível de serviço na barra lateral para ver como a sugestão muda.
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# KPIs
# ---------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Itens críticos", formatar_numero((dff["alerta"] == "Crítico").sum()),
          help="O estoque não cobre nem a demanda prevista até a entrega chegar.")
c2.metric("Pedir agora", formatar_numero((dff["alerta"] == "Pedir agora").sum()),
          help="O estoque está abaixo do ponto de pedido.")
c3.metric("Unidades sugeridas", formatar_numero(dff["quantidade_sugerida"].sum()))
c4.metric("Valor da compra", formatar_reais(dff["valor_compra"].sum()))

# ---------------------------------------------------
# 01 - SITUAÇÃO
# ---------------------------------------------------
st.markdown("## 01 · Quais itens estão abaixo do ponto de pedido?")
col1, col2 = st.columns([3, 2])
with col1:
    st.plotly_chart(grafico_estoque_ponto(dff), use_container_width=True)
with col2:
    st.markdown(f"""
<div class="info-box">
<ul>
    <li>Abaixo da linha tracejada, o estoque não atravessa o prazo de <strong>{prazo} dia(s)</strong> com
    {nivel} de segurança: é hora de pedir.</li>
    <li><strong style="color:#e34948">Crítico</strong>: o estoque não cobre nem a demanda prevista até a entrega.
    Vai faltar mesmo pedindo hoje.</li>
    <li>O pedido de hoje cobre <strong>{prazo + revisao} dias</strong>: o prazo de entrega mais o período até a
    próxima revisão.</li>
</ul>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# 02 - LISTA DE COMPRAS
# ---------------------------------------------------
st.markdown("## 02 · Lista de compras")
ordem = {"Crítico": 0, "Pedir agora": 1, "OK": 2}
lista = (
    dff.assign(_ordem=dff["alerta"].map(ordem), _folga=dff["estoque_atual"] - dff["ponto_pedido"])
       .sort_values(["_ordem", "_folga"])
       [["alerta", "loja_id", "produto_id", "categoria", "estoque_atual", "demanda_prevista_L",
         "ponto_pedido", "estoque_seguranca", "quantidade_sugerida", "valor_compra"]]
)
st.dataframe(
    lista.style.apply(lambda col: [f"color: {CORES_ALERTA[v]}; font-weight: 600" for v in col], subset=["alerta"]),
    use_container_width=True, hide_index=True,
    column_config={
        "alerta": "Alerta", "loja_id": "Loja", "produto_id": "Produto", "categoria": "Categoria",
        "estoque_atual": st.column_config.NumberColumn("Estoque atual", format="%d"),
        "demanda_prevista_L": st.column_config.NumberColumn("Demanda até a entrega", format="%.0f"),
        "ponto_pedido": st.column_config.NumberColumn("Ponto de pedido", format="%.0f"),
        "estoque_seguranca": st.column_config.NumberColumn("Estoque de segurança", format="%.0f"),
        "quantidade_sugerida": st.column_config.NumberColumn("Comprar (un.)", format="%d"),
        "valor_compra": st.column_config.NumberColumn("Valor (R$)", format="%.2f"),
    },
)

# ---------------------------------------------------
# 03 - DETALHE DO ITEM
# ---------------------------------------------------
st.markdown("## 03 · De onde vem a sugestão de um item?")
opcoes = (lista["loja_id"] + " · " + lista["produto_id"]).tolist()
escolha = st.selectbox("Item", opcoes)
loja_item, produto_item = escolha.split(" · ")
linha = reposicao[(reposicao["loja_id"] == loja_item) & (reposicao["produto_id"] == produto_item)].iloc[0]

hist = historico[(historico["loja_id"] == loja_item) & (historico["produto_id"] == produto_item)]
hist = hist[hist["data"] >= data_ref - pd.Timedelta(59, unit="D")]
prev = previsao[(previsao["loja_id"] == loja_item) & (previsao["produto_id"] == produto_item)]
prev = prev[prev["dia"] <= prazo + revisao]

col1, col2 = st.columns([3, 2])
with col1:
    st.plotly_chart(grafico_item(hist, prev, linha, prazo, revisao), use_container_width=True)
with col2:
    st.markdown(f"""
<div class="info-box">
<p><strong>Conta da quantidade sugerida</strong></p>
<ul>
    <li>Demanda prevista em {prazo + revisao} dias: <strong>{formatar_numero(linha['demanda_prevista_LR'])}</strong></li>
    <li>+ Estoque de segurança: <strong>{formatar_numero(linha['estoque_seguranca'])}</strong>
    (erro típico do modelo: {linha['sigma_erro']:.0f} un./dia)</li>
    <li>− Estoque atual: <strong>{formatar_numero(linha['estoque_atual'])}</strong></li>
    <li>= Comprar: <strong>{formatar_numero(linha['quantidade_sugerida'])} unidades</strong>
    ({formatar_reais(linha['valor_compra'])})</li>
</ul>
<p><strong>O que pesa na previsão:</strong> sazonalidade do ano de ±{linha['amplitude_ano']:.0f} un./dia,
dia da semana de ±{linha['amplitude_semana']:.0f} un./dia e tendência de {linha['tendencia_ano']:+.0f} un./dia por ano.
O modelo não conhece promoções futuras: em semana de promoção, reforce o pedido.</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# 04 - CONFIANÇA NA REGRA
# ---------------------------------------------------
st.markdown("## 04 · A regra funciona?")
st.markdown("""
<div class="info-box">
<p>Teste com os últimos 84 dias da base (notebook 03, seção 10). A regra foi simulada com a demanda real e comparada
com a reposição que aconteceu de verdade. Prazo de 1 dia e nível de serviço de 95%:</p>
<ul>
    <li><strong>Reposição real da base:</strong> falta de produto em 14,3% dos dias, 93,9% da demanda atendida.</li>
    <li><strong>StockFlow, revisão diária:</strong> 3,4% dos dias com falta e estoque médio 24% <em>menor</em>.</li>
    <li><strong>StockFlow, revisão a cada 3 dias:</strong> 1,3% dos dias com falta, com menos pedidos que a base.</li>
    <li><strong>StockFlow, revisão semanal:</strong> 0,6% dos dias com falta, mas mais que o dobro de estoque.</li>
</ul>
<p>Dados sintéticos: os números mostram o comportamento da regra, não um resultado garantido em uma loja real.</p>
</div>
""", unsafe_allow_html=True)
