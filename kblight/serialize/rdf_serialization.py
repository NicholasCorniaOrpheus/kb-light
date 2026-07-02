"""
Simplified RDF Serialization for KB-Light

Uses RDF 1.1 reification only when necessary (multiple qualifiers).
Falls back to simple triples for factoids with only 'value' and 'label'.
"""

from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, XSD, RDFS
import os
from datetime import date, datetime
from kblight import utilities


def rdf_serialization(
    entity: dict,
    kblight_namespace: str,
    output_dir: str = "./rdf/",
    properties_mapping_filepath: str = "./mappings/yaml_properties2lod.csv",
    namespaces_mapping_filepath: str = "./mappings/namespaces.json",
    serialization_format="turtle",
) -> Graph:
    """
    Export KB-Light entity to RDF.

    Intelligently uses simple triples or reification based on factoid complexity:
    - If factoid has only 'value' and 'label': use simple triple
    - If factoid has qualifiers: use RDF 1.1 reification
    """

    properties_mapping = utilities.csv2dict(properties_mapping_filepath)
    namespaces = utilities.json2dict(namespaces_mapping_filepath)

    g = Graph()
    _setup_namespaces(g, namespaces)

    base_url = _get_namespace_uri(kblight_namespace, namespaces)
    if not base_url:
        print(f"Error: Namespace '{kblight_namespace}' not found.")
        return g

    entity_id = entity.get("metadata", {}).get("id")
    if not entity_id:
        return g

    subject_uri = URIRef(value=entity_id, base=base_url)
    g.add((subject_uri, RDF.type, RDFS.Resource))

    statements = entity.get("statements", {})
    if statements:
        _convert_statements(g, statements, properties_mapping, subject_uri, base_url)

    # Serialize
    os.makedirs(output_dir, exist_ok=True)
    extension_map = {"turtle": ".ttl", "json-ld": ".json", "xml": ".xml", "nt": ".nt"}
    extension = extension_map.get(serialization_format, ".ttl")
    output_path = os.path.join(output_dir, f"{entity_id}{extension}")

    try:
        g.serialize(destination=output_path, format=serialization_format)
        print(f"✓ RDF serialized to {output_path}")
    except Exception as e:
        print(f"✗ Serialization failed: {e}")

    return g


def _setup_namespaces(g, namespaces):
    """Bind namespaces to graph."""
    for ns in namespaces:
        if ns.get("namespace") and ns.get("base_URI"):
            g.bind(ns["namespace"], Namespace(ns["base_URI"]))


def _get_namespace_uri(key, namespaces):
    """Get base URI for namespace."""
    for ns in namespaces:
        if ns.get("namespace") == key:
            return ns.get("base_URI")
    return None


def _get_mapping(yaml_prop, mappings):
    """Look up property mapping by YAML property name."""
    for m in mappings:
        if m.get("yaml_property") == yaml_prop:
            return m
    return None


def _is_absolute_uri(val):
    """Check if value is already an absolute URI."""
    if not isinstance(val, str):
        return False
    return val.startswith(("http://", "https://", "urn:", "file://", "ftp://"))


def _normalize_value(val):
    """Convert various types to string representation."""
    if val is None:
        return None
    if isinstance(val, (date, datetime)):
        return val.isoformat()
    if isinstance(val, dict):
        return _normalize_value(val.get("value"))
    if isinstance(val, list) and len(val) > 0:
        return _normalize_value(val[0])
    return str(val) if val else None


def _make_uri(val, data_type, base_url):
    """
    Create URIRef intelligently.

    Rules:
    - Absolute URIs: use as-is
    - Local IDs (no scheme): prepend base_url
    - Non-strings: normalize first
    """
    str_val = _normalize_value(val)
    if not str_val:
        return None

    try:
        if _is_absolute_uri(str_val):
            return URIRef(str_val)
        return URIRef(value=str_val, base=base_url)
    except Exception as e:
        print(f"Warning: Could not create URIRef from '{str_val}': {e}")
        return None


def _add_triple(g, s, p, obj, obj_type, base_url):
    """Add triple with type-aware conversion."""
    str_val = _normalize_value(obj)
    if not str_val:
        return

    norm_type = (obj_type or "String").lower().strip()

    if norm_type in ["entity", "uriref"]:
        uri = _make_uri(obj, obj_type, base_url)
        if uri:
            g.add((s, p, uri))
        else:
            g.add((s, p, Literal(str_val)))
    elif norm_type == "date":
        g.add((s, p, Literal(str_val, datatype=XSD.date)))
    elif norm_type == "integer":
        try:
            g.add((s, p, Literal(int(str_val), datatype=XSD.integer)))
        except ValueError:
            g.add((s, p, Literal(str_val)))
    elif norm_type == "float":
        try:
            g.add((s, p, Literal(float(str_val), datatype=XSD.float)))
        except ValueError:
            g.add((s, p, Literal(str_val)))
    else:
        g.add((s, p, Literal(str_val)))


def _has_qualifiers(factoid):
    """
    Check if factoid has qualifiers beyond 'value' and 'label'.

    Returns True if it has meaningful sub-properties that require reification.
    """
    if not isinstance(factoid, dict):
        return False

    for key, val in factoid.items():
        # Skip 'value' and 'label' - these are basic structure
        if key in ["value", "label"]:
            continue
        # If any other key exists and is not None/empty, we have qualifiers
        if val is not None and val != "":
            return True

    return False


def _convert_statements(g, statements, mappings, subject, base_url):
    """
    Convert statements to RDF.

    Uses heuristic:
    - If Statement factoid has only 'value'+'label': use simple triple
    - If Statement factoid has other qualifiers: use RDF reification
    - Simple types: always use simple triple
    """

    for yaml_prop, values in statements.items():
        # Skip system keys
        if (
            yaml_prop in ["id", "markdown_content", "filename", "n_id", "base_name"]
            or values is None
        ):
            continue

        # Get property mapping
        prop_map = _get_mapping(yaml_prop, mappings)
        if not prop_map:
            print(f"Warning: No mapping for '{yaml_prop}'")
            continue

        data_type = prop_map.get("data_type", "String")

        pred_uri = URIRef(prop_map.get("property_URI"))
        # if not pred_uri or str(pred_uri) == "":
        #     print(f"Warning: Empty predicate URI for '{yaml_prop}'")
        #     continue

        # Normalize to list
        if not isinstance(values, list):
            values = [values]

        for val_item in values:
            if val_item is None:
                continue

            # ========== STATEMENT TYPE ==========
            if data_type == "Statement" and isinstance(val_item, dict):
                main_val = val_item.get("value")
                if main_val is None:
                    continue

                # Decide: simple triple or reification?
                has_quals = _has_qualifiers(val_item)

                if not has_quals:
                    # ✅ SIMPLE TRIPLE: only value+label, no other qualifiers
                    main_map = _get_mapping(f"{yaml_prop}/value", mappings)
                    main_type = (
                        main_map.get("data_type", "String") if main_map else "String"
                    )
                    _add_triple(g, subject, pred_uri, main_val, main_type, base_url)

                else:
                    # ✅ REIFICATION: has qualifiers
                    stmt_id = f"{subject.split('/')[-1]}-{utilities.truncated_uuid()}"
                    stmt_uri = URIRef(value=stmt_id, base=base_url)

                    # Reification header
                    g.add((stmt_uri, RDF.type, RDF.Statement))
                    g.add((stmt_uri, RDF.subject, subject))
                    g.add((stmt_uri, RDF.predicate, pred_uri))

                    # Main value as object
                    main_map = _get_mapping(f"{yaml_prop}/value", mappings)
                    main_type = (
                        main_map.get("data_type", "String") if main_map else "String"
                    )

                    if main_val:
                        _add_triple(
                            g, stmt_uri, RDF.object, main_val, main_type, base_url
                        )

                        # Direct triple for Entity types
                        if main_type.lower() in ["entity", "uriref"]:
                            uri = _make_uri(main_val, main_type, base_url)
                            if uri:
                                g.add((subject, pred_uri, uri))

                    # Qualifiers
                    for qual_key, qual_val in val_item.items():
                        if (
                            qual_key in ["value", "label"]
                            or qual_val is None
                            or qual_val == ""
                        ):
                            continue

                        qual_map = _get_mapping(f"{yaml_prop}/{qual_key}", mappings)
                        if not qual_map:
                            continue

                        qual_pred = URIRef(qual_map.get("property_URI"))
                        if not qual_pred or str(qual_pred) == "":
                            continue

                        qual_type = qual_map.get("data_type", "String")

                        if isinstance(qual_val, list):
                            for item in qual_val:
                                _add_triple(
                                    g, stmt_uri, qual_pred, item, qual_type, base_url
                                )
                        else:
                            _add_triple(
                                g, stmt_uri, qual_pred, qual_val, qual_type, base_url
                            )

            # ========== SIMPLE TYPES ==========
            else:
                _add_triple(g, subject, pred_uri, val_item, data_type, base_url)
