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

    def cmd(self, *args, **kwargs):
        raise NotImplementedError

    def search(self, *args, **kwargs):

        conn = self.db.connection
        cur = conn.cursor()

        result = cur.execute(self.cmd(*args, **kwargs))

        return [p[1] for p in result.fetchall()]
