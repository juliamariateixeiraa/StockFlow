import streamlit as st

st.set_page_config(
    page_title="StockFlow",
    page_icon=":material/inventory_2:",
    layout="wide"
)

navegacao = st.navigation([
    st.Page("paginas/panorama.py", title="Panorama", icon=":material/bar_chart:", default=True),
    st.Page("paginas/reposicao.py", title="Reposição", icon=":material/shopping_cart:"),
])
navegacao.run()
