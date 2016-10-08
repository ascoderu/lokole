from os import getenv


class OpwenConfig(object):
    CLIENT_NAME = getenv('OPWEN_CLIENT_NAME')
    CLIENT_EMAIL_HOST = '{}.ascoderu.ca'.format(CLIENT_NAME)
    INTERNET_INTERFACE_NAME = getenv('OPWEN_INTERNET_INTERFACE_NAME')
    STORAGE_ACCOUNT_NAME = getenv('OPWEN_REMOTE_ACCOUNT_NAME')
    STORAGE_ACCOUNT_KEY = getenv('OPWEN_REMOTE_ACCOUNT_KEY')
    STORAGE_CONTAINER = 'opwen'
    STORAGE_UPLOAD_PATH = '{}/from_opwen/%Y-%m-%d_%H-%M.gz'.format(CLIENT_NAME)
    STORAGE_DOWNLOAD_PATH = '{}/to_opwen/new.gz'.format(CLIENT_NAME)
