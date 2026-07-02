import re
from pathlib import Path
import json

from kblight import utilities


def generate_global_network(
    base_url: str, yaml_dir: str | Path = "./yaml", graph_path="./graph.json"
):
    """
    Generates a single D3.js compatible graph for ALL entities in the vault.
    Records label, image, and class for nodes, and property names for links.
    """

    yaml_dir = Path(yaml_dir)
    # Ensure base_url matches the specific format in your YAML files
    base_url = base_url

    nodes_registry = {}  # uri -> {node_data}
    links = []  # list of {source, target, property}

    # Pre-compile regex for efficiency
    entity_uri_pattern = re.compile(re.escape(base_url) + r"\w+")

    # 1. Global Crawl to define all Nodes and Edges
    for file in yaml_dir.glob("*.y*ml"):
        data = utilities.yaml2dict(file)
        if not data:
            continue

        meta = data.get("metadata", {})
        # Note: Constructing URI based on your provided base_url
        entity_id = meta.get("id")
        entity_uri = f"{base_url}{entity_id}"

        # Register the node with its class for color-coding [6]
        if meta.get("label") is None:
            label = meta.get("base_name")
        else:
            label = meta.get("label")
        nodes_registry[entity_uri] = {
            "id": entity_uri,
            "label": label,
            "class": meta.get("class", ""),  # For D3 color scales
            "image": data.get("assets", {}).get("image"),
        }

        # Recursive helper to find internal links within the Factoid structure [2]
        def find_links(content, current_prop):
            if isinstance(content, list):
                for item in content:
                    find_links(item, current_prop)
            elif isinstance(content, dict):
                # Check for augmented 'value' keys
                val = content.get("value")
                if isinstance(val, str) and base_url in val:
                    links.append(
                        {"source": entity_uri, "target": val, "property": current_prop}
                    )
                # Recurse into qualifiers/references
                for k, v in content.items():
                    if k != "value":
                        find_links(v, current_prop)
            elif isinstance(content, str) and base_url in content:
                # Handle bare URI strings
                links.append(
                    {"source": entity_uri, "target": content, "property": current_prop}
                )

        # Process all statement keys
        statements = data.get("statements", {})
        if statements:
            for prop, val in statements.items():
                find_links(val, prop)

        # Retrieve entities from Markdown content
        markdown_content = data.get("content", {}).get("markdown_content", "")
        if markdown_content:
            # Find all entity URIs in the markdown content
            found_uris = entity_uri_pattern.findall(markdown_content)
            for found_uri in found_uris:
                links.append(
                    {
                        "source": entity_uri,
                        "target": found_uri,
                        "property": "related_to",
                    }
                )

    # 2. Cleanup: Ensure all link targets exist as nodes
    # If a target URI was mentioned but the file is missing, create a placeholder node
    all_sources_targets = set(
        [l["source"] for l in links] + [l["target"] for l in links]
    )
    for uri in all_sources_targets:
        if uri not in nodes_registry:
            pass

    # 3. Format for D3.js
    output = {"nodes": list(nodes_registry.values()), "links": links}

    # save to JSON
    print(f"Saving graph to {graph_path}")
    utilities.dict2json(output, graph_path)


def generate_backlinks_graphs(
    graph_json: str | Path = "./graph.json", graph_dir="./graph"
):
    """
    Generates for each entity a D3.js compatible graph given the complete graph.
    """
    graph_dir = Path(graph_dir)
    graph_dir.mkdir(parents=True, exist_ok=True)

    # Import whole graph
    G = utilities.json2dict(graph_json)

    for node in G.get("nodes", []):
        g = {"nodes": [node]}

        # filter all links that have the node as source
        g["links"] = [l for l in G.get("links", []) if l["source"] == node["id"]]

        # filter all links that have the node as target
        g["links"] += [l for l in G.get("links", []) if l["target"] == node["id"]]

        # Get unique neighbor node IDs
        neighbour_ids = set(
            [link["target"] for link in g["links"]]
            + [link["source"] for link in g["links"]]
        )

        # Retrieve neighbor node data from main graph
        neighbour_nodes = [n for n in G["nodes"] if n["id"] in neighbour_ids]
        g["nodes"] += neighbour_nodes

        # Add links between neighbors
        nodes_list = [node["id"] for node in g["nodes"]]
        g["links"] += [
            link
            for link in G.get("links", [])
            if link["source"] in nodes_list and link["target"] in nodes_list
        ]

        # ✅ IMPROVED: Remove duplicates without pandas using dict + set
        # Remove duplicate nodes (by id)
        seen_nodes = {}
        for node_item in g["nodes"]:
            seen_nodes[node_item["id"]] = node_item
        g["nodes"] = list(seen_nodes.values())

        # Remove duplicate links (by source + target + property tuple)
        seen_links = {}
        for link in g["links"]:
            link_key = (link["source"], link["target"], link.get("property", ""))
            seen_links[link_key] = link
        g["links"] = list(seen_links.values())

        # save graph locally
        file_path = graph_dir / f"{node['id'].split('/')[-1]}.json"
        utilities.dict2json(g, file_path)
