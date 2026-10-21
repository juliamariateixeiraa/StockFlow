# Log de Tratamento dos Dados

Segue as seções 3, 4, 5 e 6 do Plano de Preparação de Dados. Duas etapas: Bronze → Silver (Sprint 2, `notebooks/01_tratamento.ipynb`) e Silver → Gold análise (Sprint 3, `notebooks/02_eda.ipynb`).

## Bronze → Silver (Sprint 2)

- **Bronze:** `data/bronze/sales_data.csv` — 76.000 linhas, 16 colunas. Período de 01/01/2022 a 30/01/2024 (760 dias), 5 lojas e 20 produtos.
- **Silver:** `data/silver/vendas_tratadas.parquet` — 76.000 linhas, 21 colunas (as 16 originais + 5 colunas de marcação).

| Etapa | O que foi feito | Linhas/valores afetados | Justificativa |
|-------|-----------------|-------------------------|---------------|
| 1. Leitura do CSV | Leitura do CSV original e cópia para trabalho. | 76.000 linhas, 16 colunas | A camada Bronze nunca é alterada. |
| 2. Visão geral | Confirmação do período e das classes, pendentes no plano. | Data final: 30/01/2024. Clima: Cloudy, Rainy, Snowy, Sunny. Desconto: 0, 5, 10, 15, 20, 25. | O plano deixou a data final e a lista de climas para confirmar na Sprint 2. |
| 3. Padronização de nomes e texto | Colunas renomeadas para snake_case; espaços e maiúsculas padronizados nas categóricas. | 16 colunas renomeadas; nenhuma classe duplicada por escrita diferente | Evita que a mesma classe vire duas por causa de espaço ou maiúscula. |
| 4. Conversão de tipos | Data como data; IDs e categóricas como texto; quantidades como inteiro; Promotion e Epidemic mantidas em 0/1. | Todas as colunas conferidas; data convertida de texto | Evita cálculo errado (ex.: ID tratado como número). |
| 5. Duplicados | Verificação da chave data × loja × produto. | 0 duplicados; 0 linhas removidas | A chave deve ser única. |
| 6a. Faltantes — nulos | Contagem de nulos por coluna. | 0 nulos | Passo 1 do plano. |
| 6b. Faltantes — linhas ausentes | Verificação de todas as combinações data × loja × produto. | 76.000 esperadas, 76.000 existentes; 0 ausentes | Linha que não existe também é dado faltante. |
| 6c. Faltantes — zeros | Verificação de zeros que poderiam esconder faltante. | 406 dias com estoque zero, todos com venda zero; nenhum dia com venda zero e estoque positivo. Pedido zero em 62% das linhas. | Venda zero só ocorre sem estoque, então é consequência e não falta de registro. Pedido zero = não houve pedido (seção 2 do plano). |
| 6d. Mecanismo de falta | Classificação MCAR/MAR/MNAR. | Sem nulos, nada a classificar | Regra mantida no notebook para a importação de planilhas reais. |
| 6e. Venda censurada | Contagem dos dias em que a venda pode ter sido limitada pelo estoque. | Venda = estoque: 8.654 (11,4%). Demanda > estoque: 10.394 (13,7%). Uma das duas: 11.200 (14,7%). | Nesses dias a venda não mostra toda a demanda (MNAR), como previsto na seção 3. |
| 6f. Consistência de Demand | Verificação se a venda passa da demanda. Criada `flag_venda_maior_demanda`. | 21.000 linhas (27,6%), diferença mediana de 8 unidades. Taxa parecida em todas as lojas, categorias e com/sem promoção. | O plano condiciona o uso de Demand como alvo à consistência da coluna. As linhas foram marcadas, não removidas, porque não dá para saber qual valor está errado. |
| 7. Valores impossíveis | Verificação de negativos, preço ≤ 0 e desconto fora de 0–100. | 0 casos; 0 linhas removidas | São erros, não sinal (seção 4). |
| 7b. Venda acima do estoque | Verificação de venda maior que o estoque. | 0 casos | Indica que o estoque registrado é o disponível no dia, ponto que o plano deixou em aberto para a regra de ruptura. |
| 7c. Consistência entre colunas | Verificação de categoria por loja × produto, região por loja, clima por dia × região, estação × mês e promoção × desconto. Só verificação, nenhum dado alterado. | Todas passaram. Categoria fixa em cada loja × produto, mas o mesmo `produto_id` tem categoria diferente em cada loja (5 categorias por produto_id). Uma região por loja; um clima por dia × região; estação bate com o mês em 100% das linhas; com promoção o desconto vai de 10 a 25, sem promoção de 0 a 10. | Confirma que não há conflito entre colunas. Mostra que o item de verdade é loja × produto, o que muda o agrupamento do IQR (etapa 8) e das defasagens e médias móveis (Gold). |
| 8. Valores extremos | IQR por loja × produto, com coluna de marcação para venda, demanda, estoque e preço. Pedido fora (62% de zeros). | Venda: 1.104 (1,5%). Demanda: 804 (1,1%). Estoque: 1.119 (1,5%). Preço: 550 (0,7%). | Marcados, não removidos (seção 4). O plano fala em IQR por produto, mas o mesmo `produto_id` tem categoria diferente em cada loja (etapa 7c); agrupar só por produto misturaria itens diferentes. Os extremos de venda ocorrem mais em promoção (3,5% contra 0,5%), o que reforça que são sinal real. |
| 9. Período de epidemia | Registro do tamanho do período. Coluna mantida. | 15.200 linhas (20%), 152 dias em 6 blocos entre 23/04/2022 e 08/01/2024. Venda média de 60,9 com epidemia e 95,8 sem. | O plano mantém a variável e prevê testar o modelo com e sem esse período. |
| 10. Resumo | Comparação entre Bronze e Silver. | 76.000 → 76.000 linhas; 16 → 21 colunas; 0 nulos e 0 chaves repetidas nas duas camadas | Nenhuma linha removida. Mudanças: nomes, tipos e colunas de marcação. |
| 11. Salvar | Base salva em Parquet e relida para conferência. | 76.000 linhas, 21 colunas | Parquet guarda os tipos (seção 6). A carga no banco fica para as Sprints 7 e 8. |

## Silver → Gold análise (Sprint 3)

- **Gold — análise:** `data/gold/vendas_analise.parquet` — 76.000 linhas, 37 colunas (as 21 da Silver + 14 variáveis derivadas + 2 colunas de marcação de extremos bivariados).

| Etapa | O que foi feito | Linhas/valores afetados | Justificativa |
|-------|-----------------|-------------------------|---------------|
| 1. Calendário | `dia_semana` (0 = segunda), `mes`, `ano`, `fim_de_semana`. | Todas as linhas | Seção 5 do plano. |
| 2. Defasagens e média móvel | `_lag1`, `_lag7` e `_mm7` (média dos 7 dias anteriores, sem o próprio dia) para `unidades_vendidas` (prefixo `venda`) e `demanda`, por loja × produto em ordem de data. | 100 nulos no lag1 e 700 no lag7/mm7 (primeiros dias de cada item) | O item é loja × produto (Silver, etapa 7c). Calculadas para os dois alvos possíveis. Não usam o próprio dia, para não vazar informação. |
| 3. Preço | `dif_preco_concorrente` = preço − preço do concorrente; `preco_com_desconto` = preço × (1 − desconto/100). | Todas as linhas | Preço e concorrente têm correlação de 0,98; a diferença quase não se relaciona com o preço (−0,07). |
| 4. Cobertura de estoque | `cobertura_estoque` = estoque ÷ `venda_mm7`. | 700 nulos (primeiros 7 dias de cada item) | Estoque é o do início do dia (Silver, etapa 7b), então a cobertura é conhecida antes do dia. |
| 5. Rótulo de ruptura | `ruptura` = 1 quando venda ≥ estoque **ou** demanda > estoque. | 11.200 linhas (14,7%) | Pega os 806 dias com estoque zerado em que a `demanda` registrada ficou abaixo da venda (90% marcados como inconsistentes). Venda ≥ estoque é a única regra possível na planilha real, que não tem demanda. Prioriza o recall, como a pesquisa de métodos pede. |
| 6. Extremos bivariados | Distância de Mahalanobis por loja × produto (limite: qui-quadrado 99,9%, 2 g.l.). Colunas `extremo_biv_preco_com_desconto` e `extremo_biv_estoque`. | Preço × demanda: 178 (0,23%). Estoque × demanda: 365 (0,48%). | Marcados, não removidos (seção 4). Os de preço × demanda são 99% os mesmos extremos univariados (picos de promoção). |
| 7. Salvar | Base salva em Parquet e relida para conferência. | 76.000 linhas, 37 colunas; 0 chaves repetidas | Nenhuma linha removida. |

## Decisões tomadas na EDA (Sprint 3)

Os números e gráficos que sustentam cada decisão estão no `notebooks/02_eda.ipynb` (seção indicada).

| Ponto | Decisão | Evidência |
|-------|---------|-----------|
| Regra da ruptura | Venda ≥ estoque ou demanda > estoque (14,7% dos dias). | Etapa 5 acima; seção 2.5. |
| Alvo da regressão | `demanda`, mantendo `flag_venda_maior_demanda`. A alternativa do plano (venda sem os dias de ruptura) entra como teste de robustez na Sprint 4. | A demanda se relaciona mais com promoção (0,28 × 0,23) e epidemia (−0,36 × −0,32), é menos assimétrica (0,61 × 0,79) e não é censurada. Nos dias sem ruptura, as duas têm correlação de 0,91 (seção 12). |
| Estação × mês | `estacao` nos modelos; `mes` só para análise e filtros. | Sem epidemia, os dois explicam o mesmo (η² 0,0099 × 0,0103). Na base toda o mês parece melhor só porque os blocos de epidemia caíram em meses específicos (seção 6). |
| Log no alvo | Não aplicar. | Assimetria de 0,61; com log vai para −1,1 (seção 4). |
| Dia da semana e fim de semana | Fora dos modelos. | Demanda de 103 a 105 em todos os dias; t de Welch p = 0,82, d = 0,02 (seções 5 e 10.3). |
| Preço do dia | `preco`, `preco_com_desconto` e `preco_concorrente` fora do modelo principal de demanda. Uma versão com preço pode ser treinada só para mostrar o efeito. | Dentro de cada item e nível de desconto, o preço explica de 92% a 98% da demanda (R² mediano 0,965), relação exata demais para loja real: o gerador sintético parece calcular o preço a partir da demanda. Entre itens a correlação é −0,51; dentro do item, +0,81 (seção 8.1). |
| Promoção × desconto | Usar `promocao`; `desconto` fica fora. | Sem promoção a demanda é ~95 com qualquer desconto; com promoção, ~123 com qualquer desconto (seção 7). |
| Diferença para o concorrente | Testar na Sprint 4; sai se não reduzir o erro. | Correlação de 0,003 com a demanda, p = 0,49 (seções 7 e 8). |
| Primeiros 7 dias de cada item | Excluir dos modelos. | 700 linhas (0,9%) sem defasagem nem cobertura. |
| Valores extremos | Manter todos, marcados. | Extremos de demanda são picos de promoção (2,9% com promoção × 0,15% sem), quase todos para cima (seção 11). |
| Classificação da ruptura | `cobertura_estoque` como variável central; a regra "alerta quando cobertura < 2 dias" é a referência que o modelo precisa superar. | Cobertura < 1 dia: 84% de ruptura; < 2 dias concentra 95% das rupturas (seção 10.2). |
| Estoque de segurança | Normal com z = 1,65 (95%). Para 99%, usar o quantil observado do erro. | Resíduo quase simétrico (0,2) com cauda direita um pouco pesada: 94,6% observado × 95,1% teórico a 95%; 98,3% × 99,0% a 99% (seção 10.1). |

## Pendente para a Gold de modelos (Sprints 4 a 6)

One-hot de `categoria`, `clima` e `estacao`; padronização (z-score) calculada só no treino; divisão treino/teste por data. Prazo de entrega padrão e nível de serviço continuam em aberto (pesquisa de métodos, seção 7).
