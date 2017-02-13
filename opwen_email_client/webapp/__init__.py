# pylint: disable=wrong-import-position
from opwen_email_client.webapp.ioc import create_app

app = create_app()

from opwen_email_client.webapp import login
from opwen_email_client.webapp import views
