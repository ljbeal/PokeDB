from BaseSearch import BaseSearch
from src import package_root


class MoveSearch(BaseSearch):

    def cmd(self, query: str) -> str:
        """
        Search for a pokemon by single stat

        Operators are python syntax, or sql syntax
        """
        stat, operator, val = query.split()

        stat = stat.lower()
        val = int(val)

        match operator:
            case ">":
                # greater than
                pass
            case ">=":
                # greater than or equal to
                pass
            case "==":
                # equal to
                pass
            case "<=":
                # less than or equal to
                pass
            case "<":
                # less than
                pass
            case "<>":
                # sql not equal to
                pass
            case "!=":
                # python not equal to
                operator = "<>"
            case _:
                raise ValueError(f"Operator {operator} not recognised!")

        cmd = f"SELECT * FROM moves WHERE {stat} {operator} {val} AND pp <> 1 AND NOT name LIKE 'Max%' AND NOT name LIKE 'HiddenPower%'"

        return cmd

    def _query_search(self, column, query):
        moves = self.search(f"{column} {query}")
        return self.search_by_moves(moves)

    def power(self, query: str) -> list:
        return self._query_search("power", query)

    def pp(self, query: str) -> list:
        return self._query_search("pp", query)

    def priority(self, query: str) -> list:
        return self._query_search("priority", query)


if __name__ == "__main__":
    db = package_root() / "sql/test.db"

    test = MoveSearch(db)

    print(test.priority(">= 1"))
