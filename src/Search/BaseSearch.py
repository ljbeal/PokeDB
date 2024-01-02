import sqlite3

from src import package_root
from src.Database import Database


class BaseSearch:
    """
    Individual searches should be extremely basic, to be later chained
    """

    def __init__(self, dbfile):
        self._db = Database(dbfile)

    @property
    def db(self):
        return self._db

    def cmd(self, *args, **kwargs) -> str:
        raise NotImplementedError

    def _search(self, query) -> list:
        conn = self.db.connection
        cur = conn.cursor()

        try:
            result = cur.execute(query).fetchall()
        except sqlite3.OperationalError as E:
            print(f"error in query:\n{query}")
            raise E

        return result

    def search(self, *args, **kwargs) -> list:
        cmd = self.cmd(*args, **kwargs)

        table = cmd.split("FROM")[-1].split()[0]

        match table:
            case "moves":
                namecol = 6
            case "pokemon":
                namecol = 1
            case _:
                raise ValueError(f"Table {table} not recognised!")

        result = self._search(cmd)

        return [p[namecol] for p in result]

    def search_by_moves(self, names: list) -> list:
        """
        Get a list of pokemon that know all the moves in `names`
        """
        tables = self._search("SELECT name FROM sqlite_master WHERE type='table';")
        learnsets = [t[0] for t in tables if "learnset" in t[0]]

        cmd = [f"SELECT {learnsets[0]}.pokemon FROM {learnsets[0]}"]

        for table in learnsets[1:]:
            cmd.append(f"LEFT JOIN {table} on {learnsets[0]}.pokemon={table}.pokemon")

        if len(names) == 0:
            print("names is len 0")
            return []

        tmp = []
        for move in names:
            tmp.append(f"{move} IS NOT NULL")

        cmd.append("WHERE " + " OR ".join(tmp))

        cmd = " ".join(cmd) + ";"

        result = self._search(cmd)

        return [p[0] for p in result]


if __name__ == "__main__":
    db = package_root() / "sql/test.db"

    test = BaseSearch(db)

    print(test.search_by_moves(["blizzard", "watergun"]))
