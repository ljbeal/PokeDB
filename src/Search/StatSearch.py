from BaseSearch import BaseSearch
from src import package_root


class StatSearch(BaseSearch):

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

        cmd = f"SELECT * FROM pokemon WHERE {stat} {operator} {val}"

        return cmd


if __name__ == "__main__":
    db = package_root() / "sql/test.db"

    test = StatSearch(db)

    print(test.search("spe >= 120"))
