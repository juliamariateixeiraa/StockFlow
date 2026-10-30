"""StockFlow — estudo acadêmico global de previsões agregadas por horizonte."""
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from statsmodels.tsa.holtwinters import ExponentialSmoothing

st.set_page_config(page_title='StockFlow | Estudo comparativo',page_icon='📊',layout='wide')
st.markdown('''<style>
.block-container{padding-top:1.5rem;max-width:1450px}
[data-testid="stMetric"]{border:1px solid #2B5660;border-radius:13px;padding:14px;background:#132F43}
[data-testid="stMetricLabel"]{color:#B6CED3}
[data-testid="stSidebar"]{background:#10283F}
[data-testid="stSidebar"] *{color:#EAF4F5}
h1,h2,h3{letter-spacing:-.025em}
.stTabs [data-baseweb="tab-highlight"]{background:#26B4A3}
.stTabs [data-baseweb="tab"]{font-weight:600}
</style>''',unsafe_allow_html=True)
from motor import METODOS, carregar

def resumo(tab):
    if tab.empty:return pd.DataFrame()
    r=tab.groupby('Método',as_index=False).agg(Observações=('Real','size'),Séries=('Produto',lambda x:0),Erro_absoluto=('Erro absoluto','sum'),Erro_quadrático=('Erro quadrático','sum'),Volume_real=('Real','sum'))
    r['Séries']=[tab[tab['Método']==m][['Loja','Produto']].drop_duplicates().shape[0] for m in r['Método']]
    r['MAE (un./período)']=r['Erro_absoluto']/r['Observações']
    r['RMSE (un./período)']=np.sqrt(r['Erro_quadrático']/r['Observações'])
    r['WAPE (%)']=np.where(r['Volume_real']>0,100*r['Erro_absoluto']/r['Volume_real'],np.nan)
    r['Índice 100−WAPE (%)']=100-r['WAPE (%)']
    return r[['Método','Observações','Séries','MAE (un./período)','RMSE (un./período)','WAPE (%)','Índice 100−WAPE (%)']].sort_values('WAPE (%)').reset_index(drop=True)

def grafico_comparativo(tab,metodos):
    fig=go.Figure()
    real=tab[tab['Método']==metodos[0]].sort_values('Início')
    labels=real['Início'].dt.strftime('%d/%m/%y')
    fig.add_bar(x=labels,y=real['Real'],name='Real',marker_color='#137F78')
    cores=['#D9A441','#A994E8','#30C4B0','#A0C7F3','#F29D74','#DB87B7','#B6C9D7']
    for i,m in enumerate(metodos):
        gg=tab[tab['Método']==m].sort_values('Início')
        fig.add_scatter(x=labels,y=gg['Previsto'],name=m,mode='lines+markers',line={'color':cores[i],'width':2})
    fig.update_layout(height=435,hovermode='x unified',yaxis_title='Unidades totais por período',xaxis_title='Início de cada período',legend=dict(orientation='h',y=1.2),margin=dict(t=85))
    return fig

try:df=carregar()
except Exception as exc:
    st.error(f'Falha ao ler base Gold: {exc}');st.stop()

with st.sidebar:
    st.title('📦 StockFlow')
    st.caption('Sprint 4 · Estudo estatístico global')
    alvo=st.radio('Variável avaliada',[x for x in ['demanda','unidades_vendidas'] if x in df],format_func=lambda x:'Demanda estimada' if x=='demanda' else 'Unidades vendidas')
    h=st.selectbox('Horizonte de previsão',[7,14,30],format_func=lambda x:{7:'Semanal · 7 dias',14:'Quinzenal · 14 dias',30:'Mensal · 30 dias'}[x])
    st.caption('Avaliação fixa: 5 períodos históricos completos (pré-calculados).')
    sazonal=st.checkbox('Holt-Winters com sazonalidade semanal',False,help='Desativado: Holt com tendência amortecida. Ativado: Holt-Winters sazonal.')
    st.caption('O ranking usa resultados já calculados. Troque de horizonte sem recalcular os modelos.')
    st.caption('Resultados lidos de arquivos pré-calculados.')
    st.divider()
    st.caption('Sem reposição de estoque; exclusivamente comparação de métodos de previsão.')

st.title('📈 StockFlow | Laboratório de previsão')
st.caption('Resultados pré-calculados • filtros sem ajustes estatísticos ao vivo')
st.write('**Objetivo:** descobrir qual método estatístico estima melhor o **total de demanda em 7, 14 ou 30 dias** no conjunto de lojas e produtos, usando apenas dados anteriores a cada período previsto.')
st.info('Cada método é avaliado nas mesmas janelas históricas, com previsões emitidas antes do começo do período. O ranking geral usa WAPE calculado a partir dos erros absolutos de **cada loja, produto e período** — os erros não se cancelam.')

chave=f'{alvo}_{h}d_{"sazonal" if sazonal else "sem_sazonal"}'
pasta=Path(__file__).with_name('resultados')
arquivo=pasta/f'{chave}.parquet'
if not arquivo.exists():
    st.warning('Os resultados ainda não foram gerados para esta opção. No terminal, execute **python precomputar.py** (apenas uma vez).')
    st.stop()
@st.cache_data(show_spinner=False)
def ler_precalculado(nome):
    raiz=Path(__file__).with_name('resultados')
    tabela=pd.read_parquet(raiz/f'{nome}.parquet')
    meta=pd.read_json(raiz/f'{nome}_meta.json').iloc[0]
    ocorrencias=pd.read_csv(raiz/f'{nome}_ocorrencias.csv')
    return tabela,ocorrencias,int(meta.total_series),int(meta.series_validas),int(meta.candidatos)
tab,issues,total_series,series_validas,candidatos=ler_precalculado(chave)
if tab.empty:
    st.error('Nenhuma combinação teve dados suficientes para validar. Reduza os períodos ou revise a base.');st.stop()
rank=resumo(tab)
q1,q2,q3,q4=st.columns(4)
q1.metric('Séries avaliadas',f'{series_validas}/{total_series}')
q2.metric('Janelas comparadas',f'{len(tab)//len(METODOS)}')
q3.metric('Melhor WAPE agregado',f"{rank.iloc[0]['WAPE (%)']:.1f}%")
q4.metric('Melhor método',rank.iloc[0]['Método'])
st.caption(f'Cobertura: {len(tab)//len(METODOS)} de {candidatos} pares série/período potenciais. Resultados calculados na base histórica até {df.data.max():%d/%m/%Y}.')

t1,t2,t3=st.tabs(['🏆 Ranking geral','🏬 Lojas e produtos','📚 Metodologia e qualidade'])
with t1:
    st.subheader('Comparação geral — todas as lojas e produtos elegíveis')
    st.dataframe(rank.style.format({'MAE (un./período)':'{:,.1f}','RMSE (un./período)':'{:,.1f}','WAPE (%)':'{:.2f}%','Índice 100−WAPE (%)':'{:.2f}%'}),use_container_width=True,hide_index=True)
    st.caption('Menores MAE, RMSE e WAPE indicam menores erros neste teste. **WAPE** é o critério de ordenação; não é uma probabilidade de acerto.')
    st.plotly_chart(px.bar(rank,x='Método',y='WAPE (%)',text='WAPE (%)',color_discrete_sequence=['#137F78'],title='Erro percentual ponderado por volume — quanto menor, melhor').update_traces(texttemplate='%{text:.1f}%',textposition='outside').update_layout(yaxis_title='WAPE (%)',height=390),use_container_width=True)
    base=tab.copy()
    base['Chave']=base['Loja']+' / '+base['Produto']
    g=base.groupby(['Chave','Método'],as_index=False).agg(abs_err=('Erro absoluto','sum'),volume=('Real','sum'))
    g['WAPE']=np.where(g.volume>0,100*g.abs_err/g.volume,np.nan)
    piv=g.pivot(index='Chave',columns='Método',values='WAPE')
    vencedores=piv.idxmin(axis=1).value_counts().reindex(METODOS,fill_value=0).reset_index()
    vencedores.columns=['Método','Séries onde obteve menor WAPE']
    st.subheader('Em quantas combinações loja/produto cada método venceu?')
    st.dataframe(vencedores,hide_index=True,use_container_width=True)
    st.caption('Empates recebem desempate pela ordem das colunas. A quantidade de vencedores não substitui a avaliação de WAPE agregado.')
    st.download_button('⬇️ Baixar resultados completos (.csv)',tab.to_csv(index=False).encode('utf-8-sig'),file_name='stockflow_avaliacao_global.csv',mime='text/csv')
with t2:
    st.subheader('Investigar resultados por loja, produto e categoria')
    aa,bb,cc=st.columns(3)
    with aa:loja=st.selectbox('Loja',['Todas']+sorted(tab['Loja'].unique().tolist()))
    d=tab if loja=='Todas' else tab[tab['Loja']==loja]
    with bb:categoria=st.selectbox('Categoria',['Todas']+sorted(d['Categoria'].unique().tolist()))
    if categoria!='Todas':d=d[d['Categoria']==categoria]
    with cc:produto=st.selectbox('Produto',['Todos']+sorted(d['Produto'].unique().tolist()))
    if produto!='Todos':d=d[d['Produto']==produto]
    rr=resumo(d)
    if rr.empty:st.warning('Não há resultados para essa seleção.')
    else:
        st.dataframe(rr.style.format({'MAE (un./período)':'{:,.1f}','RMSE (un./período)':'{:,.1f}','WAPE (%)':'{:.2f}%','Índice 100−WAPE (%)':'{:.2f}%'}),hide_index=True,use_container_width=True)
        st.caption('O ranking é recalculado apenas sobre os registros filtrados.')
        if d[['Loja','Produto']].drop_duplicates().shape[0]==1:
            st.plotly_chart(grafico_comparativo(d,rr['Método'].tolist()),use_container_width=True)
        else:
            by=d.groupby(['Loja','Método'],as_index=False).agg(erro=('Erro absoluto','sum'),volume=('Real','sum'))
            by['WAPE (%)']=np.where(by.volume>0,100*by.erro/by.volume,np.nan)
            st.plotly_chart(px.bar(by,x='Loja',y='WAPE (%)',color='Método',color_discrete_sequence=['#D9A441','#A994E8','#30C4B0','#A0C7F3','#F29D74','#DB87B7','#B6C9D7'],barmode='group',title='WAPE por loja').update_layout(height=410),use_container_width=True)
        st.download_button('⬇️ Baixar seleção (.csv)',d.to_csv(index=False).encode('utf-8-sig'),file_name='stockflow_avaliacao_filtrada.csv',mime='text/csv')
with t3:
    st.subheader('Como as previsões foram avaliadas?')
    st.markdown("""- **Unidade de avaliação:** total previsto de demanda por **loja × produto × período de 7, 14 ou 30 dias**.
- **Cortes históricos:** cinco períodos completos, não sobrepostos, terminando na data máxima da base. Todos os modelos utilizam as mesmas janelas elegíveis.
- **Modelo Ridge:** α=10 fixo, com intercepto não penalizado; para uma seleção definitiva seria necessário ajustar hiperparâmetros em validação separada.
- **Previsão ingênua sazonal:** repete os últimos sete valores disponíveis, mesmo em horizontes de 14 ou 30 dias; isso pressupõe ciclo semanal.
- **Sem vazamento do alvo:** cada método usa somente a demanda disponível antes de começar o período de teste. A regressão considera apenas indicadores de calendário conhecidos antecipadamente, não promoções futuras desconhecidas.
- **Modelos:** média móvel de 7 dias, média dos períodos recentes, Holt/Holt-Winters, regressão por mínimos quadrados com calendário, Ridge com padronização e penalização L2 (α=10), ingênua do último dia e ingênua sazonal que repete os últimos 7 dias.
- **Indicadores:** MAE e RMSE em unidades por período; WAPE como soma dos erros absolutos dividida pela soma dos volumes reais; `100 − WAPE` é apenas índice didático, não taxa literal de acerto.
- **Meta exploratória de 70%:** equivale a WAPE de até 30%; não atingí-la não demonstra que machine learning será melhor.
- **Séries incompletas:** lacunas de treino são interpoladas apenas no histórico disponível; janelas de teste com datas faltantes são excluídas. Séries com datas duplicadas são excluídas para auditoria.
- **Limitação:** dados sintéticos, sazonalidade e fatores externos podem não se refletir como no varejo real. A soma de demanda semanal não garante ausência de rupturas diárias.
- **Comparação por volume:** WAPE agregado dá mais peso aos produtos com maior demanda. A aba Lojas e produtos permite inspecionar o desempenho de cada segmento. Não há escolha de modelo definitivo nem recomendação de compras nesta sprint.""")
    if not issues.empty:
        st.warning(f'{len(issues)} ocorrência(s) de dados/modelagem exigem atenção. Algumas séries ou janelas podem ter sido excluídas.')
        st.dataframe(issues.drop_duplicates().head(100),hide_index=True,use_container_width=True)
    else:st.success('Nenhum problema de série duplicada ou ajuste registrado.')
    st.caption('Recomendação acadêmica: repetir a comparação com diferentes horizontes e conferir a cobertura e a robustez dos resultados antes de escolher um método.')
