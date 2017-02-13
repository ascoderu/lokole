from opwen_email_client.webapp.login import admin_role
from opwen_email_client.webapp.login import user_datastore
from tests.opwen_email_client.webapp.base import Base


# noinspection PyPep8Naming,PyMethodMayBeStatic
class LoginTests(Base.AppTests):
    def create_user(self, **kwargs):
        kwargs.setdefault('password', 'password')
        return user_datastore.create_user(**kwargs)

    def tearDown(self):
        user_datastore.db.session.rollback()

    def test_is_admin(self):
        admin = self.create_user(email='root@foo.com', roles=[admin_role])
        user = self.create_user(email='user@foo.com')

        self.assertTrue(admin.is_admin)
        self.assertFalse(user.is_admin)

    def test_create_duplicate_user_throws(self):
        self.create_user(email='user@foo.com')
        self.create_user(email='user@foo.com')

        with self.assertRaises(Exception):
            user_datastore.commit()
