from src import package_root
from src.Database import Database
from src.utils.ListFormat import format_list


class TypeSearch:

    def __init__(self, type: str | list):

        if isinstance(type, str):
            self._type = [type.title()]
        else:
            self._type = [t.title() for t in type]

    @property
    def query(self):
        return self._type

    def search(self):

        cmd = ["SELECT * FROM pokemon"]
        if len(self.query) == 1:
            cmd.append(f"WHERE type1 == '{self.query[0]}' OR")
            cmd.append(f"type2 == '{self.query[0]}'")
        else:
            cmd.append(f"WHERE type1 in {format_list(self.query, bracket=True)} AND")
            cmd.append(f"type2 in {format_list(self.query, bracket=True)}")

        cmd = " ".join(cmd)

        print(cmd)

        return cmd


if __name__ == "__main__":
    db = Database(package_root() / "sql/test.db")

    conn = db.connection
    cur = conn.cursor()

    single = TypeSearch("water")
    multi = TypeSearch(["water", "dragon"])

    print(cur.execute(single.search()).fetchall())
    print(cur.execute(multi.search()).fetchall())
