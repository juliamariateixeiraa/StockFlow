# Log de Tratamento dos Dados (Bronze → Silver)

Segue as seções 3, 4 e 6 do Plano de Preparação de Dados.

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

## O que fica para a Gold (Sprint 3)

Conforme a seção 5 do plano: dia da semana, mês, fim de semana, venda dos dias anteriores e média móvel (calculadas por loja × produto, em ordem de data), diferença de preço para o concorrente, preço com desconto, cobertura de estoque, rótulo de ruptura, one-hot, padronização e divisão treino/teste por data.

## Pontos para o grupo decidir

- **Alvo da regressão:** a venda passa da demanda em 27,6% das linhas, então a coluna Demand não está totalmente consistente. O plano prevê, nesse caso, treinar sem os dias de ruptura ou mantê-los com marcador e comparar os dois resultados.
- **Regra da ruptura:** como não há venda acima do estoque, o estoque registrado parece ser o do início do dia. O plano aceita "venda ≥ estoque" ou "demanda > estoque". As duas juntas marcam 14,7% dos dias; só demanda > estoque marca 13,7%.
