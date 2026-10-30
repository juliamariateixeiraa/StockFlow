from pathlib import Path
import warnings
import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
METODOS=['Média móvel (7d)', 'Média de períodos', 'Holt / Holt-Winters', 'Regressão (calendário)', 'Regressão Ridge', 'Ingênua (último dia)', 'Ingênua sazonal (7d)']

def carregar():
    raiz = Path(__file__).resolve().parents[2]
    arquivo = raiz / "data" / "gold" / "vendas_analise.parquet"

    if not arquivo.exists():
        raise FileNotFoundError(
            f"Base Gold não encontrada: {arquivo}"
        )

    d = pd.read_parquet(arquivo)
    d["data"] = pd.to_datetime(
        d["data"], errors="coerce"
    ).dt.normalize()

    return d.dropna(subset=["data"])

def matriz_calendario(datas,origem):
    d=pd.DatetimeIndex(datas)
    t=(d-origem).days.to_numpy(dtype=float)
    w=d.dayofweek.to_numpy(dtype=float)
    m=d.month.to_numpy(dtype=float)
    return np.column_stack([np.ones(len(d)),t/365.25,np.sin(2*np.pi*w/7),np.cos(2*np.pi*w/7),np.sin(2*np.pi*(m-1)/12),np.cos(2*np.pi*(m-1)/12)])

def modelos(treino,h,sazonal):
    """Prever h dias sem utilizar observações do próprio período previsto."""
    if len(treino)<90 or treino.notna().sum()<70: raise ValueError('Histórico de treino insuficiente')
    if treino.isna().all(): raise ValueError('Sem dados de treinamento')
    # Preenchimento limitado ao conjunto de treinamento; sem tocar no intervalo de teste.
    y=treino.interpolate(limit_direction='both')
    if not np.isfinite(y.to_numpy(dtype=float)).all():raise ValueError('Dados inválidos')
    futuro=pd.date_range(y.index[-1]+pd.Timedelta(days=1),periods=h,freq='D')
    mm7=max(float(y.tail(7).mean())*h,0)
    blocos=y.iloc[-min(len(y),h*8):]
    n=len(blocos)//h
    soma=blocos.iloc[-n*h:].to_numpy(dtype=float).reshape(n,h).sum(axis=1) if n else np.array([])
    mp=max(float(soma.mean()),0) if len(soma) else max(float(y.tail(h).sum()),0)
    x=matriz_calendario(y.index,y.index[0]);xf=matriz_calendario(futuro,y.index[0])
    beta=np.linalg.lstsq(x,y.to_numpy(dtype=float),rcond=None)[0]
    reg=float(np.maximum(xf@beta,0).sum())
    # Ridge: padronização no treino; intercepto não penalizado. Alpha é fixo (não otimizado no teste).
    x0=x[:,1:]; xf0=xf[:,1:]
    mu=x0.mean(axis=0); scale=x0.std(axis=0); scale=np.where(scale>1e-12,scale,1.)
    z=(x0-mu)/scale; zf=(xf0-mu)/scale
    yt=y.to_numpy(dtype=float); ym=yt.mean()
    alpha=10.0
    weights=np.linalg.solve(z.T@z + alpha*np.eye(z.shape[1]), z.T@(yt-ym))
    ridge=float(np.maximum(ym+zf@weights,0).sum())
    # Ingênua: mantém a última demanda observada durante os próximos h dias.
    ingenua=max(float(y.iloc[-1]),0)*h
    # Ingênua sazonal: repete os últimos 7 dias para o futuro (sem acessar período de teste).
    ult7=y.iloc[-7:].to_numpy(dtype=float)
    ingenua_sazonal=float(np.maximum(np.resize(ult7,h),0).sum())
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        fit=ExponentialSmoothing(y,trend='add',damped_trend=True,seasonal='add' if sazonal else None,seasonal_periods=7 if sazonal else None,initialization_method='estimated').fit(optimized=True)
        holt=float(np.maximum(np.asarray(fit.forecast(h),dtype=float),0).sum())
    return dict(zip(METODOS,[mm7,mp,holt,reg,ridge,ingenua,ingenua_sazonal]))

def preparar_serie(g,alvo):
    if g['data'].duplicated().any():raise ValueError('Datas duplicadas')
    y=pd.to_numeric(g.set_index('data').sort_index()[alvo],errors='coerce')
    if (y.dropna()<0).any():raise ValueError('Valores negativos')
    return y.reindex(pd.date_range(y.index.min(),y.index.max(),freq='D')).astype(float)

def avaliar_todas(alvo,h,n_janelas,sazonal):
    df=carregar()
    out=[]; issues=[]; series=0; validas=0; candidatos=0
    # Janela histórica fixada ao último dia global para comparabilidade de calendário.
    fim_global=pd.Timestamp(df['data'].max())
    for (loja,produto),g in df.groupby(['loja_id','produto_id'],sort=True):
        series+=1
        try:y=preparar_serie(g,alvo)
        except ValueError as exc:
            issues.append({'Loja':str(loja),'Produto':str(produto),'Motivo':str(exc)});continue
        algum=False
        for i in reversed(range(n_janelas)):
            fim=fim_global-pd.Timedelta(days=i*h)
            inicio=fim-pd.Timedelta(days=h-1)
            treino=y.loc[:inicio-pd.Timedelta(days=1)]
            real=y.reindex(pd.date_range(inicio,fim,freq='D'))
            candidatos+=1
            if len(treino)<90 or treino.notna().sum()<70 or real.isna().any():continue
            try:pr=modelos(treino,h,sazonal)
            except Exception as exc:
                issues.append({'Loja':str(loja),'Produto':str(produto),'Motivo':f'Não foi possível ajustar o modelo: {str(exc)[:95]}'})
                continue
            algum=True
            total=float(real.sum())
            cat=str(g['categoria'].iloc[0]) if 'categoria' in g else 'Sem categoria'
            for metodo,prev in pr.items():
                out.append({'Loja':str(loja),'Produto':str(produto),'Categoria':cat,'Início':inicio,'Fim':fim,'Método':metodo,'Real':total,'Previsto':prev,'Erro':prev-total,'Erro absoluto':abs(prev-total),'Erro quadrático':(prev-total)**2})
        if algum:validas+=1
    return pd.DataFrame(out),pd.DataFrame(issues),series,validas,candidatos

