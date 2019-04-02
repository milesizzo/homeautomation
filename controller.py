import socket
import re
import urllib2
import httplib

class Receiver:
    def __init__(self, socket_path="/var/run/lirc/lircd"):
        self.socket_path = socket_path

    def listen(self):
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.connect(self.socket_path)

    def next_key(self):
        while True:
            data = self.socket.recv(128)
            data = data.strip()
            if data:
                break
        print(data)
        words = data.split()
        return words[2], words[1]


class Pro2MatrixSwitch:
    def __init__(self, host, inputs=8, outputs=8):
        self.host = host
        self.inputs = inputs
        self.outputs = outputs
        assert inputs > 0 and inputs < 10 and outputs > 0 and outputs < 10

    def set(self, output, input):
        assert output > 0 and output <= self.outputs
        assert input > 0 and input <= self.inputs
        print('Switching output %d to input %d' % (output, input))
        try:
            urllib2.urlopen('http://%s/@PORT%d=%d.' % (self.host, output, input))
        except httplib.BadStatusLine:
            # we expect this
            pass


if __name__ == '__main__':
    STATE_LISTEN, STATE_OUTPUT, STATE_INPUT = (0, 1, 2)
    r = Receiver()
    r.listen()

    ms = Pro2MatrixSwitch('192.168.1.145', inputs=8, outputs=8)

    state = STATE_LISTEN
    data = None
    while True:
        keyname, updown = r.next_key()
        updown = int(updown)
        if updown == 0:
            if state == STATE_LISTEN:
                if keyname == 'KEY_0':
                    state = STATE_OUTPUT
            elif state == STATE_OUTPUT:
                m = re.search(r'KEY_([0-9])$', keyname)
                if m:
                    val = int(m.group(1))
                    if val > 0 and val <= ms.outputs:
                        state = STATE_INPUT
                        data = val
                    else:
                        state = STATE_LISTEN
                else:
                    state = STATE_LISTEN
            elif state == STATE_INPUT:
                m = re.search(r'KEY_([0-9])$', keyname)
                if m:
                    val = int(m.group(1))
                    if val > 0 and val <= ms.inputs:
                        output = data
                        input = val
                        ms.set(output, input)
                state = STATE_LISTEN
                data = None

        #print('%s (%s)' % (keyname, updown))

