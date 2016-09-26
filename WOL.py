
import re
import sys
import os
from subprocess import call
from getpass import getpass
from networktools import ping


#	Run this from the command line : python WOL.py <SITECODE>


username = 'your_username'

passwd = getpass()

dhcpServer = {	'SITE-ID1':['10.1.2.1', '10.1.2.0'],
                'SITE-ID2':['RemoteServerIPAddress', 'RemoteSubnet'],
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


serverPath = r'\\{}\c$\Windows\System32\MC-WOL.bat'.format(serverIP)
with open(serverPath, 'w') as wol:
    print('## Creating MC-WOL.bat file in C:\Windows\System32')
    for mac in macAddresses:
        wol.write('mc-wol.exe\t' + ':'.join(mac) + '\n')

print('## Sending Wake On LAN packets')
call(['psexec', '\\\{}'.format(serverIP), '-u', username, '-p', passwd, 'MC-WOL.bat'])
