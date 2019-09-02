from os import remove
from tempfile import NamedTemporaryFile

from opwen_email_client.domain.email.sql_store import SqliteEmailStore
from tests.opwen_email_client.domain.email.test_store import Base


class SqliteEmailStoreTests(Base.EmailStoreTests):
    store_location = None

    def create_email_store(self, restricted=None):
        return SqliteEmailStore(
            self.page_size,
            self.store_location,
            restricted,
        )

    @classmethod
    def setUpClass(cls):
        with NamedTemporaryFile(delete=False) as fobj:
            cls.store_location = fobj.name

    @classmethod
    def tearDownClass(cls):
        remove(cls.store_location)

    def tearDown(self):
        dbwrite = self.email_store._dbwrite
        base = self.email_store._base

        with dbwrite() as db:
            for table in reversed(base.metadata.sorted_tables):
                db.execute(table.delete())
