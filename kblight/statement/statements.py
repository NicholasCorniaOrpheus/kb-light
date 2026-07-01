from pathlib import Path
from kblight import utilities
import yaml


def organize_statements(yaml_dir: str | Path, properties_mapping_path: str | Path):
    """
    Turns a YAML metadata file in a more structured file, following the category field in properties_mapping
    See the following example:

    {
                    "metadata": {
                                                    "id":
                                                    "n_id":
                                                    "label":
                                                    "aliases": ...
                                    },

                    "statements": {
                                                    "instance_of": ...
                                                    "subclass_of": ...
                                                    "identifier": ....
                                    }

                    "content": {
                                    "markdown_content": ...
                    }

                    "assets": {
                                                    "local_file_path": "..."
                                                    "image": "..."
                                    }


    }
    """

    # Load properties mapping to retrieve categories
    properties_mapping = utilities.csv2dict(properties_mapping_path)

    yaml_dir = Path(yaml_dir)
    for f in yaml_dir.iterdir():
        # get json file as dict
        # print(f"Current entity: {f.name}")
        entity_dict = utilities.yaml2dict(f)

        new_entity_dict = {
            "metadata": {},
            "statements": {},
            "assets": {},
            "content": {},
        }

        for key in entity_dict.keys():
            property_query = list(
                filter(lambda x: x["yaml_property"] == key, properties_mapping)
            )
            if len(property_query) == 1:
                category = property_query[0]["category"]

                new_entity_dict[category][key] = entity_dict[key]

            else:
                pass

        # save new version on same file
        utilities.dict2yaml(new_entity_dict, f)
        # print(f"Saving changes...")


def add_labels_to_statements(
    base_url: str, yaml_dir: str | Path = "./yaml", mapping_index: dict = None
):
    """
    Add 'label' keys to entity statements for kb-light.
    """
    if not mapping_index:
        mapping_index = generate_label_uri_mapping(base_url=base_url, yaml_dir=yaml_dir)

    # create a reverse_index
    reverse_index = {v: k for k, v in mapping_index.items()}

    def process_node(data):
        # 1. Handle Lists (like 'has_version' or 'place_of_publication')
        if isinstance(data, list):
            return [process_node(item) for item in data]

        # 2. Handle Dictionaries (Factoid qualifiers/statements)
        if isinstance(data, dict):
            # If the dict has a 'value' that is an internal URI, add the label
            if (
                "value" in data
                and isinstance(data["value"], str)
                and base_url in data["value"]
            ):
                uri = data["value"]
                if uri in reverse_index:
                    data["label"] = reverse_index[uri]

            # Recurse into all other keys (to catch nested lists/dicts)
            for k, v in data.items():
                if k != "value":  # Avoid recursing into the URI string itself
                    data[k] = process_node(v)
            return data

        # 3. Handle bare Strings (Internal URIs used as simple values)
        if isinstance(data, str) and base_url in data:
            if data in reverse_index:
                # Convert bare URI string to a dict with its label
                return {"value": data, "label": reverse_index[data]}

        return data

    yaml_dir = Path(yaml_dir)
    for file in yaml_dir.glob("*.y*ml"):
        try:
            entity = utilities.yaml2dict(file)
            if not entity or "statements" not in entity:
                continue

            if entity["statements"]:
                # Step A: Resolve labels and convert strings to dicts recursively
                resolved = process_node(entity["statements"])

                # Step B: Enforce the list structure for ALL top-level properties
                for key, value in resolved.items():
                    # If it's a single dict (object), wrap it in a list
                    if value is not None and not isinstance(value, list):
                        resolved[key] = [value]

                entity["statements"] = resolved

            utilities.dict2yaml(entity, file)

        except Exception as e:
            print(f"❌ Error processing {file.name}: {e}")
