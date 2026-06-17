import networkx as nx
import json


# Need first to extract all entities directly related with current one. It is not working out of the box.
# Add images and descriptions when hovering
def build_d3_graph(entities: List[Entity], statements: List[Statement]) -> dict:
    """Convert entities + statements → D3-compatible JSON."""
    G = nx.DiGraph()

    # Add nodes
    for entity in entities:
        G.add_node(
            entity.id,
            label=entity.label,
            type=entity.type,
            description=entity.description,
        )

    # Add edges from statements
    for stmt in statements:
        if stmt.object in [e.id for e in entities]:  # Only internal links
            G.add_edge(stmt.subject, stmt.object, label=stmt.predicate)

    # Serialize
    node_link = nx.node_link_graph(G, edges="links")
    return {
        "nodes": [
            {"id": n["id"], "label": n.get("label"), "type": n.get("type")}
            for n in node_link["nodes"]
        ],
        "links": [
            {"source": l["source"], "target": l["target"], "label": l.get("label")}
            for l in node_link["links"]
        ],
    }
