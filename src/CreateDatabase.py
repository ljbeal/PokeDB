import json
import pathlib

from src import package_root
from src.Database import Database
from src.utils.clean_sql import remove_sql_illegal_characters


SOURCE_POKES = package_root() / "jsondata/pokedex.json"
SOURCE_MOVES = package_root() / "jsondata/learnsets.json"


class Conversion:
    """
    Simple class that stores information on converting the json data to sql
    """

    __slots__ = ["fieldname", "jsonpath", "datatype"]

    def __init__(self, fieldname, jsonpath, datatype):
        self.fieldname = fieldname
        self.jsonpath = jsonpath
        self.datatype = datatype


class Injector:

    convert = [Conversion("num", ["num"], "INT"),
               Conversion("name", ["name"], "TEXT"),
               Conversion("type1", ["types", 0], "TEXT"),
               Conversion("type2", ["types", 1], "TEXT"),
               Conversion("hp", ["baseStats", "hp"], "INT"),
               Conversion("atk", ["baseStats", "atk"], "INT"),
               Conversion("def", ["baseStats", "def"], "INT"),
               Conversion("spa", ["baseStats", "spa"], "INT"),
               Conversion("spd", ["baseStats", "spd"], "INT"),
               Conversion("spe", ["baseStats", "spe"], "INT"),
               Conversion("ability1", ["abilities", "0"],"TEXT"),
               Conversion("ability2", ["abilities", "1"], "TEXT"),
               Conversion("abilityH", ["abilities", "H"], "TEXT"),
               ]

    def __init__(self, file):
        self._db = Database(file)

    @property
    def db(self):
        return self._db

    @property
    def file(self):
        return self.db.file

    @property
    def connection(self):
        return self.db.connection

    def create(self):
        print("recreating database")
        cols = []
        types = []
        for conversion in self.convert:
            cols.append(conversion.fieldname)
            types.append(conversion.datatype)

        self.db.create_table("pokemon", cols, types, force=True)

        with open(SOURCE_MOVES) as o:
            movedata = json.load(o)

        allmoves = []
        for pokemon, data in movedata.items():
            learnset = data.get("learnset", {})

            for move in learnset:
                if move not in allmoves:
                    allmoves.append(move)

        allmoves = sorted(allmoves)

        self.db.create_table("learnsets", [allmoves[0]], ["TEXT"], force=True)

        for move in allmoves[1:30]:
            self.db.execute(f"ALTER TABLE learnsets ADD {move} TEXT", commit=True)

        print(f"added up to move {move}")

    def fill(self):

        with open(SOURCE_POKES) as o:
            pokedata = json.load(o)

        for name, data in pokedata.items():
            print(f"parsing pokemon {name}", end="... ")

            num = data["num"]

            if num < 0:
                print("Skipped.")
                continue

            fields = []
            values = []
            for convert in self.convert:
                field = convert.fieldname
                jpath = convert.jsonpath

                fields.append(field)

                temp = None
                for term in jpath:
                    try:
                        temp = temp[term]
                    except TypeError:
                        temp = data[term]
                    except KeyError:
                        temp = None
                        continue
                    except IndexError:
                        temp = None
                        continue

                values.append(f"'{remove_sql_illegal_characters(temp)}'")

            cmd = "INSERT INTO Pokemon (" + ", ".join(fields) + ")\nVALUES (" + ", ".join(values) + ")"

            print("Done.")

            conn = self.connection
            cur = conn.cursor()
            cur.execute(cmd)
            conn.commit()
            cur.close()


if __name__ == "__main__":

    path = package_root() / pathlib.Path("sql/test.db")

    db = Injector(path)
    db.create()
    # db.fill()
