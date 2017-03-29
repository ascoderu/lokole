from os import environ

#
# Environment configuration values
#

STORAGE_ACCOUNT = environ.get('LOKOLE_EMAIL_SERVER_AZURE_STORAGE_NAME')
STORAGE_KEY = environ.get('LOKOLE_EMAIL_SERVER_AZURE_STORAGE_KEY')

CLIENT_STORAGE_ACCOUNT = environ.get('LOKOLE_CLIENT_AZURE_STORAGE_NAME')
CLIENT_STORAGE_KEY = environ.get('LOKOLE_CLIENT_AZURE_STORAGE_KEY')

#
# Azure configuration values
#

CONTAINER_CLIENT_PACKAGES = 'CompressedPackages'
CONTAINER_EMAILS = 'Emails'
CONTAINER_SENDGRID_MIME = 'SendgridInboundEmails'

TABLE_DOMAIN = 'domain'
TABLE_TO = 'to'
TABLE_CC = 'cc'
TABLE_BCC = 'bcc'
TABLE_FROM = 'from'
TABLE_DOMAIN_X_DELIVERED = 'domainXdelivered'

QUEUE_CLIENT_PACKAGE = 'LokoleInboundEmails'
QUEUE_EMAIL_SEND = 'SengridOutboundEmails'
QUEUE_SENDGRID_MIME = 'SengridInboundEmails'
