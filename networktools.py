import sys, re, subprocess

def validateip(ip_addr):
    '''	This checks if an IP address is valid

    Args:
        IP address to test using the subprocess.call module

    Returns:
        1 on success
        0 on failure
    '''

    ip_regex = r'(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})'
    if not re.match(ip_regex, ip_addr):
        return False

    result = re.findall(ip_regex, ip_addr)

    for first, second, third, fourth in result:
        if fourth == '255' or fourth == '0':
            return False
        if first == '10':
            return True
        elif first == '192' and second == '168':
            return True
        elif first == '172' and (int(second) >= 16 and int(second) <= 32):
            return True
        else:
            return False

def ping(ip_addr):
    '''	This checks if an IP address is up

    Args:
        IP address to test using the subprocess.call module

    Returns:
        0 on success
        1 on failure
    '''
    return subprocess.call(['ping', '-c', '1', ip_addr])


if __name__ == '__main__':
    print(__name__)
    ip_addr = '10.1.1.1'
    if not validateip(ip_addr):
        sys.exit('Invalid IP address {}'.format(ip_addr))
    if ping(ip_addr):
        sys.exit('Host {} down'.format(ip_addr))


