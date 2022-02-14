import telnetlib, time, re, getpass

def parse_interface(show_int):
	bw = re.search(r'BW (\d+) K', show_int)
	return bw.group(1)


def parse_int_loopback(show_desc):
	show_desc = show_desc.split('-')[1]
	show_desc = show_desc.strip().split()
	return show_desc[0]


def parse_version(show_ver):
	model = re.search(r'Cisco (CISCO)?(\d+)', show_ver)
	ver = re.search(r'Version (\S+)', show_ver)
	return model.group(2), ver.group(1).strip(',')


def show_interface(tn_session):
    tn_session.write("show version\n")
    time.sleep(1)
    model, ver = parse_version(tn_session.read_very_eager())

    if '29' in model or '19' in model:
        tn_session.write("show int g0/1\n")
    elif '18' in model or '28' in model:
        tn_session.write("show int f0/1\n")
    else:
        tn_session.write("show int f1\n")

    time.sleep(1)


def show_bandwidth(tn_session):
    show_interface(tn_session)
    return parse_interface(tn_session.read_very_eager())


def get_interface_desc(tn_session):
    tn_session.write("show int l0 desc\n")
    time.sleep(1)
    return parse_int_loopback(tn.read_very_eager())


def create_telnet_session(ip_address):
	user = 'james.comiskey'
	PORT = 23
	TIMEOUT = 6
	READ_TIMEOUT = 6
	pwd = getpass.getpass()
	tn = telnetlib.Telnet(ip_address, PORT, TIMEOUT)
	tn.read_until("username: ", READ_TIMEOUT)
	tn.write(user + "\n")
	tn.read_until("password: ", READ_TIMEOUT)
	tn.write(pwd + "\n")
	time.sleep(1)
	tn.write("terminal length 0\n")

	return tn



