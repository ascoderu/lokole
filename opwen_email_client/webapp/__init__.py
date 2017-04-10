from opwen_email_client.webapp.ioc import create_app

app = create_app()

from opwen_email_client.webapp import login  # noqa: F401,E402
from opwen_email_client.webapp import views  # noqa: F401,E402
