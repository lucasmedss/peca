import requests
import pandas as pd
from datetime import datetime
import calendar
import time
import pytz
from pathlib import Path

# Solicitar ao mantenedor o token de acesso e os possíveis IDs de sensores para o prédio. Substituir os valores abaixo:
TOKEN = "token_XXXX"
SENSOR_ID = "sensor_ID"
# Definir o período de extração (exemplo: janeiro a dezembro de 2025)
START_YEAR = 2025
START_MONTH = 1
END_YEAR = 2025
END_MONTH = 12

TZ_BRASIL = pytz.timezone("America/Sao_Paulo")
BASE_URL = f"https://painel.liteme.com.br/service/rest/sensor/{SENSOR_ID}/balance"

HEADERS = {
    "Access-token": TOKEN,
    "User-Agent": "Mozilla/5.0 (Script dataset extractor) python-requests/2.31"
}

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = PROJECT_ROOT / "dataset_extraido"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Definir nome do prédio para a tabela
PREDIO_NOME = "Prédio Exemplo"

def iterar_meses(inicio_ano, inicio_mes, fim_ano, fim_mes):
    if (inicio_ano, inicio_mes) > (fim_ano, fim_mes):
        raise ValueError("Periodo invalido: inicio maior que fim.")
    ano, mes = inicio_ano, inicio_mes
    while (ano, mes) <= (fim_ano, fim_mes):
        yield ano, mes
        mes += 1
        if mes > 12:
            mes = 1
            ano += 1

def obter_timestamps_mes(ano, mes):
    dt_inicio = datetime(ano, mes, 1, 0, 0, 0)
    dt_inicio_br = TZ_BRASIL.localize(dt_inicio)

    _, ultimo_dia = calendar.monthrange(ano, mes)
    dt_fim = datetime(ano, mes, ultimo_dia, 23, 59, 59)
    dt_fim_br = TZ_BRASIL.localize(dt_fim)

    start_ms = int(dt_inicio_br.timestamp() * 1000)
    end_ms = int(dt_fim_br.timestamp() * 1000)

    return start_ms, end_ms


print(
    f"--- Iniciando extração de dados de "
    f"{START_YEAR}-{START_MONTH:02d} até {END_YEAR}-{END_MONTH:02d} ---"
)

for ano, mes in iterar_meses(START_YEAR, START_MONTH, END_YEAR, END_MONTH):

    nome_arquivo = OUTPUT_DIR / f"energy_{ano}_{mes:02d}.csv"

    if nome_arquivo.exists():
        print(f"[{ano}-{mes:02d}] Já existe. Pulando...")
        continue

    start_ts, end_ts = obter_timestamps_mes(ano, mes)

    params = {
        "aggregationType": "FIFTEEN_MINUTES",
        "sensorBalanceType": "SEPARATE",
        "reallocate": "true",
        "start": start_ts,
        "end": end_ts
    }

    print(f"[{ano}-{mes:02d}] Baixando dados...")

    try:
        response = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=30)

        if response.status_code == 200:

            dados = response.json()
            lista_registros = dados.get('details')

            if not lista_registros:
                print("   -> Aviso: 'details' vazio.")
                continue

            df = pd.json_normalize(lista_registros)

            # --------------------------------------
            # CONVERTE TIMESTAMP
            # --------------------------------------
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
            df['timestamp'] = df['timestamp'].dt.tz_convert(TZ_BRASIL)
            df['timestamp'] = df['timestamp'].dt.tz_localize(None)

            # --------------------------------------
            # CRIA DATA E HORA
            # --------------------------------------
            df['data'] = df['timestamp'].dt.strftime("%Y-%m-%d")
            df['hora'] = df['timestamp'].dt.strftime("%H:%M")

            # --------------------------------------
            # EXTRAI COLUNAS IMPORTANTES
            # --------------------------------------
            df['consumption_kwh'] = df.get('consumption.consumption', None)
            df['building'] = PREDIO_NOME

            # --------------------------------------
            # DATASET FINAL
            # --------------------------------------
            df_final = df[[
                'data',
                'hora',
                'building',
                'consumption_kwh',
            ]]

            df_final.to_csv(nome_arquivo, index=False)

            print(f"   -> Sucesso! {len(df_final)} registros salvos.")

        else:
            print(f"Erro {response.status_code}: {response.text}")

    except Exception as e:
        print(f"Erro crítico: {e}")

    time.sleep(1)

print("\nProcesso finalizado!")
