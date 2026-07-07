import json
import os
from pathlib import Path
import re
from copy import deepcopy

# Dealing with Markdown metadata
import frontmatter
import yaml
import shortuuid

from kblight import utilities


def cleanup_metadata(dirs: list = ["./yaml", "./rdf", "./json", "./csv"]):
    for d in dirs:
        d = Path(d)
        for file in d.iterdir():
            os.remove(file)


def extract_metadata(
    source_dir: str | Path = "./vault/entity",
    yaml_dir: str | Path = "./yaml",
    update_existing: bool = True,
    mapping_index: dict = None,
    id_length=12,
):
    """
    Extract metadata from Markdown file in dolder and store it in YAML files.
    """
    all_metadata = []

    # Ensure the source directory exists
    if not os.path.exists(source_dir):
        print(f"Error: The directory '{source_dir}' does not exist.")
        return

    # Create the output directory if it doesn't exist
    os.makedirs(yaml_dir, exist_ok=True)

    yaml_dir = Path(yaml_dir)
    source_dir = Path(source_dir)

    new_entities = 0
    updated_entities = 0

    if update_existing is False:
        print(
            f"Cleaning up all entities and all its serializations. Press Enter to continue."
        )
        input()
        cleanup_metadata()

        # Iterate through all files in the given directory
        for file in source_dir.iterdir():
            if file.name.endswith(".md"):
                # print(f"Current file: {file.name}")
                try:
                    # Load the file using python-frontmatter
                    page = frontmatter.load(file)

                    # Get the metadata dictionary
                    metadata = page.metadata

                    # Add unique ID and filename to metadata
                    metadata["base_name"] = file.stem
                    metadata["filename"] = file.name
                    metadata["id"] = utilities.truncated_uuid(id_length)
                    # add numerical_id for bisect search
                    metadata["n_id"] = shortuuid.decode(metadata["id"]).int

                    # Default class to Thing if not present
                    if "class" is not in metadata.keys():
                        metadata["class"] = ""

                    # Add content as field
                    metadata["markdown_content"] = page.content

                    # YAML export
                    yaml_filepath = yaml_dir / f"{metadata['id']}.yaml"
                    utilities.dict2yaml(metadata, yaml_filepath)

                    # print(f"Metadata and content extracted successfully")

                except Exception as e:
                    print(f"Error parsing {file.name}: {e}")
    else:
        # updating metadata if entity exists, otherwise create a new one

        print("Retrieving mapping index...")
        if mapping_index is None:
            mapping_index = generate_label_uuid_mapping(yaml_dir=yaml_dir)

        # update each entity from vault data
        for file in source_dir.iterdir():
            if file.name.endswith(".md"):
                # print(f"Current file: {file.name}")
                # search for filename
                if file.stem not in mapping_index.keys():
                    new_entities += 1
                    # create new entity
                    try:
                        # Load the file using python-frontmatter
                        page = frontmatter.load(file)

                        # Get the metadata dictionary
                        metadata = page.metadata

                        # Add unique ID and filename to metadata
                        metadata["base_name"] = file.stem
                        metadata["filename"] = file.name
                        metadata["id"] = utilities.truncated_uuid(id_length)
                        # add numerical_id for bisect search
                        metadata["n_id"] = shortuuid.decode(metadata["id"]).int

                        # Default class to Thing if not present
                        if "class" is not in metadata.keys():
                            metadata["class"] = ""

                        # Add content as field
                        metadata["markdown_content"] = page.content

                        # YAML export
                        yaml_filepath = yaml_dir / f"{metadata['id']}.yaml"
                        utilities.dict2yaml(metadata, yaml_filepath)

                        # print(f"Metadata and content extracted successfully")

                    except Exception as e:
                        print(f"Error parsing {file.name}: {e}")
                else:
                    updated_entities += 1
                    # updating existing one
                    entity_uuid = mapping_index[file.stem]

                    # Load the file using python-frontmatter
                    page = frontmatter.load(file)

                    # Get the metadata dictionary
                    metadata = page.metadata
                    metadata["base_name"] = file.stem
                    metadata["filename"] = file.name
                    # preserve UUID from URI
                    metadata["id"] = entity_uuid
                    metadata["n_id"] = shortuuid.decode(metadata["id"]).int

                    # Add content as field
                    metadata["markdown_content"] = page.content

                    # YAML export
                    yaml_filepath = yaml_dir / f"{metadata['id']}.yaml"
                    utilities.dict2yaml(metadata, yaml_filepath)

        print(f"Updated entities: {updated_entities} \n New entities: {new_entities}")


def substitute_wikilinks(
    base_url: str, yaml_dir: str | Path = "./yaml", mapping_index: dict = None
):
    """
    Retrieves Entity IDs/Labels and substitutes [[wikilinks]] with URIs
    strictly within the 'statements' and 'content' categories of nested YAML files.
    """
    import re
    from pathlib import Path

    WIKILINK_REGEX = re.compile(r"\[\[(.*?)\]\]")

    if not mapping_index:
        # Assuming generate_label_uri_mapping is available in your scope
        mapping_index = generate_label_uri_mapping(base_url=base_url, yaml_dir=yaml_dir)

    def replace_links_md_hyperlink(data, mapping_index=mapping_index):
        """
        Traverses factoid structures and substitutes [[wikilink]] with [label](URI).
        """
        # 1. Handle null values (common in 'description' or empty 'has_part')
        if data is None:
            return None

        # 2. FIX: Recursively call THIS function for dictionaries (qualifiers)
        if isinstance(data, dict):
            return {
                k: replace_links_md_hyperlink(v, mapping_index) for k, v in data.items()
            }

        # 3. FIX: Recursively call THIS function for lists (multiple statements)
        elif isinstance(data, list):
            return [replace_links_md_hyperlink(item, mapping_index) for item in data]

        # 4. Perform the regex substitution on strings
        elif isinstance(data, str):

            def _replacer(match):
                link_label = match.group(1)
                # Fetch URI from mapping_index (label -> UUID/Path)
                target_uri = mapping_index.get(link_label)

                if target_uri:
                    # Returns standard Markdown: [label](URI)
                    return f"[{link_label}]({target_uri})"
                else:
                    # If not found, leave as text: [[wikilink]]
                    return match.group(0)

            return WIKILINK_REGEX.sub(_replacer, data)

        return data

    def replace_links(data):
        # 1. Handle null values (common in your 'has_part' or 'description' fields)
        if data is None:
            return None

        # 2. Recurse into dictionaries (Factoid qualifiers like 'role' or 'holding_institution')
        if isinstance(data, dict):
            return {k: replace_links(v) for k, v in data.items()}

        # 3. Recurse into lists (supporting multiple instances of a statement)
        elif isinstance(data, list):
            return [replace_links(item) for item in data]

        # 4. Perform the regex substitution on strings
        elif isinstance(data, str):

            def _replacer(match):
                link_content = match.group(1)
                # If found in mapping_index, return URI; otherwise leave as [[link]]
                return mapping_index.get(link_content, match.group(0))

            return WIKILINK_REGEX.sub(_replacer, data)

        return data

    # 2. Re-open files, update records in-memory, and overwrite back to disk
    yaml_dir = Path(yaml_dir)
    for file in yaml_dir.iterdir():
        if file.name.endswith((".yaml", ".yml")):
            try:
                # Step A: Read the file content cleanly
                entity = utilities.yaml2dict(file)

                if not entity:
                    continue

                if entity["statements"]:
                    entity["statements"] = replace_links(entity["statements"])

                if entity["content"]:
                    entity["content"] = replace_links_md_hyperlink(entity["content"])

                # Step C: Write the new structure back down safely
                utilities.dict2yaml(entity, file)

                # print(f"Substituted links in: {file.name}")

            except Exception as e:
                print(f"Error processing modifications on {file.name}: {e}")


def generate_label_uuid_mapping(yaml_dir: str | Path = "./yaml") -> dict:
    """
    Returns a dictionary with mapping between entity label and UUID
    """
    # Build the mapping dictionary: { "François Desterbecq": "g8enQt9tCewQ" }
    mapping_index = {}

    yaml_dir = Path(yaml_dir)
    for file in yaml_dir.iterdir():
        if file.name.endswith((".yaml", ".yml")):
            try:
                entity = utilities.yaml2dict(file)

                if "id" and "filename" in entity["metadata"]:
                    # Strip .md extension from the original filename to get the core name
                    entity_name = entity["metadata"]["base_name"]
                    # Format absolute URI (stripping trailing slash safely to avoid double slashes)
                    mapping_index[entity_name] = entity["metadata"]["id"]
            except Exception as e:
                print(f"Error indexing {file.name}: {e}")

    print(f"Index built successfully. Mapped {len(mapping_index)} entities.")
    return mapping_index


def generate_label_uri_mapping(base_url: str, yaml_dir: str | Path = "./yaml") -> dict:
    """
    Returns a dictionary with mapping between entity label and UUID
    """
    # Build the mapping dictionary: { "François Desterbecq": "g8enQt9tCewQ" }
    mapping_index = {}

    yaml_dir = Path(yaml_dir)
    for file in yaml_dir.iterdir():
        if file.name.endswith((".yaml", ".yml")):
            try:
                entity = utilities.yaml2dict(file)

                if "id" and "filename" in entity["metadata"]:
                    # Strip .md extension from the original filename to get the core name
                    entity_name = entity["metadata"]["base_name"]
                    # Format absolute URI (stripping trailing slash safely to avoid double slashes)
                    mapping_index[entity_name] = f"{base_url}{entity['metadata']['id']}"
            except Exception as e:
                print(f"Error indexing {file.name}: {e}")

    print(f"Index built successfully. Mapped {len(mapping_index)} entities.")
    return mapping_index
