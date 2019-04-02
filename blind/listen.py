import broadlink
import time
import sys
import socket

class Command:
	def __init__(self, name, packet):
		self.packet = packet
		self.name = name

	def send(self, device):
		device.send_data(self.packet)

	def diff(self, other):
		if len(self.packet) != len(other.packet):
			return sys.maxint
		diff = 0
		for x, y in zip(self.packet, other.packet):
			x, y = ord(x), ord(y)
			if abs(x - y) > diff:
				diff = abs(x - y)
			#print "%02x %02x" % (x, y)
		return diff

def log(msg, newline=True):
	sys.stderr.write(msg)
	if newline:
		sys.stderr.write("\n")
	sys.stderr.flush()

def load(name, commandfile):
	with open(commandfile, "r") as fp:
		return Command(name, fp.read().strip().decode('hex'))

def listen(device):
	while True:
		device.enter_learning()
		time.sleep(2)
		packet = device.check_data()
		if packet is not None:
			log("Received packet (len: %d)" % len(packet))
			break
	return packet

def connect():
	log("Connecting...", newline=False)
	attempt = 1
	max_attempts = 5
	try:
		devices = broadlink.discover(timeout=5)
		assert len(devices) == 1
		device = devices[0]
		assert device.auth()
	except:
		log("Error connecting - attempt %d/%d" % (attempt, max_attempts))
		if attempt >= max_attempts:
			raise
		attempt += 1
	log("OK")
	return device

def compare_signals(first, second):
	if len(first) != len(second):
		return sys.maxint
	diff = 0
	for x, y in zip(first, second):
		x, y = ord(x), ord(y)
		if abs(x - y) > diff:
			diff = abs(x - y)
		#print "%02x %02x" % (x, y)
	return diff

"""
power_on = load("power_on.cmd")
start = load("start.cmd")
stop = load("stop.cmd")
print compare_signals(power_on, start)
print compare_signals(start, stop)
print compare_signals(power_on, stop)

sys.exit("Done")
"""

device = connect()

projector_on = load("Projector on", "start.cmd")
projector_off = load("Projector off", "stop.cmd")
blind_up = load("Blind up", "up.cmd")
blind_down = load("Blind down", "down.cmd")

commands = {
	"projector start": (projector_on, blind_down),
	"projector stop": (projector_off, blind_up),
	"projector power down": (projector_off, projector_off)
}

while True:
	log("Listening...")
	retries = 0
	while retries < 5:
		try:
			data = Command("data", listen(device))
			break
		except socket.timeout:
			log("Timeout while listening - reconnecting...")
			device = connect
			retries += 1
			if retries >= 5:
				raise
	handled = 0
	diffs = []
	for name, (match, output) in commands.iteritems():
		diff = data.diff(match)
		if diff < 4:
			log("Received command '%s' - sending response '%s'" % (match.name, output.name))
			# send twice, just in case the first one doesn't work
			output.send(device)
			output.send(device)
			device = connect()
			handled += 1
		else:
			diffs.append(diff)
	if handled == 0:
		log("Ignoring signal (diffs: %s)" % diffs)

