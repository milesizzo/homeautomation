import samsungctl

if __name__ == '__main__':
	config = {
		'host': '192.168.1.146', #27
		'port': 55000,
		'method': 'legacy',
		'name': 'Downstairs',
		'description': '192.168.1.146', # IP
		#'id': '50:85:69:3a:6e:b0', # MAC
		'id': '50:85:69:4e:51:d0', # MAC
		'timeout': 0
	}
	with samsungctl.Remote(config) as remote:
		remote.control('KEY_POWERON')


