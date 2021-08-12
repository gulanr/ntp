from StateMachine import TestStand
from StateMachine import TestStandStates
import Model
import SM
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5 import QtWidgets
from UI import UI
from Log import Log
import threading
import Config
import time
from UI.Stylize import Stylize

class Presenter:

    ui: UI.UI = None
    model: Model.Model = None
    serial_monitor: SM.SerialMonitor = None
    test_stand: TestStand.TestStand = None
    test_stand_standby_state: TestStandStates.DemoStandbyState
    test_stand_idle_state: TestStandStates.DemoIdleState
    test_stand_auto_state: TestStandStates.DemoAutoState

    def __init__(self):
        pass
    
    def setup(self):
        
        # TODO: This isn't working in a for loop for some reason, might be because of the lambda expression? revisit
        self.ui.tabs[0].clicked.connect(lambda: self.tab_clicked(0))
        self.ui.tabs[1].clicked.connect(lambda: self.tab_clicked(1))
        self.ui.tabs[2].clicked.connect(lambda: self.tab_clicked(2))
        self.ui.tabs[3].clicked.connect(lambda: self.tab_clicked(3))
        self.ui.tabs[4].clicked.connect(lambda: self.tab_clicked(4))
        self.ui.tabs[5].clicked.connect(lambda: self.tab_clicked(5))

        # Setup
        self.ui.setup.manual_connect_button.clicked.connect(self.setup_manual_connect_clicked)

        # Abort
        self.ui.abort_tab.clicked.connect(self.abort_clicked)

        # Configuration
        self.ui.configuration.blue_lines_plus_button.clicked.connect(self.configuration_blue_lines_plus_clicked)
        self.ui.configuration.blue_lines_minus_button.clicked.connect(self.configuration_blue_lines_minus_clicked)

        self.ui.configuration.sequence_plus_button.clicked.connect(self.configuration_sequence_plus_clicked)
        self.ui.configuration.sequence_minus_button.clicked.connect(self.configuration_sequence_minus_clicked)

        self.ui.configuration.save_button.clicked.connect(self.configuration_save_clicked)


        # Run
        self.ui.run.load_button.clicked.connect(self.run_load_clicked)
        self.ui.run.pause_button.clicked.connect(self.run_paused_clicked)
        self.ui.run.start_button.clicked.connect(self.run_start_clicked)

        # Start UI Update Loop
        self.__start_ui_update_loop()

    def __start_ui_update_loop(self):
        self.ui_update_thread = UI.UpdateThread()
        self.number = 0
        self.ui_update_thread.set_max_frequency(0.5)
        self.ui_update_thread.update_signal.connect(self.on_ui_update)
        self.ui_update_thread.start()

    def on_ui_update(self):
        self.number += 1

        x, y = self.model.get_run_plot_data('Heater TC')
        self.ui.run.plot1.setData(x,y)
        x, y = self.model.get_run_plot_data('Tank Pressure')
        self.ui.run.plot2.setData(x,y)
        x, y = self.model.get_run_plot_data('Mass Flow')
        self.ui.run.plot3.setData(x,y)
        x, y = self.model.get_run_plot_data('Outlet Pressure')
        self.ui.run.plot4.setData(x,y)

        if(self.model.trial_is_running):
            self.ui.run.start_button.setText('Running Trial - ' + str(round(self.model.trial_time, 1)))

        if(self.model.daq_is_connected):
            self.ui.setup.daq_status_label.setText('Connected')
        else:
            self.ui.setup.daq_status_label.setText('Not Connected')

        if(self.model.controller_is_connected):
            self.ui.setup.controller_status_label.setText('Connected')
        else:
            self.ui.setup.controller_status_label.setText('Not Connected')


    def tab_clicked(self, tab_index):
        if(self.ui.current_tab == self.ui.tabs[tab_index]):
            return

        self.ui.set_current_tab(tab_index)

    # TODO: Define abort procedure
    def abort_clicked(self):
        # self.model.stop
        pass

# SETUP PAGE LOGIC

    def setup_manual_connect_clicked(self):
        print('presenter: setup_manual_connect_clicked: hit')   
        daq_port = self.ui.setup.daq_port_field.text()
        controller_port = self.ui.setup.controller_port_field.text()

        self.serial_monitor.connect_arduinos(daq_port, controller_port)


# CONFIGURATION PAGE LOGIC
    def configuration_blue_lines_plus_clicked(self):
        self.ui.configuration.add_row_to_blue_lines_table()
    def configuration_blue_lines_minus_clicked(self):
        self.ui.configuration.remove_row_from_blue_lines_table()
    
    def configuration_sequence_plus_clicked(self):
        self.ui.configuration.add_row_to_sequence_table()
    def configuration_sequence_minus_clicked(self):
        self.ui.configuration.remove_row_from_sequence_table()

    def configuration_clear_clicked(self):
        pass

    def configuration_save_clicked(self):
        self.config_validation_thread = Config.ValidationThread(self.ui)

        self.config_validation_thread.validation_message.connect(self.on_configuration_validation_message)
        self.config_validation_thread.validation_is_complete.connect(self.on_configuration_validation_is_complete)

        self.config_validation_thread.start()

    def on_configuration_validation_message(self, message):
        self.ui.configuration.set_status_text(message)

    def on_configuration_validation_is_complete(self, validation_was_successful):
        if(validation_was_successful):
            file_name = Config.get_save_file_name_from_user()

            if(file_name == ""):
                return

            trial_name = self.ui.configuration.trial_name_field.text()
            description = self.ui.configuration.description_field.toPlainText()
            blue_lines = self.ui.configuration.blue_lines_table
            test_sequence = self.ui.configuration.sequence_table
            
            Config.create_file(file_name, trial_name, description, blue_lines, test_sequence)

# RUN PAGE LOGIC
    def run_start_clicked(self):

        if(self.model.trial_is_paused):
            self.test_stand.switch_state(self.test_stand_auto_state)
            Stylize.set_start_button_active(self.ui.run.start_button, False)
            Stylize.set_pause_button_active(self.ui.run.pause_button, True) 
        else:
            if(not self.model.trial_is_running):
                self.test_stand.switch_state(self.test_stand_auto_state)
                Stylize.set_start_button_active(self.ui.run.start_button, False)
                Stylize.set_pause_button_active(self.ui.run.pause_button, True)  

        
    def run_paused_clicked(self):
        if(self.model.trial_is_running and not self.model.trial_is_paused):
            self.test_stand.switch_state(self.test_stand_idle_state)
            Stylize.set_start_button_active(self.ui.run.start_button, True)
            Stylize.set_pause_button_active(self.ui.run.pause_button, False)
            self.ui.run.start_button.setText('Resume Trial at ' + str(round(self.model.trial_time,1)))

    def run_load_clicked(self):
        file_name = Config.select_file()
        
        if(file_name == ''):
            return

        config: Config.Config = Config.open_file(file_name)
        
        self.ui.run.set_loaded_trial_text(config.trial_name)
        self.ui.run.set_start_button_active(True)
        self.ui.run.set_sequence_table(config)
