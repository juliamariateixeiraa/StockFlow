# Pesquisa de Métodos de Previsão

Sprint 2. Define como prever a demanda e a ruptura nas Sprints 4 a 6, dentro dos limites do projeto:

- só regressão simples (previsão de demanda e sugestão de compra) e classificação simples (alerta de ruptura);
- o modelo precisa ser explicável (mostrar quais variáveis pesam na sugestão);
- modelos de série temporal ficam fora (restrições de CC);
- divisão treino/teste por data, nunca aleatória.

## 1. O que os dados já mostram

Primeira leitura da Silver, feita só para orientar a escolha dos métodos. Os números finais saem dos notebooks de modelagem.

| Verificação | Resultado | O que significa |
|---|---|---|
| Venda de ontem x venda de hoje (autocorrelação, média das 100 séries loja × produto) | 0,24 para demanda; 0,16 para venda | O passado recente explica pouco. As defasagens ajudam, mas não devem ser a base do modelo. |
| Demanda por dia da semana | Entre 103,4 e 105,2 em todos os dias | Não há padrão semanal. Dia da semana deve pesar pouco. |
| Demanda por estação e clima | Verão 112,9 x primavera 97,7; ensolarado 115,2 x neve 94,0 | Estação e clima têm efeito visível. |
| Correlação com a demanda | Epidemia −0,36; promoção 0,28; desconto 0,22; preço −0,02 | Os fatores externos explicam mais que o histórico. |

Erro das previsões de referência (seção 2), usando 01/11/2023 a 30/01/2024 como teste:

| Previsão de referência | Erro médio (MAE, unidades) |
|---|---|
| Igual a ontem | 41,0 |
| Igual ao mesmo dia da semana passada | 43,4 |
| Média móvel dos 7 dias anteriores | 32,1 |
| Média histórica do item (treino) | 32,6 |

A média supera "igual a ontem", o que confirma que a demanda oscila muito de um dia para o outro em torno de um nível. Para valer a pena, a regressão precisa ficar abaixo de ~32 unidades de erro.

## 2. Previsões de referência

Antes de qualquer modelo, o grupo mede o erro de métodos simples. Hyndman e Athanasopoulos (seção 5.2) recomendam esses métodos como referência: um método novo só vale a pena se for melhor que eles.

| Método | Como é calculado |
|---|---|
| Ingênuo | Previsão = valor do dia anterior |
| Ingênuo sazonal | Previsão = valor do mesmo dia da semana anterior |
| Média móvel de 7 dias | Previsão = média dos 7 dias anteriores |
| Média histórica | Previsão = média do item no treino |

Todos calculados por loja × produto, em ordem de data. A média móvel é a referência principal, por ter sido a melhor na primeira leitura e por ser o que um gestor faria de cabeça.

## 3. Regressão para a demanda

**Método escolhido: regressão linear múltipla.** É o modelo mais fácil de explicar: cada coeficiente diz quanto a demanda muda quando a variável muda, mantidas as outras. Hyndman e Athanasopoulos (cap. 7) mostram que a regressão linear com variáveis de calendário, variáveis indicadoras e valores defasados é uma forma válida de previsão sem usar modelos de série temporal.

**Variáveis** (as da Gold, seção 5 do Plano de Preparação):

- fatores externos: promoção, desconto, preço com desconto, diferença para o concorrente, clima, estação, epidemia;
- calendário: mês ou estação (só um dos dois), fim de semana;
- histórico: venda dos dias anteriores (1 e 7) e média móvel de 7 dias.

**Alternativa a testar: Ridge.** É a mesma regressão linear com uma penalidade que reduz os coeficientes. A documentação do scikit-learn (seção 1.1.2) indica Ridge quando as variáveis são correlacionadas, como preço, preço com desconto e preço do concorrente. Os coeficientes continuam interpretáveis. Só vale manter se reduzir o erro no teste.

**Cuidados:**

- **Vazamento:** `unidades_vendidas` do mesmo dia tem correlação de 0,83 com a demanda, mas não é conhecida no momento da previsão. Não entra como variável. Defasagens e médias móveis usam só dias anteriores.
- **Alvo:** a venda passa da demanda em 27,6% das linhas (log de tratamento). A decisão entre `demanda` e `unidades_vendidas` continua com o grupo, conforme a seção 3 do Plano de Preparação. O método vale para os dois.
- **Assimetria:** se o alvo for muito assimétrico, aplicar log(1 + x), como já previsto no Plano.

## 4. Classificação para a ruptura

**Método escolhido: regressão logística.** Dá a probabilidade de ruptura e coeficientes que mostram o que aumenta o risco. É a versão para classificação da regressão linear, o que mantém a explicação parecida nos dois modelos.

**Alternativa a testar: árvore de decisão rasa** (profundidade 3 ou 4). As regras podem ser lidas diretamente ("se promoção e cobertura menor que 2 dias, alerta"), o que facilita a explicação no dashboard.

**Desbalanceamento:** a ruptura marca entre 13,7% e 14,7% dos dias, conforme a regra (log de tratamento). Por isso:

- usar `class_weight="balanced"`, que dá mais peso à classe rara (documentação do scikit-learn, `LogisticRegression`);
- escolher o limiar do alerta pela curva precision-recall, não deixar o padrão de 0,5;
- priorizar recall: deixar de avisar uma ruptura custa mais para a Renata que um alarme falso.

## 5. Métricas e validação

**Regressão:**

- **MAE** como métrica principal: erro médio em unidades, fácil de explicar.
- **RMSE** como complemento: pesa mais os erros grandes. Hyndman e Athanasopoulos (seção 5.8) explicam que minimizar o MAE leva a prever a mediana e minimizar o RMSE leva à média.
- **MASE** para comparar com a referência: menor que 1 significa que o modelo é melhor que a previsão ingênua (seção 5.8).
- **Evitar MAPE:** erros percentuais ficam infinitos com valor zero e exagerados com valores pequenos (seção 5.8). A venda tem 406 dias com zero.

**Classificação:** matriz de confusão, precisão, recall, F1, curva ROC e curva precision-recall, como pede o requisito Bônus. Com classe rara, a precisão média de um modelo aleatório é igual à proporção de positivos (documentação do scikit-learn, seção 3.4.4.9), então a curva precision-recall é mais informativa que a ROC.

**Validação:**

- Treino e teste separados por data, com os últimos meses como teste (Plano, seção 5).
- Para escolher variáveis ou o parâmetro do Ridge, usar validação em janelas crescentes: treina até um mês, testa no seguinte, e repete. É a lógica do `TimeSeriesSplit` do scikit-learn, em que cada treino contém o anterior. Como a base tem 100 linhas por dia, o corte deve ser feito por **data**, não por posição da linha.
- Padronização calculada só no treino (Plano, seção 5).

## 6. Da previsão à sugestão de compra

A previsão vira quantidade sugerida com o modelo de ponto de pedido e estoque de segurança:

- **Estoque de segurança** = z × σ × √L
- **Ponto de pedido** = demanda prevista durante L + estoque de segurança
- **Quantidade sugerida** = demanda prevista para o período coberto + estoque de segurança − estoque atual (nunca negativa)

Onde:

- **L** é o prazo de entrega do fornecedor, em dias;
- **σ** é o desvio padrão do erro do modelo no teste, por loja × produto. Usar o erro do modelo, e não a variação total da demanda, faz o estoque de segurança diminuir quando a previsão melhora;
- **z** vem do nível de serviço escolhido: 1,65 para 95% de chance de não faltar no ciclo.

**Limitação:** a base não tem prazo de entrega. Ele precisa ser um parâmetro informado pela Renata no sistema, com um valor padrão para os testes (ex.: 7 dias).

A fórmula assume erros aproximadamente normais. Isso deve ser conferido na análise de resíduos.

## 7. Recomendação para a Sprint 4

1. Calcular as quatro previsões de referência e registrar o erro de cada uma.
2. Treinar a regressão linear com as variáveis da Gold e comparar com a média móvel. Testar Ridge.
3. Treinar a regressão logística com `class_weight="balanced"` e escolher o limiar pela curva precision-recall. Testar a árvore rasa.
4. Rodar tudo com e sem o período de epidemia (Plano, seção 4).
5. Com o erro do modelo no teste, calcular o estoque de segurança e a quantidade sugerida.

Decisões que o grupo precisa tomar antes:

- alvo da regressão: `demanda` ou `unidades_vendidas`;
- regra da ruptura;
- prazo de entrega padrão e nível de serviço.

## Fontes

- Hyndman, R. J.; Athanasopoulos, G. *Forecasting: Principles and Practice*, 3ª ed. OTexts, 2021.
  - Seção 5.2, métodos simples: https://otexts.com/fpp3/simple-methods.html
  - Seção 5.8, avaliação de previsões: https://otexts.com/fpp3/accuracy.html
  - Capítulo 7, regressão para séries temporais: https://otexts.com/fpp3/regression.html
- scikit-learn, Linear Models (Ridge, LogisticRegression): https://scikit-learn.org/stable/modules/linear_model.html
- scikit-learn, Model evaluation (precisão, recall, F1, curva precision-recall): https://scikit-learn.org/stable/modules/model_evaluation.html
- scikit-learn, `TimeSeriesSplit`: https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html
- Wikipedia, Safety stock (fórmula de estoque de segurança e ponto de pedido): https://en.wikipedia.org/wiki/Safety_stock
