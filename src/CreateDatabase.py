import json
import math
import pathlib

from src import package_root
from src.Database import Database
from src.utils.clean_sql import remove_sql_illegal_characters


SOURCE_LEARNSET = package_root() / "jsondata/learnsets.json"
SOURCE_POKES = package_root() / "jsondata/pokedex.json"
SOURCE_MOVES = package_root() / "jsondata/moves.json"


class Conversion:
    """
    Simple class that stores information on converting the json data to sql
    """

    __slots__ = ["fieldname", "jsonpath", "datatype", "multipath"]

    def __init__(self, fieldname: str, jsonpath: list, datatype: str):
        self.fieldname = fieldname
        self.jsonpath = jsonpath
        self.datatype = datatype
        # if we give a list of lists, flag this conversion as multi-key
        self.multipath = isinstance(jsonpath[0], list)


class Injector:
    """
    Base class for a database insertion schema.

    Must specify the table name, json source path and a schema.

    Schema definition is done by a list of Conversion objects within a `convert` property
    """

    def __init__(self, file):
        self._db = Database(file)

        self.create()
        self.fill()

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

        def flatten_dict(data: dict) -> [list, list]:
            """
            Return a list of all keys within a dict
            """
            keys = []
            vals = []
            for k, v in data.items():
                if isinstance(v, dict):
                    newkeys, newvals =  flatten_dict(v)

                    keys += [f"{k}/{val}" for val in newkeys]
                    vals += newvals
                else:
                    keys.append(k)
                    vals.append(v)

            return keys, vals

        with open(self.source) as o:
            raw = json.load(o)

        data_fields = {}
        for name, data in raw.items():
            print(f"parsing item {name}", end="... ")

            keys, vals = flatten_dict(data)
            flat_data = {k: v for k, v in zip(keys, vals)}

            for key in keys:
                if key not in data_fields:
                    data_fields[key] = False

            num = data["num"]

            if num < 0:
                print("Skipped.")
                continue

            fields = []
            values = []
            for convert in self.convert:
                # get the field, path(s) and data type
                field = convert.fieldname
                jpath = convert.jsonpath
                dtype = convert.datatype
                # if we're not multipathing, just add the path to a list and proceed
                if not convert.multipath:
                    jpath = [jpath]

                # iterate over all paths, adding the result to vals, to be reduced later
                vals = []
                for p in jpath:
                    # need to separate out string and int "paths"
                    path = []
                    idx = []
                    for item in p:
                        if isinstance(item, int):
                            idx.append(item)
                        else:
                            path.append(item)
                    path = "/".join(path)

                    value = flat_data.get(path, None)

                    for i in idx:
                        try:
                            value = value[i]
                        except IndexError:
                            # this index doesn't exist, invalidate the result
                            value = None

                    if value is not None:
                        data_fields[path] = True

                    vals.append(value)

                value = None
                for v in vals:
                    if value is None:
                        value = v
                    elif v != value and v is not None:
                        raise ValueError(f"got differing values for field {field}, {v} vs {value}")

                if value is None:
                    continue

                if dtype == "INT" and isinstance(value, bool):
                    value = 101

                if dtype == "TEXT":
                    values.append(f"'{remove_sql_illegal_characters(str(value))}'")
                elif dtype == "BOOL":
                    values.append(str(bool(value)))
                else:
                    values.append(str(value))

                fields.append(field)

            cmd = f"INSERT INTO {self.name} (" + ", ".join(fields) + ")\nVALUES (" + ", ".join(values) + ")"

            print("Done.")

            conn = self.connection
            cur = conn.cursor()
            cur.execute(cmd)
            conn.commit()
            cur.close()

        print("data types used:")
        maxlen = max([len(k) for k in data_fields])
        for key in sorted(list(data_fields.keys())):
            v = data_fields[key]
            print(key.ljust(maxlen), v)


class Learnset(Injector):

    name = "learnset"
    source = SOURCE_LEARNSET

    def create(self):
        with open(self.source) as o:
            rawdata = json.load(o)

        flat = {}
        allmoves = []
        for poke, data in rawdata.items():
            learnset = data.get("learnset", {})

            flat[poke] = {}
            for move, details in learnset.items():
                if move not in allmoves:
                    allmoves.append(move)

                flat[poke][move] = ",".join(details)

        # need to chunk the moves
        chunksize = 100
        nchunks = math.ceil(len(allmoves) / chunksize)

        print(f"creating {nchunks} tables of size {chunksize} for {len(allmoves)} moves")

        locations = {}
        for i in range(nchunks):
            name = f"{self.name}_{i}"

            u = i * chunksize
            v = min((i + 1) * chunksize, len(allmoves))

            slice = allmoves[u:v]

            locations[name] = slice

            self.db.create_table(name, ["pokemon"] + slice, ["TEXT"] * ((v - u) + 1), force=True)

        conn = self.connection
        cur = conn.cursor()
        for poke, learnset in flat.items():
            if len(learnset) == 0:
                continue

            # need to fill all the tables one by one
            for table, moves in locations.items():
                overlap = list(set(moves) & set(learnset))

                this_learnset = []
                for move in overlap:
                    this_learnset.append(f"'{learnset[move]}'")

                # print(f"from table {table}, {poke} learns {this_learnset}")

                cols = ",".join(["pokemon"] + overlap)
                vals = ",".join([f"'{poke}'"] + this_learnset)

                cmd = f"INSERT INTO {table} ({cols}) VALUES ({vals})"

                cur.execute(cmd)

            print(f"added learnset for pokemon {poke}")

        conn.commit()

    def fill(self):
        return None


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
               Conversion("abilityS", ["abilities", "S"], "TEXT"),
               Conversion("weight", ["weightkg"], "FLOAT"),
               Conversion("forme", ["forme"], "TEXT"),
               ]

    name = "pokemon"
    source = SOURCE_POKES

class Move(Injector):

    # TODO: recoil is split strangely, having two distinct types
    # TODO: parse all the boost, self/boosts, selfBoost/boosts mess into a single column
    # TODO: damage column is for set damage moves. Usually int, but "level" for things like seismic toss

    # list of flags https://www.smogon.com/forums/threads/add-an-encore-tag-in-moves-desc.3725143/post-9716164

    convert = [Conversion("num", ["num"], "INT"),
               Conversion("accuracy", ["accuracy"], "INT"),
               Conversion("breaksProtect", ["breaksProtect"], "BOOL"),
               Conversion("category", ["category"], "TEXT"),
               Conversion("critRatio", ["critRatio"], "INT"),
               Conversion("power", ["basePower"], "INT"),
               Conversion("name", ["name"], "TEXT"),
               Conversion("type", ["type"], "TEXT"),
               Conversion("target", ["target"], "TEXT"),
               Conversion("pp", ["pp"], "INT"),
               Conversion("priority", ["priority"], "INT"),
               # Conversion("recoilA", ["recoil", 0], "INT"),
               # Conversion("recoilB", ["recoil", 1], "INT"),
               Conversion("status", ["status"], "TEXT"),
               Conversion("boostsevasion", ["boosts", "evasion"], "INT"),
               Conversion("boostsacc", ["boosts", "accuracy"], "INT"),
               Conversion("boostsatk", ["boosts", "atk"], "INT"),
               Conversion("boostsdef", ["boosts", "def"], "INT"),
               Conversion("boostsspa", ["boosts", "spa"], "INT"),
               Conversion("boostsspd", ["boosts", "spd"], "INT"),
               Conversion("boostsspe", ["boosts", "spe"], "INT"),
               Conversion("selfboostsacc", ["self", "boosts", "accuracy"], "INT"),
               Conversion("selfboostsatk", [["self", "boosts", "atk"], ["selfBoost", "boosts", "atk"]], "INT"),
               Conversion("selfboostsdef", [["self", "boosts", "def"], ["selfBoost", "boosts", "def"]], "INT"),
               Conversion("selfboostsspa", [["self", "boosts", "spa"], ["selfBoost", "boosts", "spa"]], "INT"),
               Conversion("selfboostsspd", [["self", "boosts", "spd"], ["selfBoost", "boosts", "spd"]], "INT"),
               Conversion("selfboostsspe", [["self", "boosts", "spe"], ["selfBoost", "boosts", "spe"]], "INT"),
               Conversion("secondarychance", ["secondary", "chance"], "INT"),
               Conversion("secondarystatus", ["secondary", "status"], "TEXT"),
               Conversion("secondaryvolatilestatus", ["secondary", "volatileStatus"], "TEXT"),
               Conversion("secondaryboostsaccuracy", ["secondary", "boosts", "accuracy"], "INT"),
               Conversion("secondaryboostsatk", ["secondary", "boosts", "atk"], "INT"),
               Conversion("secondaryboostsdef", ["secondary", "boosts", "def"], "INT"),
               Conversion("secondaryboostsevasion", ["secondary", "boosts", "evasion"], "INT"),
               Conversion("secondaryboostsspa", ["secondary", "boosts", "spa"], "INT"),
               Conversion("secondaryboostsspd", ["secondary", "boosts", "spd"], "INT"),
               Conversion("secondaryboostsspe", ["secondary", "boosts", "spe"], "INT"),
               Conversion("secondaryselfboostsatk", ["secondary", "self", "boosts", "atk"], "INT"),
               Conversion("secondaryselfboostsdef", ["secondary", "self", "boosts", "def"], "INT"),
               Conversion("secondaryselfboostsevasion", ["secondary", "self", "boosts", "evasion"], "INT"),
               Conversion("secondaryselfboostsspa", ["secondary", "self", "boosts", "spa"], "INT"),
               Conversion("secondaryselfboostsspd", ["secondary", "self", "boosts", "spd"], "INT"),
               Conversion("secondaryselfboostsspe", ["secondary", "self", "boosts", "spe"], "INT"),
               Conversion("dustproof", ["secondary", "dustproof"], "TEXT"),
               Conversion("bite", ["flags", "bite"], "BOOL"),
               Conversion("bullet", ["flags", "bullet"], "BOOL"),
               Conversion("bypasssub", ["flags", "bypasssub"], "BOOL"),
               Conversion("cantusetwice", ["flags", "cantusetwice"], "BOOL"),
               Conversion("charge", ["flags", "charge"], "BOOL"),
               Conversion("contact", ["flags", "contact"], "BOOL"),
               Conversion("distance", ["flags", "distance"], "BOOL"),
               Conversion("defrost", ["flags", "defrost"], "BOOL"),
               Conversion("dance", ["flags", "dance"], "BOOL"),
               Conversion("mirror", ["flags", "mirror"], "BOOL"),
               Conversion("powder", ["flags", "powder"], "BOOL"),
               Conversion("protect", ["flags", "protect"], "BOOL"),
               Conversion("pulse", ["flags", "pulse"], "BOOL"),
               Conversion("punch", ["flags", "punch"], "BOOL"),
               Conversion("recharge", ["flags", "recharge"], "BOOL"),
               Conversion("reflectable", ["flags", "reflectable"], "BOOL"),
               Conversion("slicing", ["flags", "slicing"], "BOOL"),
               Conversion("snatch", ["flags", "snatch"], "BOOL"),
               Conversion("sound", ["flags", "sound"], "BOOL"),
               Conversion("wind", ["flags", "wind"], "BOOL"),
               Conversion("stallingMove", ["stallingMove"], "BOOL"),
               Conversion("selfdestruct", ["selfdestruct"], "BOOL"),
               Conversion("selfSwitch", ["selfSwitch"], "BOOL"),
               Conversion("forceSwitch", ["stallingMove"], "BOOL"),
               Conversion("hasCrashDamage", ["hasCrashDamage"], "BOOL"),
               Conversion("hasSheerForce", ["hasSheerForce"], "BOOL"),
               Conversion("ignoreEvasion", ["ignoreEvasion"], "BOOL"),
               Conversion("multiaccuracy", ["multiaccuracy"], "BOOL"),
               Conversion("multihit", ["multihit"], "BOOL"),
               Conversion("ohko", ["ohko"], "BOOL"),
               Conversion("terrain", ["terrain"], "TEXT"),
               Conversion("weather", ["weather"], "TEXT"),
               Conversion("willCrit", ["willCrit"], "BOOL"),
               Conversion("volatileStatus", ["volatileStatus"], "TEXT"),
               Conversion("selfvolatileStatus", ["self," "volatileStatus"], "TEXT"),
               ]

    name = "moves"
    source = SOURCE_MOVES


if __name__ == "__main__":

    path = package_root() / pathlib.Path("sql/test.db")

    # pokes = Pokemon(path)
    # moves = Move(path)
    learn = Learnset(path)
