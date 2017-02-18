def upload(upload_info):
    """
    :type upload_info: dict

    """
    client_id = upload_info['client_id']
    resource_id = upload_info['resource_id']
    resource_type = upload_info['resource_type']

    raise NotImplementedError


def download(client_id):
    """
    :type client_id: str
    :rtype dict

    """
    return {
        'resource_id': None,
        'resource_type': None,
    }
