from pathlib import Path

from kblight import utilities
import math


def extract_assets_from_local_paths(
    yaml_dir: str | Path,
    vault_path: str | Path,
    vault_base_url: str,
    IIIF_manifest="has_version/IIIF_manifest",
    assets_path="local_asset_path",
):
    """
    Crawls local directories and appends filenames (grouped by extension)
    and IIIF manifest URLs to the entity's assets dictionary.
    """
    yaml_dir = Path(yaml_dir)
    vault_path = Path(vault_path)

    for f in yaml_dir.glob("*.y*ml"):
        entity = utilities.yaml2dict(f)
        if not entity:
            continue

        # FIX 1: Defensive initialization of categories
        # Prevents TypeError if 'assets' or 'statements' are 'null' in YAML
        if entity.get("statements") is None:
            entity["statements"] = {}
        if entity.get("assets") is None:
            entity["assets"] = {}

        # 1. Extract IIIF_manifest from nested statements
        IIIF_keys = IIIF_manifest.split("/")
        current_val = entity["statements"]

        try:
            for key in IIIF_keys:
                # FIX 2: Handle the 'has_version' LIST structure
                # In your Factoid model, has_version is a list of dicts [Conversation History]
                if isinstance(current_val, list) and len(current_val) > 0:
                    current_val = current_val  # Take first version's manifest

                if isinstance(current_val, dict):
                    current_val = current_val.get(key)
                else:
                    current_val = None
                    break

            # Store found manifest or leave as None
            entity["assets"]["IIIF_manifest"] = current_val
        except Exception:
            entity["assets"]["IIIF_manifest"] = None

        # 2. Collect local files from vault based on extension
        local_rel_path = entity["assets"].get(assets_path)

        if local_rel_path:
            try:
                # Clean path and join with vault root
                clean_rel_path = str(local_rel_path).lstrip("./")
                assets_dir = vault_path / clean_rel_path

                if assets_dir.exists() and assets_dir.is_dir():
                    # Clear existing extension lists to avoid duplicates on re-runs
                    # but keep the 'local_asset_path' and 'IIIF_manifest'
                    keys_to_keep = [assets_path, "IIIF_manifest", "image"]
                    entity["assets"] = {
                        k: v for k, v in entity["assets"].items() if k in keys_to_keep
                    }

                    for entry in sorted(assets_dir.iterdir(), key=lambda x: x.name):
                        if entry.is_file():
                            # Normalize extension (e.g., 'jpg', 'xml', 'tei')
                            ext = entry.suffix.lstrip(".").lower()

                            if ext not in entity["assets"]:
                                entity["assets"][ext] = []

                            entity["assets"][ext].append(entry.name)
            except Exception as e:
                print(f"❌ Error processing assets for {f.name}: {e}")

        # TRANSFORM LOCAL PATHS TO URLS
        image_data = entity["assets"].get("image")

        # CHECK: Ensure image_data is not NaN before processing
        is_nan = isinstance(image_data, float) and math.isnan(image_data)

        if image_data and not is_nan and isinstance(image_data, str):
            if not image_data.startswith("http"):
                img_path = image_data.lstrip("./")
                full_url = f"{vault_base_url}/{img_path}".replace("//", "/")
                entity["assets"]["image"] = [{"value": full_url}]
        else:
            # If it is NaN or missing, set it to an empty list to avoid D3 errors
            entity["assets"]["image"] = ""

        # Save the updated nested structure back to YAML
        utilities.dict2yaml(entity, f)


def add_default_image(yaml_dir: str | Path, class_mapping_path: str | Path):
    """
    If image field is empty, add default image base on class.
    """
    yaml_dir = Path(yaml_dir)

    class_mapping = utilities.csv2dict(class_mapping_path)

    for f in yaml_dir.glob("*.y*ml"):
        entity = utilities.yaml2dict(f)
        if not entity:
            continue

        if entity["assets"].get("image", None) in [None, ""]:
            # assign default image from class
            # get entity class
            entity_class = entity["metadata"].get("class")

            class_query = list(
                filter(lambda x: x["yaml_class"] == entity_class, class_mapping)
            )

            if len(class_query) > 0:
                entity["assets"]["image"] = class_query[0]["default_image"]

                # saving back
                utilities.dict2yaml(entity, f)


def add_local_graph_to_assets(
    graph_base_url: str,
    yaml_dir: str | Path = "./yaml",
    graph_dir: str | Path = "./graph",
):
    """
    Embeds graph representation with backlinks in assets.graph for D3.js visualization.
    It assumes that the individual graph JSONs have been generate via [kblight.site.d3_graph.generate_backlinks_graphs][] method.
    """

    yaml_dir = Path(yaml_dir)
    graph_dir = Path(graph_dir)

    # generate list of graph_dir objects
    graph_dict = {
        file.stem: f"{graph_base_url}{str(file)}" for file in graph_dir.glob("*.json")
    }

    for file in yaml_dir.glob("*.y*ml"):
        try:
            entity = utilities.yaml2dict(file)
            # ingesting graph path to assets
            entity["assets"]["graph"] = graph_dict.get(entity["metadata"]["id"], "")

            # apply changes
            utilities.dict2yaml(entity, file)

        except Exception as e:
            print(f"❌ Error processing {file.name}: {e}")
