def format_list(inp: list, bracket: bool = False) -> str:
    output = []
    if bracket:
        output.append("(")

    output.append(",".join([f"'{item}'" for item in inp]))

    if bracket:
        output.append("(")

    return "".join(output)
