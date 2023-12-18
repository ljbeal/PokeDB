import sqlite3

from src import package_root


class Database:
    """
    Database handler class
    """

    def __init__(self, file):
        self._file = file

    @property
    def file(self):
        return self._file

    @property
    def connection(self):
        return sqlite3.connect(self.file)

    def execute(self, cmd: str, commit: bool = False):
        """
        Execute one single command
        """
        conn = None
        try:
            conn = sqlite3.connect(self.file)
            cursor = conn.cursor()
            cursor.execute(cmd)

            if commit:
                conn.commit()

        finally:
            if conn is not None:
                conn.close()

    def create_table(self, name: str, columns: list, types: list, force: bool = False):
        """
        Insert table into database
        """
        if force:
            self.execute(f"DROP TABLE if EXISTS {name}")

        fields = []
        for col, datatype in zip(columns, types):
            fields.append(f"{col} {datatype}")

        if len(fields) == 0:
            raise ValueError("Cannot create empty table")

        create = f"CREATE TABLE if NOT EXISTS {name} (" + ", ".join(fields) + ")"

        print(create)
        self.execute(create)

    def find_name(self, name: str | list | None = None) -> list:
        """
        Find a pokemon by name, or list of names
        """
        def parse_query(field: str, query: str | list) -> str:
            if query is None:
                raise ValueError("query cannot be None")

            if isinstance(query, str):
                return f"{field} = '{query.title()}'"

            elif isinstance(query, list):

                concat = "(" + ",".join([f"'{n.title()}'" for n in query]) + ")"

                return f"{field} in {concat}"

        query = []
        if name is not None:
            query.append(parse_query("name", name))

        if len(query) == 0:
            return []

        cmd = f"SELECT * FROM Pokemon WHERE {'AND '.join(query)}"

        cur = self.connection.cursor()

        search = cur.execute(cmd)

        return search.fetchall()


if __name__ == "__main__":

    testpath = package_root() / "sql/test.db"

    db = Database(testpath)

    print(db.find_name(name="Bulbasaur"))

    print(db.find_name(name=["Charizard", "Darkrai"]))
