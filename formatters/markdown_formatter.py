def dict_to_markdown(data: dict) -> str:
    """
    Converts dictionary to markdown format.
    """
    md = "## Final Extraction\n\n"

    for k, v in data.items():
        md += f"- {k}: {v}\n"

    return md