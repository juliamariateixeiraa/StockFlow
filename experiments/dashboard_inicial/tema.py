"""Identidade visual do StockFlow, compartilhada pelas páginas do dashboard."""
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# Interface
MARCA = "#1f6b4f"
FUNDO = "#fafaf7"
SUPERFICIE = "#f1f2ec"
TEXTO = "#1f1f1c"
TEXTO_SECUNDARIO = "#5b5b55"
GRADE = "#e4e4dd"

# Séries (validadas para daltonismo e contraste sobre o FUNDO)
DEMANDA = "#0f8a5f"
VENDAS = "#2a78d6"
NEUTRO = "#9a9a94"

# Status dos alertas: reservados, sempre com rótulo ao lado
CRITICO = "#d03b3b"
ATENCAO = "#c98500"

pio.templates["stockflow"] = go.layout.Template(
    layout=dict(
        font=dict(family="Inter, system-ui, sans-serif", color=TEXTO_SECUNDARIO, size=13),
        title=dict(font=dict(color=TEXTO, size=15), x=0, xanchor="left", y=0.97, yanchor="top", yref="container"),
        paper_bgcolor=FUNDO,
        plot_bgcolor=FUNDO,
        colorway=[DEMANDA, VENDAS, NEUTRO],
        xaxis=dict(gridcolor=GRADE, linecolor=GRADE, zeroline=False, ticks=""),
        yaxis=dict(gridcolor=GRADE, linecolor=GRADE, zeroline=False, ticks=""),
        legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="left", x=0, title_text=""),
        hoverlabel=dict(bgcolor="#ffffff", bordercolor=GRADE, font=dict(color=TEXTO)),
        margin=dict(l=10, r=10, t=80, b=10),
        barcornerradius=4,
        bargap=0.25,
        bargroupgap=0.08,
    ),
    data=dict(
        scatter=[go.Scatter(line=dict(width=2), marker=dict(size=8))],
    ),
)
pio.templates.default = "stockflow"


def aplicar_estilo():
    st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {{
        font-family: 'Inter', system-ui, sans-serif;
    }}
    .block-container {{
        padding-top: 3rem;
        padding-bottom: 2rem;
    }}
    h1 {{
        font-weight: 700;
        letter-spacing: -0.02em;
    }}
    h2 {{
        font-weight: 600;
        font-size: 1.35rem !important;
        letter-spacing: -0.01em;
        margin-top: 1.5rem;
    }}
    .marca {{
        color: {MARCA};
        font-weight: 700;
        font-size: 0.85rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0;
    }}
    .info-box {{
        background-color: {SUPERFICIE};
        border-left: 3px solid {MARCA};
        border-radius: 8px;
        padding: 14px 18px;
        margin: 10px 0;
        color: {TEXTO};
    }}
    .info-box ul {{
        margin-bottom: 0;
    }}
    [data-testid="stMetric"] {{
        background-color: #ffffff;
        border: 1px solid {GRADE};
        border-radius: 10px;
        padding: 14px 16px;
    }}
    [data-testid="stMetricValue"] {{
        color: {TEXTO};
        font-weight: 600;
    }}
</style>
""", unsafe_allow_html=True)


def cabecalho(titulo):
    st.markdown('<p class="marca">StockFlow</p>', unsafe_allow_html=True)
    st.title(titulo)
