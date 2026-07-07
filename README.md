# KBlight - Knowledge Base Light

A Python package that generates a static web application from your Obsidian vault notes. It is aimed at researchers in Digital Humanities wishing to publish their research in a sustaible, yet FAIR compatible manner.

## Setting up your local knowledge base

The package transforms a local directory of Markdown files, with corresponding YAML metadata, into an elegant static website knowledge base that can be easily hosted on GitHub Pages or similar services for long-term longevity, without the need of costly infrastructures required by many softwares such as Wikibase.

We advise you to use Obsidian in order to create your interconnected Markdown files for your entities, but you are free to use any other softwares, even text editors or creating your own scripts in order to programmatically generate them.

The YAML metadata supports nested properties, similar to Wikidata qualifiers and references, that can be made manually or with the support of [Metadata Menu](https://mdelobelle.github.io/metadatamenu/) Obsidian plugin. 

## Features

- Static website is effortless built from Markdown pages via [Mkdocs Material](https://squidfunk.github.io/mkdocs-material/).
- Simple search features and indexing at built using [Lunr.js](https://lunrjs.com/).
- Custom Javascript advanced search feature, with filters based on properties, timestamps and classes.
- Unique identifiers are assigned to each entity, according to the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) standards via a truncated short identifier.
- Custom [Jinja2](https://github.com/noirbizarre/jinja2) templates in order to generate Markdown pages for each entity according to their class.
- Serialization of data in a variety of format, such as JSON, YAML, RDF Turtle and JSON-LD and CSV.
- Graph visualization of statements via [D3.js](https://d3js.org/).
- Integrate digital assets via IIIF manifests or simple URLs rendered via [OpenSeadragon](https://openseadragon.github.io/).
- TEI visualization via [CETEIcean](https://github.com/teic/ceteicean) (still in development).
- MEI visualization of music scores via [Verovio](https://www.verovio.org/index.xhtml) (still in development).