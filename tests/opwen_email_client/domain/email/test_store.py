from os import remove
from tempfile import NamedTemporaryFile

from opwen_email_client.domain.email.store import SqliteEmailStore
from opwen_infrastructure.serialization.json import JsonSerializer
from opwen_tests.opwen_domain.test_email import Base


class SqliteEmailStoreTests(Base.EmailStoreTests):
    def create_email_store(self):
        return SqliteEmailStore(self.store_location, JsonSerializer())

    @classmethod
    def setUpClass(cls):
        with NamedTemporaryFile(delete=False) as fobj:
            cls.store_location = fobj.name

    @classmethod
    def tearDownClass(cls):
        # noinspection PyUnresolvedReferences
        remove(cls.store_location)

    def tearDown(self):
        # noinspection PyUnresolvedReferences
        dbwrite = self.email_store._dbwrite
        # noinspection PyUnresolvedReferences
        base = self.email_store._base

        with dbwrite() as db:
            for table in reversed(base.metadata.sorted_tables):
                db.execute(table.delete())
