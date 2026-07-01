from pathlib import Path
from kblight import utilities
import frontmatter
import dpath

"""
These scripts convert the properties of (Obsidian) Markdown notes
into new .md files with a structure defined by a JSON mapping.

For example property author --> contributor: {value: , role: [[author]]}
"""


def convert_md_properties(
    vault_dir: str | Path = "./vault",
    output_dir: str | Path = "./converted_vault",
    properties_mapping_filepath: str | Path = "./mappings/convert_properties.json",
):
    vault_dir = Path(vault_dir)
    for note in vault_dir.glob("*.md"):
        pass
