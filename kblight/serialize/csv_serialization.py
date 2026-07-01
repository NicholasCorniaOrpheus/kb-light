import pandas as pd
from kblight import utilities
from pathlib import Path


# NOT WORKING!!!!
def flatten_json_entities_to_csv(
    json_dir: str | Path = "./json", csv_dir: str | Path = "./csv"
):
    """
    Exports JSON entities files into flatten CSVs
    """
    json_dir = Path(json_dir)
    csv_dir = Path(csv_dir)
    for file in json_dir.glob("*.json"):
        df = pd.read_json(file)
        pd.to_csv(df, csv_dir / f"{file.stem}.csv", sep="|")
