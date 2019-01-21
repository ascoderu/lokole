from pathlib import Path
from subprocess import check_call  # nosec
from subprocess import check_output  # nosec


def _check_process_output(command):
    return check_output(command, shell=True)  # nosec


def _find_device(stdout: bytes, device_id: str):
    for line in stdout.splitlines():
        line = line.decode('utf-8')
        if 'Huawei' not in line:
            continue
        if device_id in line:
            return True
    return False


def modem_is_plugged(modem=None):
    result = _check_process_output(['/usr/bin/lsusb'])
    return _find_device(result, modem.uid if modem else '12d1:')


def modem_is_setup(target_mode: str):
    result = _check_process_output(['/usr/bin/lsusb'])
    return _find_device(result, '12d1:{}'.format(target_mode))


def setup_modem(config: Path):
    check_call(['/usr/sbin/usb_modeswitch',
                '--config-file', str(config.absolute())], shell=True)  # nosec
