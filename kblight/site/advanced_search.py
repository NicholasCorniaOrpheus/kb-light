from kblight import utilities

from pathlib import Path
import dpath
import json
import math
import pandas as pd
from json import JSONEncoder
import datetime


def clean_nan(obj):
    """
    Recursively replaces NaN values with None in dictionaries and lists.
    """
    if isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan(v) for v in obj]
    elif isinstance(obj, float) and math.isnan(obj):
        return None  # Converts to 'null' in the resulting JSON
    return obj


def generate_advanced_search_index(
    yaml_dir: str | Path = "./yaml",
    advanced_search_index_mapping_filepath: str
    | Path = "./mappings/advanced_search_index_mapping.json",
    advanced_search_index_output_path: str | Path = "./advanced_search_index.json",
):
    """
    Generate a search index for the Explore advanced search, filtering and flattening statements
    """

    # importing mapping
    advanced_search_mapping = utilities.json2dict(
        advanced_search_index_mapping_filepath
    )

    advanced_search_index = []

    yaml_dir = Path(yaml_dir)
    for file in yaml_dir.glob("*.y*ml"):
        entity = utilities.yaml2dict(file)
        entity_index = {"location": f"/entity/{file.stem}", "properties": {}}
        # search for each property in the mapping
        for filter_term in advanced_search_mapping.keys():
            for prop_path in advanced_search_mapping[filter_term]:
                # using dpath to perform xpath-like search in dictionary
                try:
                    values = dpath.get(entity, prop_path)
                    if filter_term in entity_index["properties"].keys():
                        if isinstance(values, list):
                            for sub_v in values:
                                entity_index["properties"][filter_term].append(sub_v)
                        else:
                            entity_index["properties"][filter_term].append(values)
                    else:
                        if isinstance(values, list):
                            entity_index["properties"][filter_term] = values
                        else:
                            entity_index["properties"][filter_term] = [values]
                except KeyError:
                    pass

        # getting rid of duplicates in labels
        try:
            entity_index["properties"]["label"] = list(
                set(entity_index["properties"]["label"])
            )
        except KeyError:
            pass

        # append to search index
        advanced_search_index.append(entity_index)

    # save indices to JSON converting datatime into strings
    # subclass JSONEncoder
    class DateTimeEncoder(JSONEncoder):
        # Override the default method
        def default(self, obj):
            if isinstance(obj, (datetime.date, datetime.datetime)):
                return obj.isoformat()

    with open(advanced_search_index_output_path, "w") as f:
        json.dump(
            clean_nan(advanced_search_index),
            f,
            indent=4,
            ensure_ascii=False,
            cls=DateTimeEncoder,
        )
