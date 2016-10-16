from ca.ascoderu.lokole.web.email_client.ioc import create_app

app = create_app()

from ca.ascoderu.lokole.web.email_client import login
from ca.ascoderu.lokole.web.email_client import views
