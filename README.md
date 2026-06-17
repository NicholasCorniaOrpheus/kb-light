# KBlight - Knowledge Base light

A Python package that generates a static web application from your Obsidian vault notes. It is aimed at researchers in Digital Humanities wishing to publish their research in a sustaible, yet FAIR compatible manner.

## Setting up your local knowledge base

The package transforms a local directory of Markdown files, with corresponding YAML metadata, into an elegant static website knowledge base that can be easily hosted on GitHub Pages or similar services for long-term longevity, without the need of costly infrastructures required by many softwares such as Wikibase.

We advise you to use Obsidian in order to create your interconnected Markdown files for your entities, but you are free to use any other softwares, even text editors or creating your own scripts in order to programmatically generate them.

The YAML metadata supports nested properties, similar to Wikidata qualifiers and references, that can be made manually or with the support of [Metadata Menu](https://mdelobelle.github.io/metadatamenu/) Obsidian plugin. 

## Features

- Unique identifiers are assigned to each entity, according to the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) standards.
- Simple search features and indexing at built using [Lunr.js](https://lunrjs.com/)
- Custom HTML templates according to entity's class.
- Export and serialization of data in a variety of format, such as JSON, YAML, RDF Turtle and JSON-LD and CSV.
- Integrate digital assets via IIIF manifests URLs rendered via [OpenSeadragon](https://openseadragon.github.io/) or local images and TEI transcriptions stored on GitHub and rendered via [EVT](https://evt-project.github.io/).