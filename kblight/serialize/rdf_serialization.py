from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, XSD, RDFS
import os

from kblight import utilities

"""
Classes for data types [rdfterms](https://rdflib.readthedocs.io/en/6.2.0/rdf_terms.html)

class rdflib.term.URIRef(value: str, base: Optional[str] = None)

uri = URIReF(value="Q1",base="http;//wikidata.org/entity/")

class rdflib.term.Literal(lexical_or_value: Any, lang: Optional[str] = None, datatype: Optional[str] = None, normalize: Optional[bool] = None)

name = Literal("Nicholas")

age = Literal(39, datatype=XSD.integer)

density = Literal(0.43, datatype=XSD.float)

date = Literal('2006-01-01',datatype=XSD.date)

"""


def _setup_namespaces(g: Graph, namespaces: list) -> dict:
    """Load and bind namespaces to the graph.

    Args:
            g (rdflib.Graph): The RDF graph to bind namespaces to.
            namespaces (list): List of dictionaries for the namespaces.

    Returns:
            dict: Dictionary mapping namespace strings to their URIs.
    """

    for ns in namespaces:
        namespace_prefix = ns["namespace"]
        namespace_uri = Namespace(ns["base_URI"])
        g.bind(namespace_prefix, namespace_uri)

    return {ns["namespace"]: ns["base_URI"] for ns in namespaces}


def _get_namespace_uri(namespace_key: str, namespaces: list) -> str:
    """Get the base URI for a given namespace key.

    Args:
            namespace_key (str): The namespace identifier to look up.
            namespaces (list): List of namespace dictionaries.

    Returns:
            str: The base URI for the namespace.

    Raises:
            ValueError: If namespace not found.
    """
    matching = list(filter(lambda x: x["namespace"] == namespace_key, namespaces))
    if not matching:
        raise ValueError(f"Namespace '{namespace_key}' not found in namespaces file")
    return matching[0]["base_URI"]


def rdf_serialization(
    entity: dict,
    kblight_namespace: str,
    output_dir: str = "./rdf/",
    properties_mapping_filepath: str = "./mappings/yaml_properties2lod.csv",
    classes_mapping_filepath: str = "./mappings/yaml_classes2lod.csv",
    namespaces_mapping_filepath: str = "./mappings/namespaces.json",
    serialization_format="turtle",
) -> Graph:
    """Export the entity as RDF serialized data structure."""

    properties_mapping = utilities.csv2dict(properties_mapping_filepath)
    classes_mapping = utilities.csv2dict(classes_mapping_filepath)

    # Initialize main RDF graph
    g = Graph()

    # Load namespaces and bind to main graph
    namespaces = utilities.json2dict(namespaces_mapping_filepath)
    _setup_namespaces(g, namespaces)

    # Target specific base URL
    matching_ns = list(
        filter(lambda x: x["namespace"] == kblight_namespace, namespaces)
    )
    if not matching_ns:
        print(f"Error: Namespace '{kblight_namespace}' not found.")
        return g

    base_url = matching_ns[0]["base_URI"]
    s = URIRef(value=entity["metadata"]["id"], base=base_url)

    # Add default base type statement
    g.add((s, RDF.type, RDFS.Resource))

    def convert_statements_to_rdf(g, ent, ent_id):
        for yaml_prop in ent.keys():
            # Ignore system keys like ID and internal markdown body
            if yaml_prop in ["id", "markdown_content", "filename", "n_id", "base_name"]:
                continue

            # Match LOD property safely without crashing on missing mappings
            lod_matches = list(
                filter(lambda x: x["yaml_property"] == yaml_prop, properties_mapping)
            )
            if not lod_matches:
                print(
                    f"Warning: No property mapping found for '{yaml_prop}'. Skipping."
                )
                continue

            lod_mapping = lod_matches[0]
            p = URIRef(lod_mapping["property_URI"])
            data_type = lod_mapping["data_type"]

            # 1. Statement Type (RDF Reification Fixed)
            if data_type == "Statement":
                # Find all qualifiers/sub-properties for this parent property
                # e.g., if yaml_prop is 'contributor', this finds 'contributor/role'
                substatements = [
                    x
                    for x in properties_mapping
                    if x["yaml_property"].startswith(f"{yaml_prop}/")
                ]

                # Ensure we iterate through the list of factoid objects
                values = (
                    ent[yaml_prop]
                    if isinstance(ent[yaml_prop], list)
                    else [ent[yaml_prop]]
                )

                for o in values:
                    if o is not None and isinstance(o, dict):
                        # FIX 1: Generate ONE unique assertion node for this specific factoid
                        # This groups the subject, predicate, object, and all qualifiers together [3]
                        statement_id = (
                            f"{ent_id}-assertion-{utilities.truncated_uuid()}"
                        )
                        statement_node = URIRef(value=statement_id, base=base_url)

                        # Core Reification: Assert this is a statement
                        g.add((statement_node, RDF.type, RDF.Statement))
                        g.add((statement_node, RDF.subject, s))
                        g.add((statement_node, RDF.predicate, p))

                        # FIX 2: Resolve the primary value (the 'object' of the assertion)
                        main_val = o.get("value")
                        if main_val:
                            # In factoid models, the main value is usually an Entity link [1]
                            main_obj = URIRef(value=main_val, base=base_url)
                            g.add((statement_node, RDF.object, main_obj))

                            # Optional: Also add the direct triple for easier non-LOD querying
                            g.add((s, p, main_obj))

                        # FIX 3: Process Qualifiers (Substatements)
                        for substatement in substatements:
                            sub_p = URIRef(substatement["property_URI"])

                            # Extract the internal key (e.g., 'role' from 'contributor/role')
                            sub_key = substatement["yaml_property"].split("/")[-1]
                            sub_o_val = o.get(sub_key)

                            if sub_o_val is not None:
                                # Resolve qualifier type (Entity vs Literal)
                                sub_data_type = substatement.get("data_type", "String")

                                if sub_data_type == "Entity":
                                    g.add(
                                        (
                                            statement_node,
                                            sub_p,
                                            URIRef(value=sub_o_val, base=base_url),
                                        )
                                    )
                                elif sub_data_type == "Date":
                                    g.add(
                                        (
                                            statement_node,
                                            sub_p,
                                            Literal(sub_o_val, datatype=XSD.date),
                                        )
                                    )
                                else:
                                    g.add((statement_node, sub_p, Literal(sub_o_val)))
            # 2. String Type
            elif data_type == "String":
                for o in values:
                    if o is not None:
                        # Handle both simple strings and factoid objects
                        val = o.get("value") if isinstance(o, dict) else o
                        if val:
                            g.add((s, p, Literal(val)))

            # 3. Entity Type (Internal links to other entities)
            elif data_type == "Entity":
                for o in values:
                    if o is not None:
                        val = o.get("value") if isinstance(o, dict) else o
                        if val:
                            g.add((s, p, URIRef(value=val, base=base_url)))

            # 4. Date Type (Handles YYYY-MM-DD format)
            elif data_type == "Date":
                for o in values:
                    if o is not None:
                        val = o.get("value") if isinstance(o, dict) else o
                        if val:
                            # Serialize as XSD.date for Linked Open Data compatibility
                            g.add((s, p, Literal(val, datatype=XSD.date)))

            # 5. Integer Type
            elif data_type == "Integer":
                for o in values:
                    if o is not None:
                        val = o.get("value") if isinstance(o, dict) else o
                        try:
                            g.add((s, p, Literal(int(val), datatype=XSD.integer)))
                        except (ValueError, TypeError, AttributeError):
                            continue

            # 6. Float Type
            elif data_type == "Float":
                for o in values:
                    if o is not None:
                        val = o.get("value") if isinstance(o, dict) else o
                        try:
                            g.add((s, p, Literal(float(val), datatype=XSD.float)))
                        except (ValueError, TypeError, AttributeError):
                            continue

            # 7. Class Type (Mapping the entity to its ontology class)
            elif data_type == "Class":
                for o in values:
                    if o is not None:
                        val = o.get("value") if isinstance(o, dict) else o
                        if val:
                            # Use RDF.type if the property is 'class', otherwise use the mapped P
                            predicate = RDF.type if yaml_prop == "class" else p
                            g.add((s, predicate, URIRef(value=val, base=base_url)))

    return g

    # adding metadata
    g += convert_statements_to_rdf(g, entity["metadata"], entity["metadata"]["id"])
    # adding statements
    g += convert_statements_to_rdf(g, entity["statements"], entity["metadata"]["id"])

    # Output directory and file serialization handling (Completed)
    os.makedirs(output_dir, exist_ok=True)

    extension_map = {
        "turtle": ".ttl",
        "json-ld": ".json",
        "pretty-xml": ".xml",
        "xml": ".xml",
        "nt": ".nt",
    }
    extension = extension_map.get(serialization_format, ".ttl")
    output_filepath = os.path.join(output_dir, f"{entity['metadata']['id']}{extension}")

    # Serialize to file
    try:
        g.serialize(destination=output_filepath, format=serialization_format)
        # print(f"Successfully serialized RDF to {output_filepath}")
    except Exception as e:
        print(f"Serialization failed: {e}")

    return g
