from os import environ

#
# Environment configuration values
#

STORAGE_ACCOUNT = environ.get('LOKOLE_EMAIL_SERVER_AZURE_STORAGE_NAME')
STORAGE_KEY = environ.get('LOKOLE_EMAIL_SERVER_AZURE_STORAGE_KEY')

CLIENT_STORAGE_ACCOUNT = environ.get('LOKOLE_CLIENT_AZURE_STORAGE_NAME')
CLIENT_STORAGE_KEY = environ.get('LOKOLE_CLIENT_AZURE_STORAGE_KEY')

EMAIL_SENDER_KEY = environ.get('LOKOLE_SENDGRID_KEY')

LOG_LEVEL = environ.get('LOKOLE_LOG_LEVEL', 'DEBUG')

APPINSIGHTS_KEY = environ.get('LOKOLE_EMAIL_SERVER_APPINSIGHTS_KEY')

#
# Azure configuration values
#

CONTAINER_CLIENT_PACKAGES = 'compressedpackages'
CONTAINER_EMAILS = 'emails'
CONTAINER_SENDGRID_MIME = 'sendgridinboundemails'

TABLE_DOMAIN = 'emaildomain'
TABLE_TO = 'emailto'
TABLE_CC = 'emailcc'
TABLE_BCC = 'emailbcc'
TABLE_FROM = 'emailfrom'
TABLE_DOMAIN_X_DELIVERED = 'emaildomainxdelivered'
TABLE_AUTH = 'clientsauth'

QUEUE_CLIENT_PACKAGE = 'lokoleinboundemails'
QUEUE_EMAIL_SEND = 'sengridoutboundemails'
QUEUE_SENDGRID_MIME = 'sengridinboundemails'
QUEUE_POLL_INTERVAL = float(environ.get('LOKOLE_QUEUE_POLL_SECONDS', '10'))
