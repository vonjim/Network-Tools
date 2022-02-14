import networktools

switchIP = 240
target = open('router_ips', 'w')

with open('switch_ips') as f:
	for router_ip in f.readlines():
		j = router_ip.split('.')[:-1]
		while True:
			j.append(str(switchIP))
			if networktools.ping('.'.join(j)):
				switchIP = 240
				break
			else:
				target.write(str('.'.join(j)) + '\n')
				j.pop()
				switchIP += 1


target.close()




