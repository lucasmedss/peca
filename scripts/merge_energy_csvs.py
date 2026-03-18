import argparse
import glob
import os
import pandas as pd

# Mudar parâmetros caso conforme necessidade para um novo dataset
DEFAULT_INPUT_GLOB = "dataset_bruto/**/energy_*.csv"
DEFAULT_OUTPUT_CSV = "dataset/energy_merged.csv"
DEFAULT_BUILDING_DICT_CSV = "dataset/building_dictionary.csv"
REQUIRED_COLUMNS = {"data", "hora"}
BUILDING_NAME_COLUMNS = ("predio", "building")
BUILDING_COLUMN = "building"
TIMESTAMP_COLUMN = "timestamp"
BUILDING_NAME_TO_ID = {
    "Escola Municipal Félix Araújo": "ESCOLA_MUNICIPAL",
    "UPA Dinamérica": "UPA_DIN",
    "SAMU": "SAMU",
    "Teatro Municipal": "TEATRO_MUNICIPAL",
}


def load_csvs(input_glob: str) -> tuple[pd.DataFrame, int]:
    # Lê todos os CSVs do padrão informado e valida colunas mínimas.
    paths = sorted(glob.glob(input_glob, recursive=True))
    if not paths:
        raise FileNotFoundError(f"Nenhum arquivo encontrado com o padrao: {input_glob}")

    frames = []
    for path in paths:
        df = pd.read_csv(path)
        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(f"Arquivo {path} sem colunas obrigatorias: {missing}")
        frames.append(df)

    merged = pd.concat(frames, ignore_index=True)
    return merged, len(paths)


def normalize_and_sort(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Constrói um timestamp único a partir de data + hora.
    df[TIMESTAMP_COLUMN] = pd.to_datetime(df["data"] + " " + df["hora"], errors="coerce")
    df = df.dropna(subset=[TIMESTAMP_COLUMN])

    dedup_keys = [TIMESTAMP_COLUMN]
    # Unifica possíveis colunas de nome do prédio e aplica mapeamento para IDs curtos.
    building_raw = pd.Series([pd.NA] * len(df), index=df.index, dtype="object")
    for col in BUILDING_NAME_COLUMNS:
        if col in df.columns:
            building_raw = building_raw.combine_first(df[col])
    if building_raw.notna().any():
        df[BUILDING_COLUMN] = building_raw.map(BUILDING_NAME_TO_ID).fillna(building_raw)
        dedup_keys.append(BUILDING_COLUMN)

    sort_keys = [TIMESTAMP_COLUMN]
    if BUILDING_COLUMN in df.columns:
        sort_keys.append(BUILDING_COLUMN)

    df = df.sort_values(sort_keys)
    # Remove duplicatas por timestamp (e prédio, quando existir), mantendo o registro mais recente.
    df = df.drop_duplicates(subset=dedup_keys, keep="last")

    redundant_columns = ["data", "hora", "__source_file", *BUILDING_NAME_COLUMNS]
    if BUILDING_COLUMN in redundant_columns:
        redundant_columns.remove(BUILDING_COLUMN)
    existing_redundant_columns = [col for col in redundant_columns if col in df.columns]
    if existing_redundant_columns:
        df = df.drop(columns=existing_redundant_columns)

    columns_to_drop = [col for col in df.columns if "demand" in col.lower() or "custo" in col.lower()]
    if columns_to_drop:
        df = df.drop(columns=columns_to_drop)

    # Padroniza formato final e coloca timestamp como primeira coluna.
    df[TIMESTAMP_COLUMN] = df[TIMESTAMP_COLUMN].dt.strftime("%Y-%m-%d %H:%M")
    columns = [TIMESTAMP_COLUMN] + [col for col in df.columns if col != TIMESTAMP_COLUMN]
    return df[columns]


def main() -> None:
    parser = argparse.ArgumentParser(description="Junta CSVs de energia em um unico arquivo.")
    parser.add_argument(
        "--input-glob",
        default=DEFAULT_INPUT_GLOB,
        help=f"Padrao de entrada (default: {DEFAULT_INPUT_GLOB})",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_CSV,
        help=f"Arquivo de saida (default: {DEFAULT_OUTPUT_CSV})",
    )
    parser.add_argument(
        "--building-dict-output",
        default=DEFAULT_BUILDING_DICT_CSV,
        help=f"Dicionario de predios (default: {DEFAULT_BUILDING_DICT_CSV})",
    )
    args = parser.parse_args()

    merged, file_count = load_csvs(args.input_glob)
    merged = normalize_and_sort(merged)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    merged.to_csv(args.output, index=False)
    building_dict = pd.DataFrame(
        [{"building": building_id, "nome_completo": name} for name, building_id in BUILDING_NAME_TO_ID.items()]
    )
    os.makedirs(os.path.dirname(args.building_dict_output), exist_ok=True)
    building_dict.to_csv(args.building_dict_output, index=False)

    print(f"Arquivos lidos: {file_count}")
    print(f"Linhas no CSV final: {len(merged)}")
    print(f"Arquivo gerado em: {args.output}")
    print(f"Dicionario de predios gerado em: {args.building_dict_output}")


if __name__ == "__main__":
    main()
