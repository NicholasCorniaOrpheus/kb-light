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
    output_dir: str = "./data/rdf/",
    properties_mapping_filepath: str = "./data/mappings/yaml_properties2lod.csv",
    classes_mapping_filepath: str = "./data/mappings/yaml_classes2lod.csv",
    namespaces_mapping_filepath: str = "./data/mappings/namespaces.json",
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
    s = URIRef(value=entity["id"], base=base_url)

    # Add default base type statement
    g.add((s, RDF.type, RDFS.Resource))

    for yaml_prop in entity.keys():
        # Ignore system keys like ID and internal markdown body
        if yaml_prop in ["id", "markdown_content", "filename"]:
            continue

        # Match LOD property safely without crashing on missing mappings
        lod_matches = list(
            filter(lambda x: x["yaml_property"] == yaml_prop, properties_mapping)
        )
        if not lod_matches:
            print(f"Warning: No property mapping found for '{yaml_prop}'. Skipping.")
            continue

        lod_mapping = lod_matches[0]
        p = URIRef(lod_mapping["property_URI"])
        data_type = lod_mapping["data_type"]

        # 1. Statement Type (RDF Reification Fixed)
        if data_type == "Statement":
            # Fixed typo: changed x["yaml_prop"] to x["yaml_property"]
            substatements = list(
                filter(
                    lambda x: f"{yaml_prop}/" in x["yaml_property"],
                    properties_mapping,
                )
            )

            values = (
                entity[yaml_prop]
                if isinstance(entity[yaml_prop], list)
                else [entity[yaml_prop]]
            )

            for o in values:
                if o is not None:
                    for substatement in substatements:
                        # Setup a valid Reified Statement Node
                        statement_id = (
                            f"{entity['id']}-statement-{utilities.truncated_uuid()}"
                        )
                        statement_node = URIRef(value=statement_id, base=base_url)

                        sub_p = URIRef(substatement["property_URI"])
                        sub_o_val = o.get(substatement["yaml_property"])

                        if sub_o_val is not None:
                            # Assert the statement existence and its components correctly
                            g.add((statement_node, RDF.type, RDF.Statement))
                            g.add((statement_node, RDF.subject, s))
                            g.add((statement_node, RDF.predicate, sub_p))
                            g.add((statement_node, RDF.object, Literal(sub_o_val)))

        # 2. String Type
        elif data_type == "String":
            values = (
                entity[yaml_prop]
                if isinstance(entity[yaml_prop], list)
                else [entity[yaml_prop]]
            )
            for o in values:
                if o is not None:
                    g.add((s, p, Literal(o)))

        # 3. Entity Type
        elif data_type == "Entity":
            values = (
                entity[yaml_prop]
                if isinstance(entity[yaml_prop], list)
                else [entity[yaml_prop]]
            )
            for o in values:
                if o is not None:
                    g.add((s, p, URIRef(value=o, base=base_url)))

        # 4. Date Type
        elif data_type == "Date":
            values = (
                entity[yaml_prop]
                if isinstance(entity[yaml_prop], list)
                else [entity[yaml_prop]]
            )
            for o in values:
                if o is not None:
                    g.add((s, p, Literal(o, datatype=XSD.date)))

        # 5. Integer Type
        elif data_type == "Integer":
            values = (
                entity[yaml_prop]
                if isinstance(entity[yaml_prop], list)
                else [entity[yaml_prop]]
            )
            for o in values:
                if o is not None:
                    g.add((s, p, Literal(o, datatype=XSD.integer)))

        # 6. Float Type
        elif data_type == "Float":
            values = (
                entity[yaml_prop]
                if isinstance(entity[yaml_prop], list)
                else [entity[yaml_prop]]
            )
            for o in values:
                if o is not None:
                    g.add((s, p, Literal(o, datatype=XSD.float)))

        # 7. Class Type
        elif data_type == "Class":
            class_matches = list(
                filter(
                    lambda x: x["yaml_class"] == entity[yaml_prop],
                    classes_mapping,
                )
            )
            if class_matches:
                lod_class = class_matches[0]["class_URI"]
                g.add((s, p, URIRef(lod_class)))
            else:
                print(f"Warning: Class mapping not found for '{entity[yaml_prop]}'.")

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
    output_filepath = os.path.join(output_dir, f"{entity['id']}{extension}")

    # Serialize to file
    try:
        g.serialize(destination=output_filepath, format=serialization_format)
        print(f"Successfully serialized RDF to {output_filepath}")
    except Exception as e:
        print(f"Serialization failed: {e}")

    return g
