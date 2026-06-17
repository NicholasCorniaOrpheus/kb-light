import json


def build_lunr_index(entities: List[Entity]) -> str:
    """Generate lunr.js index as JSON for browser."""
    documents = []
    for entity in entities:
        documents.append(
            {
                "id": entity.id,
                "label": entity.label,
                "description": entity.description,
                "type": entity.type,
                "body": " ".join([stmt.predicate for stmt in entity.statements]),
            }
        )

    # Use lunr Python wrapper to build index
    idx = lunr(ref="id", fields=["label", "description", "body"], documents=documents)
    return json.dumps(idx.serialize())  # Embed in template
