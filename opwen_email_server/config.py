from environs import Env

from opwen_email_server.utils.string import urlsafe

env = Env()

STORAGE_PROVIDER = env('LOKOLE_STORAGE_PROVIDER', 'AZURE_BLOBS')

BLOBS_ACCOUNT = env('LOKOLE_EMAIL_SERVER_AZURE_BLOBS_NAME', '')
BLOBS_KEY = env('LOKOLE_EMAIL_SERVER_AZURE_BLOBS_KEY', '')
BLOBS_HOST = env('LOKOLE_EMAIL_SERVER_AZURE_BLOBS_HOST', '')
BLOBS_SECURE = env.bool('LOKOLE_EMAIL_SERVER_AZURE_BLOBS_SECURE', True)

TABLES_ACCOUNT = env('LOKOLE_EMAIL_SERVER_AZURE_TABLES_NAME', '')
TABLES_KEY = env('LOKOLE_EMAIL_SERVER_AZURE_TABLES_KEY', '')
TABLES_HOST = env('LOKOLE_EMAIL_SERVER_AZURE_TABLES_HOST', '')
TABLES_SECURE = env.bool('LOKOLE_EMAIL_SERVER_AZURE_TABLES_SECURE', True)

CLIENT_STORAGE_ACCOUNT = env('LOKOLE_CLIENT_AZURE_STORAGE_NAME', '')
CLIENT_STORAGE_KEY = env('LOKOLE_CLIENT_AZURE_STORAGE_KEY', '')
CLIENT_STORAGE_HOST = env('LOKOLE_CLIENT_AZURE_STORAGE_HOST', '')
CLIENT_STORAGE_SECURE = env.bool('LOKOLE_CLIENT_AZURE_STORAGE_SECURE', True)

resource_suffix = env('LOKOLE_RESOURCE_SUFFIX', '')

CONTAINER_CLIENT_PACKAGES = f"compressedpackages{resource_suffix}"
CONTAINER_EMAILS = f"emails{resource_suffix}"
CONTAINER_MAILBOX = f"mailbox{resource_suffix}"
CONTAINER_USERS = f"users{resource_suffix}"
CONTAINER_SENDGRID_MIME = f"sendgridinboundemails{resource_suffix}"
CONTAINER_PENDING = f"pendingemails{resource_suffix}"
CONTAINER_AUTH = f"clientsauth{resource_suffix}"

REGISTER_CLIENT_QUEUE = f'register{resource_suffix}'
INBOUND_STORE_QUEUE = f'inbound{resource_suffix}'
WRITTEN_STORE_QUEUE = f'written{resource_suffix}'
SEND_QUEUE = f'send{resource_suffix}'
MAILBOX_RECEIVED_QUEUE = f'mailboxreceived{resource_suffix}'
MAILBOX_SENT_QUEUE = f'mailboxsent{resource_suffix}'

SENDGRID_MAX_RETRIES = env.int('LOKOLE_SENDGRID_MAX_RETRIES', 20)
SENDGRID_RETRY_INTERVAL_SECONDS = env.float('LOKOLE_SENDGRID_RETRY_INTERVAL_SECONDS', 5)
SENDGRID_KEY = env('LOKOLE_SENDGRID_KEY', '')
DNS_ACCOUNT = env('LOKOLE_CLOUDFLARE_USER', '')
DNS_SECRET = env('LOKOLE_CLOUDFLARE_KEY', '')
DNS_PROVIDER = env('LOKOLE_DNS_PROVIDER', 'CLOUDFLARE')

LOG_LEVEL = env('LOKOLE_LOG_LEVEL', 'INFO')

APPINSIGHTS_LOG_LEVEL = env('LOKOLE_EMAIL_SERVER_APPINSIGHTS_LOG_LEVEL', 'WARNING')
APPINSIGHTS_KEY = env('LOKOLE_EMAIL_SERVER_APPINSIGHTS_KEY', '')
APPINSIGHTS_HOST = env('LOKOLE_EMAIL_SERVER_APPINSIGHTS_HOST', '')

REGISTRATION_USERNAME = env('LOKOLE_REGISTRATION_USERNAME', '')
REGISTRATION_PASSWORD = env('LOKOLE_REGISTRATION_PASSWORD', '')
REGISTRATION_GITHUB_ORGANIZATION = env('LOKOLE_REGISTRATION_GITHUB_ORGANIZATION', 'ascoderu')
REGISTRATION_GITHUB_TEAM = env('LOKOLE_REGISTRATION_GITHUB_ORGANIZATION', 'lokole-registration')

MAX_WIDTH_IMAGES = env.int('LOKOLE_MAX_WIDTH_EMAIL_IMAGES', 200)
MAX_HEIGHT_IMAGES = env.int('LOKOLE_MAX_HEIGHT_EMAIL_IMAGES', 200)

if env('LOKOLE_QUEUE_BROKER_SCHEME', '') == 'azureservicebus':
    QUEUE_BROKER = 'azureservicebus://{username}:{password}@{host}'.format(
        username=urlsafe(env('LOKOLE_EMAIL_SERVER_QUEUES_SAS_NAME')),
        password=urlsafe(env('LOKOLE_EMAIL_SERVER_QUEUES_SAS_KEY')),
        host=urlsafe(env('LOKOLE_EMAIL_SERVER_QUEUES_NAMESPACE')))
else:
    QUEUE_BROKER = env('LOKOLE_QUEUE_BROKER_URL', '')
