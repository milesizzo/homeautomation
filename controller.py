import socket
import re
import urllib2
import httplib
import subprocess

class Receiver:
    def __init__(self, socket_path="/var/run/lirc/lircd"):
        self.socket_path = socket_path

    def start(self):
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


class Command(object):
    def __init__(self, ir_commands):
        self.ir_commands = ir_commands

    def process(self, command):
        if command not in self.ir_commands:
            return False
        return self._process(command)

    def _process(self, command):
        raise NotImplementedError


class HdmiSwitchCommand(Command):
    STATE_LISTEN, STATE_OUTPUT, STATE_INPUT = (0, 1, 2)

    def __init__(self, ip='192.168.1.145', inputs=8, outputs=8):
        super(HdmiSwitchCommand, self).__init__(set(['KEY_%d' % x for x in range(10)]))
        self.__ms = Pro2MatrixSwitch(ip, inputs=inputs, outputs=outputs)
        self.__state = HdmiSwitchCommand.STATE_LISTEN
        self.__data = None

    def _process(self, command):
        m = re.search(r'KEY_([0-9])$', command)
        if not m:
            self.__state = HdmiSwitchCommand.STATE_LISTEN
            return False
        val = int(m.group(1))
        if self.__state == HdmiSwitchCommand.STATE_LISTEN:
            if val == 0:
                self.__state = HdmiSwitchCommand.STATE_OUTPUT
        elif self.__state == HdmiSwitchCommand.STATE_OUTPUT:
            if val > 0 and val <= self.__ms.outputs:
                self.__state = HdmiSwitchCommand.STATE_INPUT
                self.__data = val
            else:
                self.__state = HdmiSwitchCommand.STATE_LISTEN
        elif self.__state == HdmiSwitchCommand.STATE_INPUT:
            if val > 0 and val <= self.__ms.inputs:
                self.__ms.set(self.__data, val)
            self.__state = HdmiSwitchCommand.STATE_LISTEN
        else:
            self.__state = HdmiSwitchCommand.STATE_LISTEN
        return True


class CECCommand(Command):
    def __init__(self):
        super(CECCommand, self).__init__({'BD5', 'BD6'})

    def _process(self, command):
        if command == 'BD5':
            print('Sending power-off over CEC')
            p1 = subprocess.Popen(["echo", "standby 0"], stdout=subprocess.PIPE)
            p2 = subprocess.Popen(["cec-client", "-s"], stdin=p1.stdout, stdout=subprocess.PIPE)
        elif command == 'BD6':
            print('Sending power-on over CEC')
            p1 = subprocess.Popen(["echo", "on 0"], stdout=subprocess.PIPE)
            p2 = subprocess.Popen(["cec-client", "-s"], stdin=p1.stdout, stdout=subprocess.PIPE)
        return True


class IRProcessor:
    def __init__(self, commands):
        self.commands = commands

    def run(self):
        receiver = Receiver()
        receiver.start()
        while True:
            keyname, updown = receiver.next_key()
            updown = int(updown)
            if updown == 0:
                for command in self.commands:
                    command.process(keyname)


if __name__ == '__main__':
    proc = IRProcessor([HdmiSwitchCommand(), CECCommand()])
    proc.run()

