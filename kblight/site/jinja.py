import yaml
import json
from jinja2 import Template, Environment, FileSystemLoader
from pathlib import Path
from kblight import utilities


def generate_mkdocs_pages(
    GITHUB_RAW_BASE: str, YAML_PATH: Path, OUTPUT_PATH: Path, TEMPLATE_FILE: str
):
    # 1. Setup Jinja2 Environment
    print(f"Importing template from {TEMPLATE_FILE}...")
    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template(TEMPLATE_FILE)

    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    VAULT_ROOT = YAML_PATH.parent  # Assuming vault root is parent of yaml dir

    # 2. Process each YAML entity file
    for yaml_file in YAML_PATH.glob("**/*.yaml"):
        # print(f"Current file {yaml_file.name}")
        data = utilities.yaml2dict(yaml_file)

        if not data:
            continue

        # FIX: Defensive check for 'assets' and 'local_asset_path'
        # Ensures we don't pass 'None' to Path() or the / operator
        assets_data = data.get("assets")
        if assets_data and assets_data.get("local_asset_path"):
            try:
                # Clean the relative path string
                rel_path_str = str(assets_data["local_asset_path"]).lstrip("./")
                asset_dir = VAULT_ROOT / rel_path_str

                # Only scan if the directory actually exists
                if asset_dir.exists() and asset_dir.is_dir():
                    # Identify .tei files for the side-by-side viewer
                    tei_list = [p.name for p in asset_dir.glob("*.tei")]
                    data["assets"]["tei_files"] = tei_list
                else:
                    data["assets"]["tei_files"] = []
            except Exception as e:
                print(f"⚠️ Warning: Could not process assets for {yaml_file.name}: {e}")
                data["assets"]["tei_files"] = []
        else:
            # Safely initialize assets if null to prevent template errors
            if data.get("assets") is None:
                data["assets"] = {}
            data["assets"]["tei_files"] = []

        # 3. Render Template
        output_md = template.render(data)

        # 4. Save file using the persistent ID [1, 2]
        entity_id = data.get("metadata", {}).get("id")
        if entity_id:
            file_name = f"{entity_id}.md"
            with open(OUTPUT_PATH / file_name, "w", encoding="utf-8") as f:
                f.write(output_md)
        else:
            print(f"❌ Error: Missing ID in {yaml_file.name}")

    print(f"✅ Generated pages in {OUTPUT_PATH}")
