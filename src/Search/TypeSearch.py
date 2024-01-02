from BaseSearch import BaseSearch
from src import package_root


class TypeSearch(BaseSearch):

    def cmd(self, query: str | list) -> str:
        """
        Search for types, either a string or list of strings

        >>> s = TypeSearch(...)
        >>> s.search("fire")
        >>> # > list of fire types

        >>> s.search(["water", "grass"])
        >>> # > list of pokemon that have water OR grass type
        """
        if isinstance(query, str):
            return (f"SELECT * "
                    f"FROM pokemon "
                    f"WHERE type1 = '{query.title()}' "
                    f"OR type2 = '{query.title()}';")
        else:
            clean = "(" + ", ".join([f"'{t.title()}'" for t in query]) + ")"
            return (f"SELECT * "
                    f"FROM pokemon "
                    f"WHERE type1 in {clean} "
                    f"OR type2 in {clean};")


if __name__ == "__main__":
    db = package_root() / "sql/test.db"

    test = TypeSearch(db)

    print(test.search("fire"))
