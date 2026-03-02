import argparse
import os
import pandas as pd


DEFAULT_INPUT_CSV = "dataset/energy_merged.csv"
DEFAULT_OUTPUT_CSV = "dataset/energy_filled.csv"
TIMESTAMP_COLUMN = "timestamp"
BUILDING_COLUMN = "building"
VALUE_COLUMN = "consumption_kwh"
EXPECTED_FREQ = "15min"


def fill_missing_by_historical_mean(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    df = df.copy()
    # Normaliza tipos para evitar problemas em groupby/reindex.
    df[TIMESTAMP_COLUMN] = pd.to_datetime(df[TIMESTAMP_COLUMN], errors="coerce")
    df[VALUE_COLUMN] = pd.to_numeric(df[VALUE_COLUMN], errors="coerce")
    df = df.dropna(subset=[TIMESTAMP_COLUMN, BUILDING_COLUMN])
    df = df.sort_values([BUILDING_COLUMN, TIMESTAMP_COLUMN])

    before_counts = df.groupby(BUILDING_COLUMN).size().sort_index()

    filled_frames = []
    for building, group in df.groupby(BUILDING_COLUMN, sort=True):
        group = group.sort_values(TIMESTAMP_COLUMN).set_index(TIMESTAMP_COLUMN)
        # Gera grade temporal completa de 15 em 15 min para explicitar os buracos.
        full_index = pd.date_range(
            start=group.index.min(),
            end=group.index.max(),
            freq=EXPECTED_FREQ,
        )
        expanded = group.reindex(full_index)
        expanded[BUILDING_COLUMN] = building
        expanded.index.name = TIMESTAMP_COLUMN
        filled_frames.append(expanded.reset_index())

    expanded_df = pd.concat(filled_frames, ignore_index=True)
    # Features de contexto temporal para calcular médias históricas.
    expanded_df["weekday"] = expanded_df[TIMESTAMP_COLUMN].dt.dayofweek
    expanded_df["hhmm"] = expanded_df[TIMESTAMP_COLUMN].dt.strftime("%H:%M")

    # Estratégia de preenchimento:
    # 1) mesmo prédio + mesmo dia da semana + mesmo horário
    slot_means = expanded_df.groupby([BUILDING_COLUMN, "weekday", "hhmm"])[VALUE_COLUMN].transform("mean")
    expanded_df[VALUE_COLUMN] = expanded_df[VALUE_COLUMN].fillna(slot_means)

    expanded_df = expanded_df.drop(columns=["weekday", "hhmm"])
    expanded_df = expanded_df.sort_values([TIMESTAMP_COLUMN, BUILDING_COLUMN])
    # Mantém compatibilidade com o formato de saída usado no pipeline.
    expanded_df[TIMESTAMP_COLUMN] = expanded_df[TIMESTAMP_COLUMN].dt.strftime("%Y-%m-%d %H:%M")

    after_counts = expanded_df.groupby(BUILDING_COLUMN).size().sort_index()
    return expanded_df, before_counts, after_counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Preenche buracos do dataset de energia por media historica.")
    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT_CSV,
        help=f"CSV de entrada (default: {DEFAULT_INPUT_CSV})",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_CSV,
        help=f"CSV de saida (default: {DEFAULT_OUTPUT_CSV})",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    missing_columns = [col for col in (TIMESTAMP_COLUMN, BUILDING_COLUMN, VALUE_COLUMN) if col not in df.columns]
    if missing_columns:
        raise ValueError(f"CSV sem colunas obrigatorias: {missing_columns}")

    filled, before_counts, after_counts = fill_missing_by_historical_mean(df)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    filled.to_csv(args.output, index=False)

    print(f"Linhas no CSV de entrada: {len(df)}")
    print(f"Linhas no CSV final: {len(filled)}")
    print("Registros por predio (antes de limpar buracos):")
    for building, count in before_counts.items():
        print(f"- {building}: {count}")
    print("Registros por predio (depois de limpar buracos):")
    for building, count in after_counts.items():
        print(f"- {building}: {count}")
    print(f"Arquivo gerado em: {args.output}")


if __name__ == "__main__":
    main()
