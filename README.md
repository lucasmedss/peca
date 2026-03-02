# Public Energy Consumption Analysis

Projeto para preparação, exploração e previsão de consumo de energia em edifícios públicos, com dados em frequência de 15 minutos.

## Estrutura do Repositório

- `cg_public_energy_consumption.csv`: dataset público consolidado usado nos notebooks.
- `01_exploracao_consumo.ipynb`: análise exploratória (EDA) do consumo.
- `02_previsao_consumo.ipynb`: pipeline de previsão mensal com SMA por slot.
- `scripts/forecast_metrics.ipynb`: notebook de avaliação para cálculo e comparação de métricas de previsão.

## Dataset

O arquivo `cg_public_energy_consumption.csv` representa a base consolidada de consumo energético por edifício público ao longo do tempo.

Detalhes principais:

- granularidade temporal de 15 minutos;
- uma linha por timestamp e por edifício;
- coluna-alvo de consumo em `consumption_kwh`;
- identificação de edifício em `building`.

Observações de uso:

- o notebook `01_exploracao_consumo.ipynb` usa essa base para análise descritiva;
- o notebook `02_previsao_consumo.ipynb` usa essa base para montar a série histórica e gerar previsões.

## Notebooks

### `01_exploracao_consumo.ipynb`

Foco em análise exploratória:

- distribuição de consumo por prédio;
- padrões temporais (dia, mês, ano, dia da semana);
- visualizações para comportamento sazonal.

Fluxo do notebook:

1. Carrega a base consolidada.
2. Converte e organiza as colunas temporais para análise.
3. Gera agregações por período (diário, mensal, anual e por dia da semana).
4. Plota gráficos comparativos entre edifícios e períodos.

Saída esperada:

- entendimento de padrões de consumo;
- identificação de sazonalidade e variação entre prédios;
- base analítica para decidir parâmetros de previsão.

### `02_previsao_consumo.ipynb`

Foco em previsão:

- previsão mensal com SMA por `slot_15m`;
- comparação entre consumo real e previsto;
- análise agregada por mês no ano alvo.

Fluxo do notebook:

1. Seleciona edifício e período de análise.
2. Monta histórico de treino por slot de 15 minutos.
3. Aplica SMA por slot para gerar previsão do mês alvo.
4. Agrega previsões para total mensal.
5. Compara previsto vs real e resume resultados em tabelas/gráficos.

Saída esperada:

- série prevista por intervalo de 15 minutos;
- total previsto mensal;
- comparação anual de desempenho da estratégia SMA.

### `scripts/forecast_metrics.ipynb`

Foco em avaliação:

- cálculo de métricas de erro (ex.: RMSE, sMAPE);
- comparação de desempenho por edifício no período selecionado.

## Observações

- Os scripts preservam o foco em séries temporais por prédio.
- O preenchimento de lacunas usa média histórica para o mesmo dia da semana e horário.
