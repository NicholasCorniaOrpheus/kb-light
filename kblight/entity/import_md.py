import json
import os
import re

# Dealing with Markdown metadata
import frontmatter
import yaml

from kblight import utilities


def extract_metadata(
    source_dir: str = "./data/vault/entity",
    output_yaml_path: str = "./data/yaml",
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
    os.makedirs(output_yaml_path, exist_ok=True)

    # Iterate through all files in the given directory
    for file in os.scandir(source_dir):
        if file.name.endswith(".md"):
            print(f"Current file: {file.name}")
            try:
                # Load the file using python-frontmatter
                page = frontmatter.load(file.path)

                # Get the metadata dictionary
                metadata = page.metadata

                # Add unique ID and filename to metadata
                metadata["filename"] = file.name
                metadata["id"] = utilities.truncated_uuid(id_length)

                # Add content as field
                metadata["markdown_content"] = page.content

                # YAML export
                yaml_filepath = os.path.join(output_yaml_path, f"{metadata['id']}.yaml")
                with open(yaml_filepath, "w", encoding="utf-8") as yaml_file:
                    yaml.dump(metadata, yaml_file, allow_unicode=True, sort_keys=False)

                print(f"Metadata and content extracted successfully")

            except Exception as e:
                print(f"Error parsing {file.name}: {e}")


def substitute_wikilinks(base_url: str, yaml_dir: str = "./data/yaml"):
    """Retrieves Entities IDs and substitute them with base_url/ID in YAML files."""

    WIKILINK_REGEX = re.compile(r"\[\[(.*?)\]\]")

    # 1. Build the mapping dictionary: { "François Desterbecq": "https://.../g8enQt9tCewQ" }
    mapping_index = {}

    for file in os.scandir(yaml_dir):
        if file.name.endswith((".yaml", ".yml")):
            try:
                with open(file.path, "r", encoding="utf-8") as f:
                    entity = yaml.safe_load(f)

                if entity and "filename" in entity and "id" in entity:
                    # Strip .md extension from the original filename to get the core name
                    entity_name = os.path.splitext(entity["filename"])[0]
                    # Format absolute URI (stripping trailing slash safely to avoid double slashes)
                    clean_base = base_url.rstrip("/")
                    mapping_index[entity_name] = f"{clean_base}/{entity['id']}"
            except Exception as e:
                print(f"Error indexing {file.name}: {e}")

    print(f"Index built successfully. Mapped {len(mapping_index)} entities.")

    # Inner helper function to recursively crawl your YAML structures
    def replace_links(data):
        if isinstance(data, dict):
            return {k: replace_links(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [replace_links(item) for item in data]
        elif isinstance(data, str):
            # Callback for re.sub to handle regex matches
            def _replacer(match):
                link_content = match.group(1)
                # If the name exists in our map, replace it; otherwise leave it as-is
                return mapping_index.get(link_content, match.group(0))

            return WIKILINK_REGEX.sub(_replacer, data)
        return data

    # 2. Re-open files, update records in-memory, and overwrite back to disk
    for file in os.scandir(yaml_dir):
        if file.name.endswith((".yaml", ".yml")):
            try:
                # Step A: Read the file content cleanly
                with open(file.path, "r", encoding="utf-8") as f:
                    entity_data = yaml.safe_load(f)

                if not entity_data:
                    continue

                # Step B: Run the recursive substitution on the loaded structure
                updated_data = replace_links(entity_data)

                # Step C: Write the new structure back down safely
                with open(file.path, "w", encoding="utf-8") as f:
                    yaml.dump(updated_data, f, allow_unicode=True, sort_keys=False)

                print(f"Substituted links in: {file.name}")

            except Exception as e:
                print(f"Error processing modifications on {file.name}: {e}")
