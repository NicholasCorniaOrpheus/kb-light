from kblight import utilities
from pathlib import Path


def yaml_metadata_to_json(
    yaml_dir: str | Path = "./yaml", output_json_dir: str | Path = "./json"
):
    """
    Converts YAML metadata to JSON
    """
    output_json_dir = Path(output_json_dir)
    yaml_dir = Path(yaml_dir)
    for file in yaml_dir.glob("*.y*ml"):
        entity = utilities.yaml2dict(file)
        # JSON export
        json_filepath = output_json_dir / f"{file.stem}.json"
        utilities.dict2json(
            {"metadata": entity["metadata"], "statements": entity["statements"]},
            json_filepath,
        )

    return None
