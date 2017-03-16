def upload(upload_info):
    """
    :type upload_info: dict

    """
    client_id = upload_info['client_id']  # noqa: F841
    resource_id = upload_info['resource_id']  # noqa: F841
    resource_type = upload_info['resource_type']  # noqa: F841

    raise NotImplementedError


def download(client_id):  # noqa: F841
    """
    :type client_id: str
    :rtype dict

    """
    return {
        'resource_id': None,
        'resource_type': None,
    }
