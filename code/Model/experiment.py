import yaml
from time import sleep
import time as tm
import os
from datetime import datetime
import threading
from PFTL import ur
import numpy as np
import tracemalloc
import shutil
import pint
#from scipy.optimize import curve_fit
#from matplotlib import pyplot as plt


class Experiment:
    def __init__(self, config_file):
        self.config_file = config_file
        self.is_running = False  # Variable checkt, ob der Scan gerade läuft
        # Es ist sehr wichtig self.is.running in _init_ zu definieren, weil sonst das Program abstürzt beim ersten Scan
        # self.scan_range = np.array([0]) * ur('V')
        # self.scan_data = np.array([0]) * ur('V')

        self.scan_data = np.array([0]) * ur('V')  # Einheit in Volt anpassen, dabei darauf achten volt_analog im Analog_Daq mit V zu multiplizieren
        self.scan_time = np.array([0]) * ur('sec')  # Array zum Abspeichern der Zeitpunkte der Messung

    def load_config(self):  # hier in der Funktion brauchen wir erstmal keine Attribute für die Yaml Datei. großer Vorteil-> Allgemeingültig
        with open(self.config_file,'r') as f:  # am Ende des Codes, wird bei der Versuchsdurchführung der Name der Yaml Datei als Attribut in die Funktion eingegeben
            data = yaml.load(f, Loader=yaml.FullLoader)
        self.config = data

    def load_daq(self):
        name = self.config['DAQ']['name']
        port = self.config['DAQ']['port']

        if name == 'AnalogDaq':
            from PFTL.Model.analog_daq import AnalogDaq
            self.daq = AnalogDaq(port)
        else:
            raise Exception('The daq specified is not yet supported')

        self.daq.initialize()

    def do_scan(self):  # Angepasst für Messungen über I2C
        tracemalloc.start()

        if self.is_running:
            #print('Scan already running')
            return
        self.is_running = True
        duration = ur(self.config['Scan']['scan_duration']).m_as('sec')  # Scandauer aus Configfile laden
        delay = ur(self.config['Scan']['delay'])  # Wartezeit zwischen zwei Scans aus Configfile laden
        self.scan_time = np.zeros(0) * ur('sec')  # Erzeugen eines leeren Arrays für die Zeitpunkte, leere Arrays und das Anhängen der Werte umgeht, vorher die Anzahl an Messwerten kennen zu müssen
        self.scan_data = np.zeros(0)  # Erzeugen eines leeren Arrays für die Messdaten, !Einheit Anpassen, wenn im Controller hinterlegt!
        self.keep_running = True
        start_time = tm.time()  # Startzeit des Versuches bestimmen
        self.scan_time = np.append(self.scan_time, 0 * ur.second)  # Anhängen des ersten Messpunktes zum Zeitpunkt 0
        # für diesen array muss in analog.py int(gain) gesetzt werden. ansonsten läuft measured = self.daq.get_i2c nicht korrekt
        # denn self.scan_data append (0, none), so is die shape of x and y nicht gleich

        measured = self.daq.get_i2c(self.config['Scan']['channel'], self.config['Scan']['gain'])  # Abfrage an den Arduino für Messwert, mit Daten aus dem Configfile
        self.scan_data = np.append(self.scan_data, measured)  # Anhängen des ersten Messwertes an das Array
        tm.sleep(delay.m_as('s'))  # erste Wartezeit vor nächsten Messwert
        while tm.time() <= start_time + duration:  # Schleife für die restlichen Messwerte, nach dem oberem Schema
            if not self.keep_running:
                break
            start = tm.time()
            measured = self.daq.get_i2c(self.config['Scan']['channel'], self.config['Scan']['gain'])
            self.scan_data = np.append(self.scan_data, measured)
            self.scan_time = np.append(self.scan_time, (tm.time() - start_time) * ur.second)  # Bestimmen des Zeitpunktes der Messung in Sekunden seit Start
            # tm.sleep(delay.m_as('s'))
            sleep(delay.m_as('s') - (tm.time() - start))
            # sleep(delay.m_as('s') - (tm.time() - start) - 0.01)
        self.is_running = False
        self.save_draft()

        #print(tracemalloc.get_traced_memory())
        tracemalloc.stop()
        # output is given in form of (current, peak)
        # current memory is the memory the code is currently using#current memory ist der Speicher, den der Code derzeit verwendet.
        # peak memory is the maximum space the program used while executing.#peak memory ist der maximale Speicherplatz, den das Programm während der Ausführung verwendet.
    def save_data(self):
        data_folder = self.config['Saving']['folder']
        today_folder = f'{datetime.today():%Y-%m-%d}'
        saving_folder = os.path.join(data_folder, today_folder)
        if not os.path.isdir(saving_folder):
            os.makedirs(saving_folder)

        data = np.vstack([self.scan_time.m_as('second'), self.scan_data.m_as('V')]).T  # Angepasst auf die gemessenen Arrays, scan_data anpassen, wenn Cotroller mit Einheit arbeitet
        header = "Scan time in 'sec', Scan Data in 'Volt' "  # Überschrift angepasst, Anpassen für Dateneinheiten

        filename = self.config['Saving']['filename']
        base_name = filename.split('.')[0]
        ext = filename.split('.')[-1]
        i = 1
        while os.path.isfile(os.path.join(saving_folder, f'{base_name}_{i:04d}.{ext}')):
            i += 1
        data_file = os.path.join(saving_folder, f'{base_name}_{i:04d}.{ext}')
        metadata_file = os.path.join(saving_folder, f'{base_name}_{i:04d}_metadata.yml')
        np.savetxt(data_file, data, header=header)
        with open(metadata_file, 'w') as f:
            f.write(yaml.dump(self.config, default_flow_style=False))

    def save_draft(self):
        data_folder = self.config['Saving']['folder']
        saving_folder = os.path.join(data_folder, "latest")
        if not os.path.isdir(saving_folder):
            os.makedirs(saving_folder)

        data = np.vstack([self.scan_time.m_as('second'), self.scan_data.m_as('V')]).T  # Angepasst auf die gemessenen Arrays, scan_data anpassen, wenn Cotroller mit Einheit arbeitet
        header = "Scan time in 'sec', Scan Data in 'Volt' "  # Überschrift angepasst, Anpassen für Dateneinheiten

        filename = self.config['Saving']['filename']
        base_name = filename.split('.')[0]
        ext = filename.split('.')[-1]
        i = 1
        while os.path.isfile(os.path.join(saving_folder, f'{base_name}_{i:04d}.{ext}')):
            i += 1
        data_file = os.path.join(saving_folder, f'{base_name}.{ext}')
        metadata_file = os.path.join(saving_folder, f'{base_name}_metadata.yml')
        np.savetxt(data_file, data, header=header)
        with open(metadata_file, 'w') as f:
            f.write(yaml.dump(self.config, default_flow_style=False))


    def start_scan(self):
        self.scan_thread = threading.Thread(target=self.do_scan)
        self.scan_thread.start()


    def stop_scan(self):
        self.keep_running = False

    def finalize(self):
        #print('Finalizing Experiment')
        self.stop_scan()
        while self.is_running:
            sleep(.1)
        self.daq.finalize()

