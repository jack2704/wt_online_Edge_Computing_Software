import serial
from time import sleep


class Device():
    DEFAULTS = {'write_termination': '\n',
                'read_termination': '\n',
                'encoding': 'ascii',
                'baudrate': 9600,
                'read_timeout': 1,
                'write_timeout': 1,
                }

    def __init__(self, port): # instantiation of the class to create an object
        self.port = port
        self.rsc = None
        self.serial_number = None

    def initialize(self):
        self.rsc = serial.Serial(port=self.port,
                                 baudrate=self.DEFAULTS['baudrate'],
                                 timeout=self.DEFAULTS['read_timeout'],
                                 write_timeout=self.DEFAULTS['write_timeout'])
        sleep(1)
        # serial communication is stored as self.rsc in the class
        #sleep for 1sec to give time for the communication to be established

    def query(self, message):
        if self.rsc is None:
            return print('Device is not initialized')
        message = message + self.DEFAULTS ['write_termination'] #IDN
        message = message.encode(self.DEFAULTS['encoding'])#b'IDN\n'
        self.rsc.write(message)
        ans = self.rsc.readline() #b'General DAQ Device built by Uetke. v.1.2019\n'
        ans = ans.decode(self.DEFAULTS['encoding']).strip()
        return ans #'General DAQ Device built by Uetke. v.1.2019'

    def idn(self):
        return self.query('IDN')

    def get_i2c_value(self, channel, gain):  # Funktion zur Abfrage; Channel wählt den Channel, der am A/D-Wandler genutzt wird/
        # Gain beeinflusst die Auflösung
        message = 'I2C:{}:{}'.format(channel, gain)  # Zusammensetzen der Message
        ans = self.query(message)  # Nutzen der query-Funktion zur Kommunikation
        return ans  # Gibt den gemessenen Wert zurück

    def finalize(self):
        if self.rsc is not None:
            self.rsc.close()