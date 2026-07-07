# Core modules

## kblight.entity

This module extract information from your Markdown notes, such as assets located in a local folder in vault, statements in YAML property header and unstructured text such as descriptions and notes.

The `convert_properties` and `split_vaults` are still in development.

::: kblight.entity.assets
	options:
	  heading_level: 3

<!-- ::: kblight.entity.convert_properties
	options:
	  heading_level: 3
	-->

::: kblight.entity.import_md
	options:
	  heading_level: 3

<!-- ::: kblight.entity.split_vaults
	options:
	  heading_level: 3
	-->

## kblight.serialize

This module serializes each entity statements in CSV, JSON and RDF formats (XML, Turtle or JSON-LD). For the RDF serialization, a CSV mapping is required in order to connect each Obsidian property to a Linked Open Data URI from vocabularies.

See the `yaml_classes2lod.csv`, `yaml_properties2lod.csv` and `namespaces.json` in the example/ folder of this GitHub repository.

::: kblight.serialize.csv_serialization
	options:
	  heading_level: 3

::: kblight.serialize.json_serialization
	options:
	  heading_level: 3

::: kblight.serialize.rdf_serialization
	options:
	  heading_level: 3

## kblight.site

This module generates Markdown pages for each entity based on a Jinja2 template (see example in `data/config/entity_template.md.j2`). Furthermore, D3.js compatible JSON graph representations and a custom search index for the advanced search are also generated.

::: kblight.site.advanced_search
	options:
	  heading_level: 3

::: kblight.site.d3_graph
	options:
	  heading_level: 3

::: kblight.site.jinja
	options:
	  heading_level: 3

## kblight.statement

This module organises statements according to the categories `metadata`, `statements`, `assets` and `content`. You can set each property's category via the `data/mappings/yaml_properties2lod.csv` file.

::: kblight.statement.statements
	options:
	  heading_level: 3

## kblight.utilities

General module with utility functions, such as import and export of YAML and JSON formats from and to Python dictionaries.

::: kblight.utilities
	options:
	  heading_level: 3