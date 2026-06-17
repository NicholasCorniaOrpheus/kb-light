from dataclasses import dataclass
from typing import Any, Dict

"""
Examples:

YAML structure
---
class: Agent
identifier:
  - Wikidata_QID: Q46999103
label: François Desterbecq
aliases:
description:
instance_of: "[[human]]"
occupation:
  - value: "[[publisher]]"
described_by_source: "[[Wikidata]]"
image:
place_of_birth:
date_of_birth:
place_of_death:
date_of_death:
  - value: 1896
sex_or_gender: "[[male]]"
---

---
class: Manifestation
label: Trésor des demoiselles (1857)
aliases:
description: 1857 issues collected in one volume.
identifier:
external_source:
  - digital_library_permalink: https://cat.orpheusinstituut.be/cgi-bin/koha/opac-detail.pl?biblionumber=19582
local_asset_path: ./assets/OI-20144531
instance_of: "[[periodical]]"
has_part:
part_of:
  - value: "[[Le trésor des demoiselles]]"
contributor:
  - value: "[[François Desterbecq]]"
    role: "[[publisher]]"
has_edition_or_translation:
title: Trésor des demoiselles. Vingt-cinquième Année.
publication_date:
  - value: 1857-01-01
place_of_publication:
  - value: "[[Amsterdam]]"
  - value: "[[Brussels]]"
instrumentation:
language_of_work_or_name:
  - value: "[[French]]"
---

"""


@dataclass
class Statement:
    s: str  # Subjject = Entity URI (base_url+UUID)
    p: str  # Predicate = property name
    o: str  # Object = The datatype is determined based on the property mapping between YAML and Linked Open Data
    qualifiers: Dict[str, Any] = None
