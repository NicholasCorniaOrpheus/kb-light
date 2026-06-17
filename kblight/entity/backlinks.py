import re


def extract_backlinks(
    entity: Entity, all_entities: List[Entity]
) -> Dict[str, List[str]]:
    """
    Returns mapping: { referencing_entity_id: [property1, property2, ...] }
    Also parses markdown free-text for [[wikilinks]].
    """
    backlinks = defaultdict(list)

    # Check structured statements
    for stmt in entity.statements:
        # TO BE CORRECTED
        if isinstance(stmt.object, str) and stmt.object in [e.id for e in all_entities]:
            backlinks[stmt.object].append(stmt.predicate)

    # Check markdown for [[entity_id]]
    # IT HAS TO CHECK THE FILENAME of the entity.
    pattern = r"\[\[([^\]]+)\]\]"
    for match in re.finditer(pattern, entity.markdown_content):
        ref_id = match.group(1)
        if ref_id in [e.id for e in all_entities]:
            backlinks[ref_id].append(f"mentioned_in_text_of_{entity.id}")

    return dict(backlinks)
