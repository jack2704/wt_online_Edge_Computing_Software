from PFTL import ur
from PFTL.Model.base_daq import DAQBase
from PFTL.Controller.pftl_daq import Device


class AnalogDaq(DAQBase):
    def __init__(self, port):
        self.port = port
        self.driver = Device(self.port)

    def initialize(self):
        self.driver.initialize()
        self.set_voltage(0, ur('0V'))
        self.set_voltage(1, ur('0V'))

    def get_i2c(self, channel, gain):  # Umsetzen der Anfrage aus Controllerebene
        gain = int(gain)  # gain wird als string angenommen, muss zu int gemacht werden um keine Vektorprobleme zu bekommen
        temp_bit = int(self.driver.get_i2c_value(channel, gain))  # Umformen des Zurückgegebenen Wertes in Integer
        # Umrechnung des Wertes mit Messspitze einpflegen
        # Rückgabe des Wertes

        # dictionary mit maximalem Spannungsbereich und jeweiligem Least-size-bit
        gain_range = {  # gain in V und steps in mV siehe Tabelle in erstem Abschnitt
            0: [6.144, 0.187503],
            1: [4.096, 0.125002],
            2: [2.048, 0.062501],
            3: [1.024, 0.031250],
            4: [0.512, 0.015625],
            7: [0.256, 0.007813],
        }

        v_range = gain_range[gain][0]  # Value v_range wird zum passenden Key- gain (vom User fesetgelegt) ausgewählt
        steps = gain_range[gain][1]  # Value steps wird abhängig vom gain in variable steps gespeichert

        volt_analog = temp_bit * steps / 1000  # in Volt # berechnet analogen Voltwert gegenüber ausgewähltem gain mit zugehörigem step

        return volt_analog * ur('V')  # wichtig mit Einheit zu multiplizieren, wegen der saving Function, sonst wird ein dimensionsloser Wert übergeben, der dann in V umgerechnet werden muss-> nicht möglich

    def finalize(self):
        self.set_voltage(0, ur('0V'))
        self.set_voltage(1, ur('0V'))
        self.driver.finalize()

    def __str__(self):
        return "Analog Daq"