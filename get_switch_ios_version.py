#! /usr/bin/python
'''
A python script that takes each IP address from the ios_switch_ips file and using SNMP
extracts Total and Free size on flash.
Telnets to IP address and extracts boot system file if it is set. Save errors to error_file and logs output to ios_switch_output
'''

import netsnmp
import re
import os
import subprocess
import threading
import telnetlib
import getpass
import time
from datetime import datetime


FLASH_TOTAL_OID = '.1.3.6.1.4.1.9.9.10.1.1.4.1.1.4.1.1'
FLASH_FREE_OID = '.1.3.6.1.4.1.9.9.10.1.1.4.1.1.5.1.1'
PUBLIC = 'public'


USER = 'username'
PORT = 23
TIMEOUT = 6
READ_TIMEOUT = 6
PWD = getpass.getpass()



def snmp_get(host_ip, mib_id):
	'''
        :param host_ip: IP address of the device to poll
        :param mib_id:  The SNMP MIB OID we want to poll
        :return:        The SNMP string returned as a list
	'''
	session = netsnmp.Session(DestHost=host_ip, Version=2, Community=PUBLIC)
	vars = netsnmp.VarList(netsnmp.Varbind(mib_id))
	return session.get(vars)[0]


def parse_boot(show_boot):
	boot = re.search(r'BOOT path-list(\s+)?:(\s)?(\S+)?', show_boot)
	if not boot.group(3):
		return 'None'
	else:
		return boot.group(3)


def main():
	f = open('ios_switch_ips', 'r')
	if not os.path.exists('./ios_switch_output'):
		os.mkdir('ios_switch_output')
	allTheads = []
	outputfile = 'ios_switch_output/ios_switch_output_' + datetime.now().strftime('%Y%m%d') + '.csv'
	with open(outputfile, 'w') as outfile:
		error_file = open('error_file', 'w')
		outfile.write('%s,%s,%s,%s,%s\n' % ('IP Address', 'Total', 'Free', 'BOOT path-list'))
	        for switch_ip in f.readlines():
			switch_ip = switch_ip.strip()
			singleThread = threading.Thread(target=threadFunction, args=(switch_ip, outfile, error_file))
			allTheads.append(singleThread)
			singleThread.start()
		for singleThread in allTheads:
			singleThread.join()
	error_file.close()
	f.close()


def threadFunction(switch_ip, target, error_file):
	try:
		tn = telnetlib.Telnet(switch_ip, PORT, TIMEOUT)
	except:
		err = switch_ip + ":\tConnection Error\n"
		error_file.write(err)	
	try:
		tn.read_until("username: ", READ_TIMEOUT)
		tn.write(USER + "\n")
	except:
		err = switch_ip + ':\tLogin Prompt Error\n'  
		error_file.write(err)
	try:
		tn.read_until("password: ", READ_TIMEOUT)
		tn.write(PWD + "\n")
	except:
		err = switch_ip + ':\tPassword Prompt Error\n'
		error_file.write(err)
	time.sleep(2)
	tn.write("terminal length 0\n")
	time.sleep(1)
	tn.write("show boot\n")
	time.sleep(1)
	try:
		boot = parse_boot(tn.read_very_eager())
	except:
		err = switch_ip + ':\tShow Boot Parse Error\n'
		boot = 'Fail to get'
		error_file.write(err)
    	try:
		total_flash = int(snmp_get(switch_ip, FLASH_TOTAL_OID))/1024
		free_flash = int(snmp_get(switch_ip, FLASH_FREE_OID))/1024
    	except:
        	err = switch_ip + '\tOID Error\n'
		error_file.write(err)
	
	target.write('%s,%s,%s,%s,%s\n'% (switch_ip.strip(), total_flash, free_flash, boot))


if __name__ == "__main__":
        main()

