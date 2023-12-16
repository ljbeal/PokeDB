import json
import pathlib

from src import package_root
from src.Database import Database
from src.utils.clean_sql import remove_sql_illegal_characters


SOURCE_POKES = package_root() / "jsondata/pokedex.json"
SOURCE_MOVES = package_root() / "jsondata/moves.json"


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

    @property
    def name(self):
        raise NotImplementedError

    @property
    def source(self):
        raise NotImplementedError

    @property
    def convert(self):
        raise NotImplementedError

    def create(self):
        print("recreating database")
        cols = []
        types = []
        for conversion in self.convert:
            cols.append(conversion.fieldname)
            types.append(conversion.datatype)

        self.db.create_table(self.name, cols, types, force=True)

    def fill(self):

        with open(self.source) as o:
            raw = json.load(o)

        data_fields = {}
        for name, data in raw.items():
            print(f"parsing item {name}", end="... ")

            for key in data:
                if key not in data_fields:
                    data_fields[key] = False

            num = data["num"]

            if num < 0:
                print("Skipped.")
                continue

            fields = []
            values = []
            for convert in self.convert:
                field = convert.fieldname
                jpath = convert.jsonpath
                dtype = convert.datatype

                fields.append(field)

                temp = None
                for term in jpath:

                    if term not in data:
                        temp = None
                        continue

                    if term in data_fields:
                        data_fields[term] = True
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

                if dtype == "INT" and isinstance(temp, bool):
                    temp = 101
                elif dtype == "BOOL":
                    temp = bool(temp)

                values.append(f"'{remove_sql_illegal_characters(temp)}'")

            cmd = f"INSERT INTO {self.name} (" + ", ".join(fields) + ")\nVALUES (" + ", ".join(values) + ")"

            print("Done.")

            conn = self.connection
            cur = conn.cursor()
            cur.execute(cmd)
            conn.commit()
            cur.close()

        print("data types used:")
        maxlen = max([len(k) for k in data_fields])
        for k, v in data_fields.items():
            print(k.rjust(maxlen), v)


class Pokemon(Injector):

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
               Conversion("weight", ["weightkg"], "FLOAT"),
               ]

    name = "pokemon"
    source = SOURCE_POKES

class Move(Injector):

    convert = [Conversion("num", ["num"], "INT"),
               Conversion("accuracy", ["accuracy"], "INT"),
               Conversion("power", ["basePower"], "INT"),
               Conversion("category", ["category"], "TEXT"),
               Conversion("name", ["name"], "TEXT"),
               Conversion("type", ["type"], "TEXT"),
               Conversion("target", ["target"], "TEXT"),
               Conversion("pp", ["pp"], "INT"),
               Conversion("priority", ["priority"], "INT"),
               Conversion("stallingMove", ["stallingMove"], "BOOL"),
               Conversion("contact", ["flags", "contact"], "BOOL"),
               Conversion("protect", ["flags", "protect"], "BOOL"),
               Conversion("mirror", ["flags", "mirror"], "BOOL"),
               Conversion("snatch", ["flags", "snatch"], "BOOL"),
               Conversion("bullet", ["flags", "bullet"], "BOOL"),
               Conversion("distance", ["flags", "distance"], "BOOL"),
               Conversion("slicing", ["flags", "slicing"], "BOOL"),
               Conversion("wind", ["flags", "wind"], "BOOL"),
               Conversion("bypasssub", ["flags", "bypasssub"], "BOOL"),
               Conversion("allyanim", ["flags", "allyanim"], "BOOL"),
               Conversion("sound", ["flags", "sound"], "BOOL"),
               ]

    name = "moves"
    source = SOURCE_MOVES


if __name__ == "__main__":

    path = package_root() / pathlib.Path("sql/test.db")

    db = Move(path)
    db.create()
    db.fill()