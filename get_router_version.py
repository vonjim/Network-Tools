#! /usr/bin/python


import telnetlib, time, re, getpass, threading, os 
from datetime import datetime

USER = 'james.comiskey'
PORT = 23
TIMEOUT = 6
READ_TIMEOUT = 6
PWD = getpass.getpass()

def parse_interface(show_int):
	bw = re.search(r'BW (\d+) K', show_int)
	duplex = re.search(r'(\w+).[Dd]uplex', show_int)
	return bw.group(1), duplex.group(1)

def parse_int_loopback(show_desc):
	show_desc = show_desc.split('-')[1]
	show_desc = show_desc.strip().split()
	return show_desc[0]

def parse_show_ip_interfaces(show_ip_int):
	interfaces = []
	show_ip_int = show_ip_int.strip().split('\n')[2:-1]
	show_ip_int.reverse()
	for interface in show_ip_int:
		interface = interface.split()
		if interface[1] != 'unassigned':
			interfaces.append((interface[0], interface[1]))
	return interfaces
	
def parse_version(show_ver):
	model = re.search(r'Cisco (CISCO)?(\d+)', show_ver)
	ver = re.search(r'Version (\S+)', show_ver)
	return model.group(2), ver.group(1).strip(',') 

def threadFunction(ip, target, error_file):
	
	try:
		tn = telnetlib.Telnet(ip, PORT, TIMEOUT)
	except:
		err = "Connection Error %s"%ip
		error_file.write(err)	

	try:
		tn.read_until("username: ", READ_TIMEOUT)
		tn.write(USER + "\n")
	except:
		err = ip + ':\tLogin Prompt Error\n'  
		error_file.write(err)

	try:
		tn.read_until("password: ", READ_TIMEOUT)
		tn.write(PWD + "\n")
	except:
		err = ip + ':\tPassword Prompt Error\n'
		error_file.write(err)

	time.sleep(2)
	hostname = tn.read_until("#").strip().split('#')[0]
	
	tn.write("terminal length 0\n")
	time.sleep(2)
	
	tn.write("show version\n")
	time.sleep(2)
	try:
		model, ver = parse_version(tn.read_very_eager())
	except:
		err = ip + ':\tShow Version Parse Error\n'
		model, ver = '0', '0'
		error_file.write(err)

	if '29' in model or '19' in model:
		tn.write("show int g0/1\n")
	elif '18' in model or '28' in model:
		tn.write("show int f0/1\n")	
	else:
		tn.write("show int f1\n")
	time.sleep(2)
	try:
		bw, duplex = parse_interface(tn.read_very_eager())
	except:
		err = ip + ':\tShow Interface Parse Error\n'
		bw, duplex = '0', '0'
		error_file.write(err)

	tn.write("show int l0 desc\n")
	time.sleep(2)
	try:
		desc = parse_int_loopback(tn.read_very_eager())
	except:
		err = ip + ':\tShow Interface Loopback Description Error\n'
		desc = '0'
		error_file.write(err)

	tn.write("show ip int brief\n")
	time.sleep(2)
	try:
		ipInterfaces = parse_show_ip_interfaces(tn.read_very_eager())
		for i in ipInterfaces:
			if 'Loopback' in i[0]:
				loopback = i[1]
				continue
			if '0/1' in i[0]:
				wanIP = i[1]
				continue
			elif 'NVI0' in i[0]:
				wanIP = i[1]
		ipInterfaces.pop(0)
		ipInterfaces.pop(0)
	except:
		err = ip + ':\tShow IP int brief Parse Error\n'
		ipInterfaces = '0'
		loopback = '0'
		wanIP = '0'
		error_file.write(err)

	bwduplex = bw + '\\' + duplex
	sitecode = hostname[:-4]
		
	report = "%s,%s,%s,%s,%s,%s,%s,%s"%(sitecode, hostname, bwduplex, model, ver, loopback, wanIP, ipInterfaces)
	target.write(report)
	target.write("\n")
	tn.close()


if __name__ == "__main__":
	
	if not os.path.exists('./router_output'):
		os.mkdir('router_output')
	allThreads = []
	outputfile = 'router_output/router_output_' + datetime.now().strftime('%d%m%Y') + '.csv'
	with open(outputfile, 'w') as target:
		error_file = open('error_file', 'w')
		target.write('Site Code,Hostname,BW\\Duplex,Model,Version,Loopback IP,WAN IP,LAN IPs\n')
		with open('router_ips') as f:
			for ip in f:
				ip = ip.strip()
				singleThread = threading.Thread(target=threadFunction, args=(ip, target, error_file))
				allThreads.append(singleThread)
				singleThread.start()
			
			for singleThread in allThreads:
				singleThread.join()
			print 'Done'

	error_file.close()
