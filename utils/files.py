import pandas as pd


def read_csv_smart(file_obj) -> pd.DataFrame:
    # sep=None + engine='python' faz o pandas tentar adivinhar se o separador é , ou ;
    return pd.read_csv(file_obj, sep=None, engine="python")


def require_column(df: pd.DataFrame, column_name: str) -> None:
    # Verificação rápida pra quebrar logo com uma mensagem clara se algo estiver errado

    if column_name not in df.columns:
        raise ValueError(f"Missing required column: '{column_name}'")
