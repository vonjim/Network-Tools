#! /usr/bin/python
'''
A python script to Upgrade the IOS on a switch. IP addresses are gotten from ios_upgrade_ips.csv 
Steps are:
	1. Fork new process and telnet to IP address in column 1.
	2. Backup running config to tftp
	3. Copy IOS (column 2) from TFTP to flash.
	4. Verify IOS with md5 hash (column 3)
	5. Set boot system path to flash:/IOS (column 2)
	6. Save configuration
	7. Reboot Switch
	8. Confirm switch booted into new IOS.
	9. Delete old IOS
'''


import re
import os
import sys
import threading
from telnetlib import Telnet
import getpass
from networktools import ping
import time
from datetime import datetime


USER = 'username'	# Change this
PORT = 23
TIMEOUT = 6
READ_TIMEOUT = 6
COPY_TIMEOUT = 720
PWD = getpass.getpass()
TFTP_SERVER = '10.1.1.1'	# Change this

def main():
	f = open('ios_test_ips.csv', 'r')
	if not os.path.exists('./ios_upgrade_output'):
		os.mkdir('ios_upgrade_output')
	allTheads = []
	outputfile = 'ios_upgrade_output/ios_upgrade_output_' + datetime.now().strftime('%Y%m%d') + '.csv'
	with open(outputfile, 'w') as outfile:
		error_file = open('error_file', 'w')
		outfile.write('%s,%s,%s,%s,%s,\n' % ('IP Address', 'Copied', 'Verified', 'System Boot', 'Delete'))
		for line in f.readlines():
			# For each switch in file ios_upgrade_ips.csv, start new thread
			singleThread = threading.Thread(target=threadFunction, args=(line.strip(), outfile, error_file))
			allTheads.append(singleThread)
			singleThread.start()
		for singleThread in allTheads:
			singleThread.join()
	error_file.close()
	f.close()


def threadFunction(line, target, error_file):
	copied, verified, boot, deleted = ['No']*4
	verify_output = ''
	ping_coutner = 1
	switch_ip, new_ios, md5hash, old_ios_path = line.split(',')
	
	# Telnet to Switch 
	try:
		tn = Telnet(switch_ip, PORT, TIMEOUT)
	except:
		err = switch_ip + ":\tConnection Error\n"
		error_file.write(err)
		sys.exit(1)
	try:
		tn.read_until("username: ", READ_TIMEOUT)
		tn.write(USER + "\n")
	except:
		err = switch_ip + ':\tLogin Prompt Error\n'  
		error_file.write(err)
		sys.exit(1)
	try:
		tn.read_until("password: ", READ_TIMEOUT)
		tn.write(PWD + "\n")
	except:
		err = switch_ip + ':\tPassword Prompt Error\n'
		error_file.write(err)
		sys.exit(1)
	time.sleep(1)
	
	tn.write("terminal length 0\n")
	time.sleep(1)
	
	# Backup startup config
	tn.write("copy run tftp\n")
	time.sleep(1)
	tn.write(TFTP_SERVER + '\n')
	time.sleep(1)
	tn.write('\n')
	print switch_ip + ': Copying running config to tftp'
	time.sleep(5)
	
	# Copy IOS to flash
	tn.write("copy tftp flash\n")
	time.sleep(1)
	tn.write(TFTP_SERVER + '\n')
	time.sleep(1)
	tn.write(new_ios + '\n')
	time.sleep(1)
	tn.write(new_ios + '\n')
	print '{}: Copying IOS to flash'.format(switch_ip)
	time.sleep(1000)
	
	# Gather output from verify IOS with md5 hash. If Verified is not in output string, close telnet session and thread
	tn.write("verify /md5 flash:{} {}\n".format(new_ios, md5hash))
	print '{}: Verifying flash'.format(switch_ip)
	
	try:
		while True:
			verify_output += tn.read_some()
	except:
		pass
	
	if 'Verified' not in verify_output:
		err = switch_ip + ':\tFailed to verify IOS\n'
		error_file.write(err)
		tn.close()
		sys.exit(1)
	else:
		copied, verified = ['Yes']*2
	
	tn.write('conf t\n')
	time.sleep(1)
	tn.write('boot system flash:{}\n'.format(new_ios))
	print '{}: Configuring system boot path'.format(switch_ip)
	time.sleep(1)
	
	# Save running configuration to NVRAM
	tn.write('do write mem\n')
	print '{}: Writing to memory'.format(switch_ip)
	time.sleep(5)

	# Reboot Switch in 1 minute
	tn.write('do reload in 1\n')
	time.sleep(1)
	tn.write('\n')
	print '{}: Rebooting in 1 minute'.format(switch_ip)
	time.sleep(65)
	print '{}: Rebooting... '.format(switch_ip)
	tn.close()
	# Wait  minutes for switch to reboot before telneting onto switch
	time.sleep(300)
	
	while True:
		if ping(switch_ip) == 0:
			print switch_ip + ': System rebooted successfully'
			break
		else:
			ping_coutner += 1
			print switch_ip + ': System offline... # {}'.format(ping_coutner)
			time.sleep(30)
			if ping_coutner == 10: 
				err = switch_ip + ':\tSWITCH DOWN!!!!\n'
				error_file.write(err)
				sys.exit(1)
				break
	
	try:
		tn = Telnet(switch_ip, PORT, TIMEOUT)
	except:
		err = switch_ip + ":\tPost reboot connection error\n"
		error_file.write(err)
		sys.exit(1)
	try:
		tn.read_until("username: ", READ_TIMEOUT)
		tn.write(USER + "\n")
	except:
		err = switch_ip + ':\tPost reboot Login Prompt Error\n'  
		error_file.write(err)
		sys.exit(1)
	try:
		tn.read_until("password: ", READ_TIMEOUT)
		tn.write(PWD + "\n")
	except:
		err = switch_ip + ':\tPost reboot Password Prompt Error\n'
		error_file.write(err)
		sys.exit(1)	
	time.sleep(1)
	
	tn.write("terminal length 0\n")
	time.sleep(1)
	
		
	# Verify system booted into new IOS
	tn.write("show version\n")
	time.sleep(1)
	
	if 'System image file is \"flash:{}\"'.format(new_ios) in tn.read_very_eager():
		# Delete old IOS
		print switch_ip + ': Deleting OLD IOS'
		tn.write("delete /force {}\n".format(old_ios_path))
		time.sleep(5)
		boot, deleted = ['Yes']*2
	else:
		err = switch_ip + ':\tNew IOS not set in boot system path\n'
		error_file.write(err)
	
	tn.close()
	
	target.write('%s,%s,%s,%s,%s\n'% (switch_ip, copied, verified, boot, deleted))

	
if __name__ == "__main__":
        main()

