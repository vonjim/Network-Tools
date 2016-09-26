
import re
import sys
import os
from subprocess import call
from getpass import getpass
from networktools import ping


#   Run cmd and chdir to C:\Users\james.comiskey\PycharmProjects\Network
#	Run this from the command line : python WOL.py <SITECODE>


username = 'pry\jamescomiskey'
#print('\n\n{}\n\n* This will kill all MD3 applications running on the local desktop *\n\n{}\n\n'.format('*'*68, '*'*68))
#if input('## Are you sure you want to continue? (y/n): ').lower() == 'y' or 'yes' or 'ok':
#    pass
#else:
#    sys.exit(1)

passwd = getpass()

dhcpServer = {	'RING':['10.3.78.61', '10.3.78.0'],
                'MOON':['10.3.20.61', '10.3.20.0'],
                'HIGH':['10.203.18.61', '10.203.18.0'],
                'WERR':['10.3.82.61', '10.3.82.0'],
                'EIVA':['10.3.27.1', '10.3.27.0'],
                'ELST':['10.3.25.61', '10.3.25.0'],
                'SURR':['10.3.29.1', '10.3.29.0'],
                'HAWT':['10.3.26.1', '10.3.26.0'],
                'ELIZ':['10.8.14.61', '10.8.14.0'],
                'MARI':['10.8.6.61', '10.8.6.0'],
                'MODB':['10.8.8.61', '10.8.8.0'],
                'ROYA':['10.8.12.61', '10.8.12.0'],
                }

os.chdir('c:\\temp')

if sys.argv[1].upper() in dhcpServer:
    serverIP, subnet = dhcpServer.get(sys.argv[1].upper())
else:
    sys.exit('{}: is not a listed Sitecode.'.format(sys.argv[1].upper))

with open('{}-dhcp.txt'.format(sys.argv[1]), 'w') as fileWrite:
    print('## Extracting DHCP leases from {}'.format(serverIP))
    call(['netsh', '-r', serverIP, 'dhcp', 'server', 'scope', subnet, 'show', 'clients'], stdout=fileWrite)

with open('{}-dhcp.txt'.format(sys.argv[1]), 'r') as fileRead:
    dhcpOutput = fileRead.read()
    print('## Parsing MAC addresses from DHCP lease')
    matchMAC = re.compile(r'(\w{2})-(\w{2})-(\w{2})-(\w{2})-(\w{2})-(\w{2})')
    macAddresses = matchMAC.findall(dhcpOutput)

'''
    matchIP = re.compile(r'(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})')
    ipAddresses = matchIP.findall(dhcpOutput)

MD3string = """IMAGENAME eq MDW3.exe"""
for ipAddr in ipAddresses:
    if not ping('.'.join(ipAddr)):
        print('Sending taskkill signal to {}'.format('.'.join(ipAddr)))
        call(['taskkill', '/s', '.'.join(ipAddr), '/F', '/FI', MD3string])
'''

serverPath = r'\\{}\c$\Windows\System32\MC-WOL.bat'.format(serverIP)
with open(serverPath, 'w') as wol:
    print('## Creating MC-WOL.bat file in C:\Windows\System32')
    for mac in macAddresses:
        wol.write('mc-wol.exe\t' + ':'.join(mac) + '\n')

print('## Sending Wake On LAN packets')
call(['psexec', '\\\{}'.format(serverIP), '-u', username, '-p', passwd, 'MC-WOL.bat'])
