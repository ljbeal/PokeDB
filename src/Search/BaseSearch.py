import sqlite3

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

    def _search(self, query) -> sqlite3.Cursor:
        conn = self.db.connection
        cur = conn.cursor()
        return cur.execute(query)

    def search(self, *args, **kwargs) -> list:
        cmd = self.cmd(*args, **kwargs)

        table = cmd.split("FROM")[-1].split()[0]
        print(table)

        match table:
            case "moves":
                namecol = 6
            case "pokemon":
                namecol = 1
            case _:
                raise ValueError(f"Table {table} not recognised!")

        result = self._search(cmd)

        return [p[namecol] for p in result.fetchall()]
