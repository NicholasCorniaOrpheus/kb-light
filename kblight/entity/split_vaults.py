from pathlib import Path
from kblight import utilities
import frontmatter
import shutil
import re


def split_vault_based_on_tags(
    vault_dir: str | Path, output_dir: str | Path, tags: list
):
    """
    This function extract a sub-vault starting with notes with tags belonging to the tags parameter,
    and then recursively extract related notes via backlinks and store them in a unique output directory.
    """
    vault_dir = Path(vault_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create a global map of filename -> absolute path for link resolution
    # Obsidian links often omit paths, so we need this to find the actual files.
    vault_map = {f.stem: f for f in vault_dir.glob("**/*.md")}
    sub_vault_paths = set()
    queue = []

    # 2. Initial Seed: Find notes by tag
    print(f"--- Initializing seed with tags: {', '.join(tags)} ---")
    for file in vault_dir.glob("**/*.md"):
        try:
            # Load the file using python-frontmatter
            page = frontmatter.load(file)
            note_tags = page.metadata.get("tags", [])
            if isinstance(note_tags, str):
                note_tags = [note_tags]
            if any(tag in note_tags for tag in tags):
                if file not in sub_vault_paths:
                    sub_vault_paths.add(file)
                    queue.append(file)
        except Exception as e:
            print(f"Error reading {file.name}: {e}")

    # 3. Recursive Discovery via Wikilinks
    # Regex handles [[Note Name]], [[Note Name|Alias]], and [[Path/To/Note]]
    WIKILINK_REGEX = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")

    print(f"--- Crawling links for {len(queue)} initial notes ---")
    while queue:
        current_file = queue.pop(0)
        try:
            page = frontmatter.load(current_file)
            metadata = page.metadata
            content = page.content

            # Find all wikilinks in the body
            links = WIKILINK_REGEX.findall(content)

            # find all wikilinks in the properties
            def extract_links_from_metadata(data):
                """
                Recursively crawls metadata (strings, lists, dicts) to find wikilinks.
                """
                found_links = []

                if isinstance(data, str):
                    # Perform regex match on simple strings
                    found_links.extend(WIKILINK_REGEX.findall(data))

                elif isinstance(data, list):
                    # Recurse into lists (supporting multiple statements)
                    for item in data:
                        found_links.extend(extract_links_from_metadata(item))

                elif isinstance(data, dict):
                    # Recurse into dictionaries (Factoid qualifiers/values) [2]
                    for value in data.values():
                        found_links.extend(extract_links_from_metadata(value))

                return found_links

            metadata_links = extract_links_from_metadata(page.metadata)

            links.extend(metadata_links)

            for link in links:
                # Resolve the link to a filename (strip path and extension if present)
                link_stem = Path(link).stem

                target_path = vault_map.get(link_stem)
                if target_path and target_path.exists():
                    if target_path not in sub_vault_paths:
                        sub_vault_paths.add(target_path)
                        queue.append(target_path)
        except Exception as e:
            print(f"Error processing links in {current_file.name}: {e}")

    # 4. Save/Copy discovered notes to the unique output directory
    print(f"--- Copying {len(sub_vault_paths)} notes to {output_dir} ---")
    for note_path in sub_vault_paths:
        # We maintain a flat structure in the output for simplicity,
        dest = output_dir / note_path.name
        shutil.copy2(note_path, dest)

    print("Sub-vault extraction complete.")
