import pandas as pd
from kblight import utilities
from pathlib import Path


def flatten_json_entities_to_csv(
    json_dir: str | Path = "./json", csv_dir: str | Path = "./csv"
):
    """
    Exports JSON entities files into flatten CSVs
    """
    json_dir = Path(json_dir)
    csv_dir = Path(csv_dir)
    csv_dir.mkdir(parents=True, exist_ok=True)  # Create output dir
    for file in json_dir.glob("*.json"):
        try:
            data = utilities.json2dict(file)

            # Flatten nested structures
            flattened_rows = []

            # Extract metadata (top level)
            meta = data.get("metadata", {})

            # Extract statements and flatten factoid structures
            statements = data.get("statements", {})

            for prop_name, prop_values in statements.items():
                # Ensure it's a list
                values_list = (
                    prop_values if isinstance(prop_values, list) else [prop_values]
                )

                for idx, val in enumerate(values_list):
                    row = {**meta, "property": prop_name}

                    if isinstance(val, dict):
                        # Flatten the factoid (e.g., {"value": "Q123", "role": "author"})
                        for k, v in val.items():
                            row[f"{prop_name}_{k}"] = v
                    else:
                        row[f"{prop_name}_value"] = val

                    flattened_rows.append(row)

            # Convert to DataFrame and save
            df = pd.DataFrame(flattened_rows)
            csv_path = csv_dir / f"{file.stem}.csv"
            df.to_csv(csv_path, sep=",", index=False)
            print(f"✓ Exported {file.name} → {csv_path}")

        except Exception as e:
            print(f"✗ Error processing {file.name}: {e}")
