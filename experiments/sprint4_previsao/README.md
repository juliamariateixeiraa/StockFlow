# StockFlow | Sprint 4 — Comparação estatística ampliada

Dashboard de **estudo acadêmico**, não o sistema de produção nem um módulo de reposição. Avalia 100 combinações loja/produto disponíveis na base Gold nos horizontes de 7, 14 e 30 dias, 5 janelas históricas por série. Compara **7 métodos**:

- Média móvel de 7 dias (nível recente × horizonte)
- Média dos períodos recentes de mesmo horizonte
- Holt / Holt-Winters (a opção sazonal altera apenas este modelo)
- Regressão linear com calendário via mínimos quadrados
- Regressão Ridge com calendário (penalização L2, alpha=10 fixo)
- Previsão ingênua (último valor diário repetido por todo o horizonte)
- Previsão ingênua sazonal (repetição cíclica dos últimos 7 dias)

As previsões são **totais de demanda por janela**, não acertos diários. Resultados comparados por MAE, RMSE e WAPE; `100 - WAPE` **não é taxa de acerto**. A regressão e a Ridge usam as mesmas variáveis de calendário. Não utilizam promoção futura, venda futura ou demanda futura.

## Execução (PowerShell)

```powershell
py -3.12 -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python precomputar.py
python -m streamlit run app.py
```

O cálculo produz 12 arquivos `.parquet` em `resultados/` (2 alvos × 3 horizontes × 2 opções de sazonalidade). **Os resultados de versões anteriores com quatro modelos NÃO podem ser reaproveitados** para comparar sete modelos; execute novamente `precomputar.py`. Os resultados ficam salvos e a interface não recalcula os modelos. Para priorizar somente demanda, use `python precomputar.py --somente-demanda`; os cenários de unidades vendidas não estarão disponíveis até processá-los.

## Limitações e interpretação

- Holt/Holt-Winters pode exigir bastante processamento.
- Ridge usa alpha=10 sem ajuste fino; desempenho não é necessariamente ótimo.
- Sazonalidade semanal deve ser comprovada na EDA; a opção sazonal não altera os demais modelos.
- WAPE agregado dá maior peso a produtos de maior volume. Inspecione o ranking por loja/produto, não só o geral.
- Dados sintéticos; métricas válidas apenas para as janelas avaliadas. Antes de selecionar um modelo para produção, faça validação temporal adicional com janelas independentes.
- Qualquer alteração da base ou código estatístico exige executar novamente o pré-cálculo.
