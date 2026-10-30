"""Execute uma vez: python precomputar.py. Calcula e salva as avaliações de todas as séries."""
from pathlib import Path
import sys
import pandas as pd
from motor import avaliar_todas

OUT=Path(__file__).with_name('resultados')
OUT.mkdir(exist_ok=True)
for alvo in (['demanda'] if '--somente-demanda' in sys.argv else ['demanda','unidades_vendidas']):
    for h in [7,14,30]:
        for sazonal in [False, True]:
            chave=f'{alvo}_{h}d_{"sazonal" if sazonal else "sem_sazonal"}'
            print(f'Calculando {chave}, 5 janelas ...',flush=True)
            tab,issues,total,validas,candidatos=avaliar_todas(alvo,h,5,sazonal)
            if tab.empty:
                print('Sem avaliações válidas:',chave,flush=True)
                continue
            tab.to_parquet(OUT/f'{chave}.parquet',index=False)
            pd.DataFrame(issues,columns=['Loja','Produto','Motivo']).to_csv(OUT/f'{chave}_ocorrencias.csv',index=False)
            pd.DataFrame([{'total_series':total,'series_validas':validas,'candidatos':candidatos}]).to_json(OUT/f'{chave}_meta.json',orient='records')
            print(f'Concluído: {len(tab)} linhas; {validas}/{total} séries.',flush=True)
print('Todas as combinações disponíveis foram salvas em resultados/.')
