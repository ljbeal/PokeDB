"""
Interface code for downloading json files

Learnset documentation can be found here:
https://github.com/smogon/pokemon-showdown/blob/master/sim/global-types.ts
"""
import json

import yaml

from src import package_root


ROOT = package_root()


def collect_data(file: str) -> dict:
    """
    Extract Information from the showdown typescript files
    """
    with open(file) as o:
        raw = o.readlines()

    # drop everything up until the actual "export const ..."
    i = 0
    for i, line in enumerate(raw):
        if line.startswith("export"):
            break
    raw = raw[i:]

    # cut out the typescript constant definition
    raw[0] = f"{{\n"

    # fix formatting to convert to valid YAML
    parsed = []
    code_block = False
    code_start_indent = -1
    # flag only the whole section, rather than replacing code blocks
    had_ts_code = False

    for line in raw:
        indent = line.count("\t")

        if not code_block:
            code_block = (":" not in line and
                          "}" not in line and
                          "{" in line and
                          line.strip() != "{")

        if not code_block and "condition:" in line:
            code_block = True

        # print(indent, code_start_indent, code_block, line.strip())

        if code_block and code_start_indent == -1:
            # parsed.append(f"{'  ' * indent}callback: True,\n")
            code_start_indent = indent
            had_ts_code = True
            continue
        elif code_block and "}," in line.strip() and indent == code_start_indent:
            code_start_indent = -1
            code_block = False
            # parsed.append("  " * indent + "},\n")
            continue
        elif code_block:
            continue

        if indent == 1 and had_ts_code:
            parsed.append(f"{'  ' * indent}callback: True,\n")
            had_ts_code = False

        line = line.replace("\t", "  ")
        line = line.replace("//", "#")

        parsed.append(line)

    # drop the ending semicolon and we now have valid yaml
    parsed = "".join(parsed)[:-2]

    with open("debug.txt", "w+") as o:
        o.write(parsed)

    data = yaml.safe_load(parsed)

    return data


if __name__ == "__main__":
    # data = collect_data(ROOT / "pokemon-showdown/data/pokedex.ts")
    # with open(ROOT / "jsondata/pokedex.json", "w+") as o:
    #     json.dump(data, o, indent = 2)

    data = collect_data(ROOT / "pokemon-showdown/data/moves.ts")
    with open(ROOT / "jsondata/moves.json", "w+") as o:
        json.dump(data, o, indent = 2)

    # data = collect_data(ROOT / "pokemon-showdown/data/learnsets.ts")
    # with open(ROOT / "jsondata/learnsets.json", "w+") as o:
    #     json.dump(data, o, indent = 2)
