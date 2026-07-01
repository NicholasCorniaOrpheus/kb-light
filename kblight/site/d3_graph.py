import re
from pathlib import Path
import json

import pandas as pd
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
        page_content_list = data["content"]["markdown_content"].split(" ")
        # find internal links
        r = re.compile(base_url)
        search_query = list(filter(r.match, page_content_list))
        for element in search_query:
            links.append({"source": entity_uri, "target": element, "property": ""})

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
    # Import whole graph
    G = utilities.json2dict(graph_json)

    for node in G.get("nodes"):
        g = {"nodes": [node]}
        # filter all links that have the node as source
        g["links"] = list(filter(lambda x: x["source"] == node["id"], G.get("links")))
        # filter all links that have the node as target
        g["links"] += list(filter(lambda x: x["target"] == node["id"], G.get("links")))
        neighbour_nodes = list(set([link["target"] for link in g["links"]]))
        neighbour_nodes += list(set([link["source"] for link in g["links"]]))
        # retrieve target nodes from main graph and append them to local one
        g["nodes"] += list(filter(lambda x: x["id"] in neighbour_nodes, G["nodes"]))
        # add extra links between neighbour_nodes
        nodes_list = [node["id"] for node in g["nodes"]]
        all_nodes_links = list(
            filter(lambda x: x["source"] in nodes_list, G.get("links"))
        )
        neighbour_nodes_links = [
            link for link in all_nodes_links if link["target"] in nodes_list
        ]

        g["links"] += neighbour_nodes_links

        # remove duplicate nodes
        df = pd.DataFrame(g["nodes"])
        df = df.drop_duplicates()
        g["nodes"] = df.to_dict(orient="records")
        # remove duplicate links
        df = pd.DataFrame(g["links"])
        df = df.drop_duplicates()
        g["links"] = df.to_dict(orient="records")
        # save graph locally
        file_path = graph_dir / f"{g['nodes'][0]['id'].split('/')[-1]}.json"
        utilities.dict2json(g, file_path)
