#! /usr/bin/env python

import netsnmp
import re
import subprocess
import telnet_helper
import threading


def snmp_get(host_ip, mib_id):
    '''
        :param host_ip: IP address of the device to poll
        :param mib_id:  The SNMP MIB OID we want to poll
        :return:        The SNMP string returned as a list
    '''
    session = netsnmp.Session(DestHost=host_ip, Version=2, Community=PUBLIC)
    vars = netsnmp.VarList(netsnmp.Varbind(mib_id))
    return session.get(vars)[0]


def calcUptime(snmpUptime):
    '''
        Calculate the uptime in weeks, days, hours, minutes
        SNMP returns system uptime in 100ths of a second
        :param snmpUptime:  Receives uptime in 100ths of a second and breaks it down
                            into weeks, days, hours and minutes
        :return:            Uptime in weeks, days, hours and minutes
    '''

    secondsTotal = int(snmpUptime) / 100
    weeks = secondsTotal / WEEKS
    days = secondsTotal / DAYS - weeks * 7
    hours = secondsTotal / HOURS - (weeks * 7 * 24 + days * 24)
    mins = secondsTotal / MINS - (weeks * 7 * 24 * 60 + days * 24 * 60 + hours * 60)
    return weeks, days, hours, mins


def parseVersion(snmpVersion):
    '''
        Regex the SNMP result to get the version, train and feature from show version SNMP
        ;param snmpVersion: Takes a show_version string and uses regex to extract major minor IOS version
        :return:            Major, minor and feature numbers
    '''
    re_match = re.search(r'Version (\d+)\.(\d+)\((\d+)', snmpVersion)
    return (re_match.group(x) for x in range(1, 4))


def parseSystemID(snmpSystemID):
    '''
        Receives an OID which corresponds to the model of the cisco switch
        eg 1.3.6.1.4.1.9.1.1748 = ciscoWsC2960P48PstL
        These can be found here: http://snmp.cloudapps.cisco.com/Support/SNMP/do/BrowseOID.do?objectInput=
        1.3.6.1.4.1.9.1&translate=Translate&submitValue=SUBMIT&submitClicked=true
        :param snmpSystemID:
        :return: the human readable model eg 2960-48T and the OID eg 1748
    '''
    system_id = snmpSystemID.split('.').pop()
    return PLATFORM.get(system_id).get('platform'), system_id


def parseInterfaceID(snmpInterfaceID):
    '''
        This extracts the IfName.ifIndex ID from the string 'snmpInterfaceID' (and uses the system_id of the platform
        to only select the interfaces that are relevant, excluding vlans, loopbacks and NULLs
        IF-MIB::ifName.10001 = STRING: Fa0/1
        IF-MIB::ifName.10009 = STRING: Fa0/9
        :param snmpInterfaceID:     This is a tuple of (output, error)
        :return:                    List of ifIndex ID and interface ID tuples . eg [('100001', 'fa0/1'), ...]
    '''
    indexID_interface = []
    lines = snmpInterfaceID.strip().split('\n')
    for line in lines:
        if 'Fa' in line or 'Gi' in line:
            match = re.search(r'ifName\.(\d+) = STRING: (\S+)', line)
            indexID_interface.append((match.group(1), match.group(2)))
    return indexID_interface


def findInactivePorts(switch_ip, indexID_interface):
    '''
        A function to poll each fastethernet or gigabit interface on a switch for the number of octets sent.
        This is an indication on whether the switch port is active or inactive
        :param switch_ip:           IP address of the switch to pill
        :param indexID_interface:   The list of IndexID and interface tuples
        :return:                    List intrefaces whose octet byte count is 0
    '''
    inactive_ports = []
    for IndexID, interface in indexID_interface:
        output_octet_oid = OUTPUT_OCTET_OID + IndexID
        if snmp_get(switch_ip, output_octet_oid) == '0':
            inactive_ports.append(interface)
    return inactive_ports


def get_router_ip_address():
    return raw_input('Enter router IP address \n> ')



def start_telnet_session(router_ip_address):
    return telnet_helper.create_telnet_session(router_ip_address)


def parse_wan_ip_address(show_interface_output):
    ip_regex = r'(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})/(\d{1,2})'
    return re.findall(ip_regex, show_interface_output)


def show_wan_interfaces(telnet_session=None):
    if not telnet_session:
        telnet_session = start_telnet_session(get_router_ip_address())

    telnet_helper.show_interface(telnet_session)
    wan_ip_address = parse_wan_ip_address(telnet_session.read_very_eager())
    print('WAN CE Interface: {}'.format(wan_ip_address))

def show_circuit_id():
    pass


def show_free_switchports():
    pass


def show_interface_bandwidth():
    pass


def menu():
    menu_options = {'1': show_wan_interfaces, '2': show_circuit_id, '3': show_free_switchports,
                    '4': show_interface_bandwidth, '0': sys.exit('Goodbye')}
    subprocess.call('clear', shell=True)
    print(BANNER)
    if menu_options.get(raw_input('\n> ')):
        pass
    else:
        menu()


MINS = 60
HOURS = 60*MINS
DAYS = 24*HOURS
WEEKS = 7*DAYS
VERSION_OID = '.1.3.6.1.2.1.1.1.0'
UPTIME_OID = '.1.3.6.1.2.1.1.3.0'
SYSTEM_OID = '.1.3.6.1.2.1.1.2.0'
INTERFACE_OID = '.1.3.6.1.2.1.31.1.1.1.1'
OUTPUT_OCTET_OID = '.1.3.6.1.2.1.2.2.1.16.'
PUBLIC = 'Pr1maryRO'
PLATFORM = {'717': {'platform': '2960-48TT'},
            '716': {'platform': '2960-24TT'},
            '695': {'platform': '2960-48'},
            '696': {'platform': '2960G-24'},
            '697': {'platform': '2960G-48'},
            '324': {'platform': '2950-24'},
            '559': {'platform': '2950-24T'},
            '1751': {'platform': '2960P-48TC'},
            '1208': {'platform': '29XX-Stack'},
            '950': {'platform': '2960-24PC'},
            '359': {'platform': '2950T-24'},
            '1748': {'platform': '2960-48PST'},
            '951': {'platform': '2960-24LT'}}
BANNER = '''
    +-----------------------------------------------------------+
    |                                                           |
    |            MCIT Network Information Utility               |
    |                                                           |
    |            1) Show WAN interface IP addresses             |
    |            2) Show Optus WAN circuit ID                   |
    |            3) Show free switch ports at a site            |
    |            4) Show interface bandwidth at a site          |
    |            0) Exit                                        |
    |                                                           |
    +-----------------------------------------------------------+
    '''








def runOnInputFile(infile):
    from datetime import date
    allThreads = []		# a list of all the Thread objects
    f = open(infile, 'r')
    with open('switch_info_' + str(date.today()), 'w') as outfile:
        outfile.write('%-16s%-35s%-12s%-13s%-20s\n' % ('IP Address', 'Uptime', 'Version', 'Platform', 'Inactive Ports'))
        for switch_ip in f.readlines():
            switch_ip = switch_ip.strip()
	    singleThread = threading.Thread(target=threadFunction, args=(switch_ip, outfile))
            allThreads.append(singleThread)
	    singleThread.start()
	for singleThread in allThreads:
	    singleThread.join()
    f.close()


def threadFunction(switch_ip, outfile):
	major_version, minor_version, train = parseVersion(snmp_get(switch_ip, VERSION_OID))
	weeks, days, hours, mins = calcUptime(snmp_get(switch_ip, UPTIME_OID))
	platform, system_oid = parseSystemID(snmp_get(switch_ip, SYSTEM_OID))
	process_output = subprocess.Popen(('snmpwalk -v 2c -c {} {} {}').format(PUBLIC, switch_ip, INTERFACE_OID),
									  stdout=subprocess.PIPE, shell=True)
	(output, errors) = process_output.communicate()
	inactivePorts = findInactivePorts(switch_ip, parseInterfaceID(output))
	outfile.write('%-15s%2s Weeks %s Days %-2s Hours %-2s Mins %5s.%s(%s%-4s %-13s%-20s\n'
				  % (switch_ip.strip(), weeks, days, hours, mins, major_version, minor_version, train, ')',
					 platform, inactivePorts))



if __name__ == '__main__':
    runOnInputFile()



'''
    while True:
        choice = raw_input('> ')
        try:
            MENU.get(choice)



try:
    infile = open(argv[1]).read()


'''
