def block(title: str, lines: list) -> str:
    """
    Build a YAML block with examples
    """
    out = f"- {title}:\n"
    out += "  examples: |\n"
    for line in lines:
        out += f"    - {line}\n"
    return out


def write_header() -> str:
    """
    Write YAML header
    """
    return 'version: "3.1"\n\nnlu:\n'


def write_intent_block(intent_name: str, examples: list) -> str:
    """
    Write intent block
    """
    out = f"\n- intent: {intent_name}\n"
    out += "  examples: |\n"
    for ex in examples:
        out += f"    - {ex}\n"
    return out


def write_synonym_block(canonical: str, examples: list) -> str:
    """
    Write synonym block
    """
    out = f"\n- synonym: {canonical}\n"
    out += "  examples: |\n"
    for ex in examples:
        out += f"    - {ex}\n"
    return out


def write_regex_block(name: str, patterns: list) -> str:
    """
    Write regex block
    """
    out = f"\n- regex: {name}\n"
    out += "  examples: |\n"
    for pattern in patterns:
        out += f"    - {pattern}\n"
    return out


def write_lookup_block(name: str, values: list) -> str:
    """
    Write lookup block
    """
    out = f"\n- lookup: {name}\n"
    out += "  examples: |\n"
    for val in values:
        out += f"    - {val}\n"
    return out
