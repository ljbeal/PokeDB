"""
Interface code for downloading json files

Learnset documentation can be found here:
https://github.com/smogon/pokemon-showdown/blob/master/sim/global-types.ts
"""
import json
import pathlib

import requests

from src import package_root


URLS = ["https://play.pokemonshowdown.com/data/pokedex.json",
        "https://play.pokemonshowdown.com/data/learnsets.json"]


def collect_data(url) -> None:
    """
    Collect the showdown database and dump to json
    """
    raw = requests.get(url).json()

    name = url.split("/")[-1]

    outfile = package_root() / pathlib.Path(f"jsondata/{name}")

    print(f"Dumping data to {outfile}", end="... ")
    with open(outfile, "w+") as o:
        json.dump(raw, o, indent=2)

    print("Done.")


if __name__ == "__main__":
    for url in URLS:
        print(f"collecting url {url}")
        collect_data(url)
