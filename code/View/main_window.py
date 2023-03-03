import os

import pandas as pd
import yaml
import pyqtgraph as pg
import tkinter as tk
from tkinter import filedialog
import threading
from PyQt5 import uic
from PyQt5.QtCore import QTimer
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QMainWindow,
                             QPushButton,
                             QWidget,
                             QHBoxLayout,
                             QVBoxLayout,
                             QFileDialog,
                             QLabel, QMessageBox, QComboBox
                             )
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QPixmap
from PyQt5 import QtCore
import pint


class MainWindow(QMainWindow):
    def __init__(self, experiment=None):
        super().__init__()
        self.file_path = None
        base_dir = os.path.dirname(os.path.abspath(__file__))

        ui_file = os.path.join(base_dir, 'GUI', 'main_window_i2c.ui')  # Angepasst auf neuen Namen der GUI-Datei
        uic.loadUi(ui_file, self)

        self.experiment = experiment
        # Die Eingabefelder wurden umbenannt und Angepasst
        self.gain_line.setText(str(self.experiment.config['Scan']['gain']))
        self.duration_line.setText(self.experiment.config['Scan']['scan_duration'])
        self.channel_line.setText(str(self.experiment.config['Scan']['channel']))
        self.delay_line.setText(self.experiment.config['Scan']['delay'])

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.timeout.connect(self.update_gui)
        self.timer.start(50)    # intervall in ms

        self.plot_widget1 = pg.PlotWidget(title="Plotting Volt vs time")  # Überschift des Diagramms
        self.plot1 = self.plot_widget1.plot([0], [0])
        self.plot_widget1.setLabel(axis='bottom', text='time', units='sec', unitPrefix=None)
        self.plot_widget1.setLabel(axis='left', text='Volt through Diamond', units='V', unitPrefix=None) # units hinzugefügt. Achsenskalierung automatisch mit angenehmeren Werten, statt Volt= 0.003 werden mV = 3 angezeigt
        layout = self.central_widget.layout()
        layout.addWidget(self.plot_widget1)

        self.plot_widget2 = pg.PlotWidget(title="Plotting Temperature vs time")  # Überschift des Diagramms
        self.plot2 = self.plot_widget2.plot([0], [0])
        self.plot_widget2.setLabel(axis='bottom', text='time', units='sec', unitPrefix=None)
        self.plot_widget2.setLabel(axis='left', text='Temperature', units='°C', unitPrefix=None) # units hinzugefügt. Achsenskalierung automatisch mit angenehmeren Werten, statt Volt= 0.003 werden mV = 3 angezeigt
        layout = self.central_widget.layout()
        layout.addWidget(self.plot_widget2)

        self.channel_line.setToolTip('Über Channel kann der Eingang am A/D-Wandler ausgewählt werden.\n Auswahloptionen: 0-3')
        self.duration_line.setToolTip('Duration gibt die Maximaldauer des Scans an.\n Mit Ablauf der Duration wird der Scan automatisch beendet.\n Der Scann kan auch zu einem beliebigen Zeitpunkt über Stop beendet werden.')
        self.gain_line.setToolTip('Über Gain kann die maximal messbare Spannung angepasst werden.\n Auswahloptionen: 0, 1, 2, 4, 8, 16.\n Beeinflusst Messauflösung und Messbereich.')
        self.delay_line.setToolTip('Delay bestimmt die Wartezeit,\n bis ein neuer Messwert aufgenommen wird.')

        self.start_button.clicked.connect(self.start_scan)
        self.stop_button.clicked.connect(self.stop_scan)
        self.actionSave.triggered.connect(self.experiment.save_data) #connect the save action to the experiment's save_data method
        self.actionSave_As.triggered.connect(self.choose_folder)
        self.pushButton.clicked.connect(self.transform_to_zeit_temp) #button to transform the graph to temperature and time
        #self.viewButton.clicked.connect(self.exp_view_results)
        self.setWindowTitle('Temperaturmessung Window')  #Set Titel
        self.setWindowIcon(QIcon('technical-university-of-berlin-logo.png')) # Open/insert picture TU LOGO

        #self.pushButton_2.clicked.connect(self.select_file)

        #path = r"C:\Users\kalan\anaconda3\envs\kal\Project_2\Auswertung(lookuptables)"
        #files = os.listdir(path)
        #self.comboBox.addItems(files) # adding items to the drop-down from the list called files which is defined as directory Auswertung(lookuptables)
        #self.comboBox.currentIndexChanged.connect(self.load_file)
        '''The currentIndexChanged.connect() method is being used to connect the combobox's currentIndexChanged signal to a function called load_file(). 
        This means that when the selected item in the combobox changes, the load_file() function will be called.'''

        self.plot_widget1.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.plot_widget1.customContextMenuRequested.connect(self.show_context_menu)
        self.export_action1 = QtWidgets.QAction("Export to Excel", self)
        self.export_action1.triggered.connect(self.export_to_excel1)

        self.plot_widget2.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.plot_widget2.customContextMenuRequested.connect(self.show_context_menu)
        self.export_action2 = QtWidgets.QAction("Export to Excel", self)
        self.export_action2.triggered.connect(self.export_to_excel2)

    def select_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename()
        # stores the file path in a configuration file
        configuration = {"file_path": file_path}
        with open("configuration.yml", "w") as f:
            yaml.dump(configuration, f)
        if not file_path or file_path == "":
            return None
        self.file_path = file_path
        return self.file_path

    def select_file_thread(self):
        while True:
            file_path = self.select_file()
            if file_path is not None:
                self.file_path = file_path
                break

    def start_scan(self): # Die Felder der neue GUI wurden implementiert
        self.timer.start(50)
        # Angepasst auf neue Bezeichungen in der GUI
        duration = self.duration_line.text()
        gain = self.gain_line.text()
        channel = int(self.channel_line.text())
        delay = self.delay_line.text()

        self.experiment.config['Scan'].update(
            {'scan_duration': duration,
             'channel': channel,
             'gain': gain,
             'delay': delay}
        )

        self.experiment.start_scan()
        #print('Scan Started')
        self.file_path = None

    def transform_to_zeit_temp(self):  # Die Felder der neue GUI wurden implementiert
        self.timer.stop()
        t, b = self.transform_test()
        self.plot2.setData(t, b)
        self.plot_widget2.setLabel(axis='bottom', text='Scan time in sec', units='sec', unitPrefix=None)
        self.plot_widget2.setLabel(axis='left', text='Temperature', units='°C', unitPrefix=None)  # units hinzugefügt. Achsenskalierung automatisch mit angenehmeren Werten, statt Volt= 0.003 werden mV = 3 angezeigt

    #def exp_view_results(self):
        #self.timer.stop()
        #self.plot1.setData(self.experiment.scan_time, self.experiment.scan_data)
        #self.plot_widget1.setLabel(axis='bottom', text='time', units='sec', unitPrefix=None)
        #self.plot_widget1.setLabel(axis='left', text='Volt through Diamond', units='V', unitPrefix=None)

    def stop_scan(self):
        self.experiment.stop_scan()
        #print('Scan Stopped')

    def update_plot(self):
        self.plot1.setData(self.experiment.scan_time, self.experiment.scan_data)  #genutzte Arrays angepasst

    def update_gui(self):
        if self.experiment.is_running:
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.pushButton.setEnabled(False)
        else:
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.pushButton.setEnabled(True)

    def transform_test(self):

        import pandas as pd
        import numpy as np
        import matplotlib.pyplot as plt
        from scipy.interpolate import interp1d

        self.select_file()
        if self.file_path is None:
            self.select_file_thread()
        #print(self.file_path)
        #self.on_combobox_selection_changed(self.comboBox.currentIndex()) #calling the "on_combobox_selection_changed" function and passing the current index of the comboBox as an argument.

        #if self.file_path is None:
            #self.select_file()

        df = pd.read_csv('../Examples/experiment_results/latest/data.dat',
                         sep="\s+",
                         # skiprows=1,
                         usecols=[0, 1],
                         names=['Scan time in sec', 'Scan Data in Volt'])
        #print(df)

        # exp data
        list3 = df["Scan Data in Volt"].to_list()  #list of strings
        list4 = df["Scan time in sec"].to_list()
        # print(list4)
        j = 0
        m = 0
        t = []
        z = []
        for j in range(len(list3[1:])):
            z.append(float(list3[1:][j]))
            # print(j, z)
        # print(z)
        for m in range(len(list4[1:])):
            t.append(float(list4[1:][m]))
        #print(t)

        #excel_lookup_table = pd.read_excel(r'C:\Users\kalan\anaconda3\envs\kal\Project_2\Auswertung BoDoDi Messung 20221116_v01_ThK.xlsx')
        #excel_path = self.file_path
        #print(excel_path)
        excel_lookup_table = pd.read_excel(self.file_path)
        #print(self.file_path)
        # print(excel_lookup_table)
        # excel_lookup_table = excel_lookup_table.apply(pd.to_numeric, errors='coerce')
        # print(excel_lookup_table)

        x = excel_lookup_table.iloc[:, 1].to_list() # adding all the rows of the third column to list y
        #print(x)
        y = excel_lookup_table.iloc[:, 0].to_list() # adding all the rows of the first column to list y
        #print(y)

        # 'linear','nearest', 'zero', 'slinear', 'quadratic', 'cubic'
        # bounds_error: If True, a ValueError is raised any time interpolation is attempted on a value outside of the range of x (where extrapolation is necessary). If False, out of bounds values are assigned fill_value. By default, an error is raised unless fill_value="extrapolate".
        #f = interp1d(x, y, bounds_error=None)
        predict_linear = interp1d(x, y, bounds_error=False, kind='linear', fill_value="extrapolate")  # f
        # predict_quadratic = interp1d(x, y, bounds_error=False, kind='quadratic', fill_value="extrapolate") #f2

        # X = np.linspace(-0.005, 0.027, 10000, endpoint=True)
        # X = np.linspace(0.05, 0.08, 10000, endpoint=True)
        X = np.linspace(-0.005, 0.08, 10000, endpoint=True)
        Y_linear = np.array([predict_linear(x) for x in X])  # f(X)
        # Y_quadratic = np.array([predict_quadratic(x) for x in X])  # f2(X)
        # plt.plot(x, y, "o:", X, Y_linear, '-', X, Y_quadratic, '--')
        plt.plot(x, y, "o:", X, Y_linear, '-')
        #plt.show()

        k = 0
        a = []
        b = []
        for k in z:
            # print(f"X:{k}, Y:{predict_quadratic(k)}")
            a.append(k)
            b.append(float(str(predict_linear(k))))
        #print(a)
        #print(b)

        return t, b

    #def excel_lookup_table(self):
        #import os
        #os.startfile(r'C:\Users\kalan\anaconda3\envs\kal\Project_2\Auswertung BoDoDi Messung 20221116_v01_ThK.xlsx')

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Choose Folder')
        self.experiment.config['Saving']['folder'] = folder
        self.experiment.save_data()
        # choosing a folder to save data when a folder is chosen from SaveAs

    def show_context_menu(self, pos):
        sender = self.sender()
        if sender == self.plot_widget1:
            export_action = self.export_action1
        elif sender == self.plot_widget2:
            export_action = self.export_action2
        else:
            return
        menu = QtWidgets.QMenu()
        menu.addAction(export_action)
        menu.exec_(sender.mapToGlobal(pos))

    def export_to_excel1(self):
        import matplotlib.pyplot as plt
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_name, _ = QFileDialog.getSaveFileName(self, "Export to Excel", "", "Excel Files (*.xlsx);;All Files (*)",
                                                   options=options)
        if file_name:
            # Get the data from the plot
            data = self.plot1.getData()
            # Create a dataframe from the data
            df = pd.DataFrame(data)
            df = df.T
            df = df.rename(columns={0: "time", 1: "Volt through Diamond"})
            # Write the dataframe to the excel file
            df.to_excel(file_name, index=False)
            QMessageBox.information(self, "Info", "Data exported to excel successfully.")

    def export_to_excel2(self):
        import matplotlib.pyplot as plt
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_name, _ = QFileDialog.getSaveFileName(self, "Export to Excel", "", "Excel Files (*.xlsx);;All Files (*)",
                                                   options=options)
        if file_name:
            # Get the data from the plot
            data = self.plot2.getData()
            df = pd.DataFrame(data)
            df = df.T
            df = df.rename(columns={0: "time", 1: "Temperature"})
            # Write the dataframe to the excel file
            df.to_excel(file_name, index=False)
            QMessageBox.information(self, "Info", "Data exported to excel successfully.")