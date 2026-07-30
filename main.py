# This Python file uses the following encoding: ascii
import sys
import time
import pyvisa
import numpy as np
from pathlib import Path
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtCore import QObject, Signal, Property, Slot, QTimer, QAbstractListModel, Qt, QModelIndex, QByteArray

class HR320_Emulator:
    def __init__(self, gpib_address):
        self.gpib_address = gpib_address
        self.buffer = b'b'
        self.current_char = 'b'
        self.buffer_index = 0

        self.min_step = 0
        self.max_step = 13000

        self.is_spectrometer_booted = False
        self.is_motor_initialized = False
        self.is_motor_speed_set = False
        self.is_motor_busy = False

        self.motor_id = None
        self.min_motor_frequency = None
        self.max_motor_frequency = None
        self.motor_ramp_time = None

        self.current_motor_position = 0
        self.target_motor_position = 0

    def write_raw(self, query):
        query = query.decode('ascii')

        if(query == 'O2000\x00'):
            self.buffer = b'*'
        elif(query == ' '):
            if self.is_spectrometer_booted:
                self.buffer = b'F'
            else:
                self.buffer = b'B'
        elif(len(query) == 1):
            if query == 'A':
                self.is_motor_initialized = True
                self.buffer = b'o'
            elif query == 'E':
                if self.is_motor_initialized and self.is_motor_speed_set:
                    if self.is_motor_busy:
                        self.buffer = b'oq'
                    else:
                        self.buffer = b'oz'
                else:
                    self.buffer = b'b'
            elif query == 'K':
                self.buffer = b'o'
            elif query == 'L':
                if self.is_motor_initialized:
                    self.is_motor_busy = False
                    self.buffer = b'o'
                else:
                    self.buffer = b'b'
        else:
            cmd = query[0]
            parameters = query[1:]
            cleaned_parameters = parameters.rstrip()
            delimited_parameters = cleaned_parameters.split(',')

            if cmd == 'B':
                if self.is_motor_initialized:
                    self.is_motor_speed_set = True
                    self.motor_id = int(delimited_parameters[0])
                    self.min_motor_frequency = int(delimited_parameters[1])
                    self.max_motor_frequency = int(delimited_parameters[2])
                    self.motor_ramp_time = int(delimited_parameters[3])
                    self.buffer = b'o'
                else:
                    self.buffer = b'b'
            elif cmd == 'C':
                if self.is_motor_initialized and self.is_motor_speed_set:
                    self.motor_id = int(delimited_parameters[0])
                    self.buffer = ('o' + str(self.min_motor_frequency) + ',' + str(self.max_motor_frequency) +  ',' + str(self.motor_ramp_time) + '\r').encode('ascii')
                else:
                    self.buffer = b'b'
            elif cmd == 'F':
                if self.is_motor_initialized and self.is_motor_speed_set:
                    self.motor_id = int(delimited_parameters[0])
                    self.target_motor_position = self.current_motor_position + int(delimited_parameters[1])
                    self.is_motor_busy = True
                    self.buffer = b'o'
                else:
                    self.buffer = b'b'
            elif cmd == 'G':
                if self.is_motor_initialized:
                    self.motor_id = int(delimited_parameters[0])
                    self.current_motor_position = int(delimited_parameters[1])
                    self.target_motor_position = int(delimited_parameters[1])
                    self.buffer = b'o'
                else:
                    self.buffer = b'b'
            elif cmd == 'H':
                if self.is_motor_initialized:
                    self.motor_id = int(delimited_parameters[0])
                    if self.is_motor_busy:
                        if self.current_motor_position < self.target_motor_position:
                            self.current_motor_position += 20
                        elif self.current_motor_position > self.target_motor_position:
                            self.current_motor_position -= 20
                        else:
                            self.is_motor_busy = False
                    self.buffer = ('o' + str(self.current_motor_position) + '\r').encode('ascii')
                else:
                    self.buffer = b'b'

    def read_bytes(self, bytes, break_on_termchar = False):
        data = ''
        decoded_buffer = self.buffer.decode('ascii')
        for i in range(0, bytes):
            self.current_char = decoded_buffer[self.buffer_index]
            self.buffer_index += 1
            data += self.current_char

        if self.current_char == decoded_buffer[-1]:
            self.buffer = b'b'
            self.buffer_index = 0

        return data.encode('ascii')

class Instrument_Log(QAbstractListModel):

    TimestampRole = Qt.UserRole + 1
    InstrumentRole = Qt.UserRole + 2
    MessageRole = Qt.UserRole + 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self.log_queue = []

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0

        return len(self.log_queue)

    def data(self, index, role=Qt.DisplayRole):

        if not index.isValid():
            return None

        if index.row() >= len(self.log_queue):
            return None

        log_entry = self.log_queue[index.row()]

        if role == self.TimestampRole:
            return log_entry["timestamp"]
        elif role == self.InstrumentRole:
            return log_entry["instrument"]
        elif role == self.MessageRole:
            return log_entry["message"]
        else:
            return None

    def roleNames(self):
        return {self.TimestampRole: QByteArray(b"timestamp"), self.InstrumentRole: QByteArray(b"instrument"), self.MessageRole: QByteArray(b"message")}

    def append_log(self, instrument, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {"timestamp": timestamp, "instrument": instrument, "message": message}

        row = len(self.log_queue)
        self.beginInsertRows(QModelIndex(),row,row)
        self.log_queue.append(log_entry)
        self.endInsertRows()

    def clear(self):
        self.beginResetModel()
        self.log_queue.clear()
        self.endResetModel()

class HR320_Interface:
    def __init__(self, gpib_address):
        self.gpib_address = gpib_address

        self.motor_id = 0
        self.min_motor_frequency = 300 # Hz
        self.max_motor_frequency = 450 # Hz
        self.motor_ramp_time = 2000 # ms

        self.min_wavelength = 0 # Angstrom
        self.max_wavelength = 13000 # Angstrom
        self.steps_per_wavelength = 200 # steps/nm
        self.backlash_steps = 200

        self.focal_length = 320 # mm
        self.deviation_angle = 24 # degrees
        self.incline = 0 # degrees

        self.current_wavelength = None
        self.current_motor_position = None

        self.target_wavelength = None
        self.target_motor_position = None

        self.is_motor_moving_in_positive_direction = None

    def Convert_Wavelength_To_Step_Position(self, wavelength):
        return int(wavelength * self.steps_per_wavelength)

    def Convert_Step_Position_To_Wavelength(self, step_position):
        return step_position / self.steps_per_wavelength

    def Write_To_HR320(self, cmd, *params):
        query = cmd
        if params:
            query += ','.join(str(p) for p in params)
            query += '\r'
        print("Query: ", query)

        self.hr320.write_raw(query.encode('ascii'))
        return

    def Read_From_HR320(self, is_known_bytes, is_carriage_return_terminated, expected_bytes = None):
        if is_known_bytes == is_carriage_return_terminated:
            return "INPUT ERROR"

        try:
            if is_known_bytes:

                if expected_bytes <= 0:
                    return "INPUT ERROR"

                data = self.hr320.read_bytes(expected_bytes, break_on_termchar=False).decode('ascii')
                return data

            elif is_carriage_return_terminated:

                self.hr320.read_termination = '\r'
                data = self.hr320.read()

                return data

        except pyvisa.errors.VisaIOError:
            print("TIMEOUT ERROR")
            return "TIMEOUT ERROR"

    def Decrypt_Response(self, response):
        cleaned_response = response.rstrip()
        delimited_response = cleaned_response.split(',')

        confirmation_character = delimited_response[0][0]
        first_parameter = delimited_response[0][1:]

        decrypted_response = []
        decrypted_response.append(first_parameter)

        if len(delimited_response) > 1:
            for i in range(1, len(delimited_response)):
                decrypted_response.append(delimited_response[i])

        return confirmation_character, decrypted_response

    def Decrypt_Limit_Status(self, status):
        if type(status) != int:
            status = int(status)

        bit_status = {}
        for bit in range(8):
            current_status = bool(status & (1 << bit))
            bit_status[bit] = current_status
        return bit_status

    def Initialize_HR320(self):
        self.Connect_HR320()
        is_booted = self.Boot_HR320()
        is_motor_initialized = self.Initialize_Motor()
        is_motor_speed_set = self.Set_Motor_Speed()
        return is_booted, is_motor_initialized, is_motor_speed_set

    def Connect_HR320(self):
        if 'ASRL' in self.gpib_address:
            self.hr320 = HR320_Emulator(self.gpib_address)
        else:
            self.rm = pyvisa.ResourceManager()
            self.hr320 = self.rm.open_resource(self.gpib_address)

    def Boot_HR320(self):
        self.Write_To_HR320(' ')
        response = self.Read_From_HR320(is_known_bytes = True, is_carriage_return_terminated = False, expected_bytes = 1)
        print("Response:", response)
        print()
        if response == 'TIMEOUT ERROR':
            self.Reboot_HR320()
        elif response == 'B':
            self.Write_To_HR320('O2000\x00')
            time.sleep(0.5) # Must wait 500 ms to ensure answer comes back
            response = self.Read_From_HR320(is_known_bytes = True, is_carriage_return_terminated = False, expected_bytes = 1)
            print("Response:", response)
            print()
            if response == '*':
                return True
            elif response == 'b':
                return False
        elif response == 'F':
            return True

    def Reboot_HR320(self):
        self.hr320.write_raw(bytes([222]))
        time.sleep(0.2) # Must wait 200 ms to ensure spectrometer reboots
        self.Boot_HR320()

    def Initialize_Motor(self):
        self.Write_To_HR320('A')
        response = self.Read_From_HR320(is_known_bytes = True, is_carriage_return_terminated = False, expected_bytes = 1)
        print("Response:", response)
        print()
        if response == 'o':
            return True
        elif response == 'b':
            return False

    def Set_Motor_Speed(self):
        self.Write_To_HR320('B', self.motor_id, self.min_motor_frequency, self.max_motor_frequency, self.motor_ramp_time)
        response = self.Read_From_HR320(is_known_bytes = True, is_carriage_return_terminated = False, expected_bytes = 1)
        print("Response:", response)
        print()
        if response == 'o':
            is_motor_speed_read, min_motor_frequency, max_motor_frequency, motor_ramp_time = self.Read_Motor_Speed()
            if is_motor_speed_read:
                if (min_motor_frequency == self.min_motor_frequency) and (max_motor_frequency == self.max_motor_frequency) and (motor_ramp_time == self.motor_ramp_time):
                    print("Min motor frequency: ", self.min_motor_frequency)
                    print("Max motor frequency: ", self.max_motor_frequency)
                    print("Motor ramp time: ", self.motor_ramp_time)
                    return True
        elif response == 'b':
            return False

    def Read_Motor_Speed(self):
        self.Write_To_HR320('C', self.motor_id)
        response = self.Read_From_HR320(is_known_bytes = False, is_carriage_return_terminated = True)
        print("Response:", response)
        print()
        if response == 'b':
            return False, -1, -1, -1
        else:
            confirmation_character, decrypted_response = self.Decrypt_Response(response)
            if confirmation_character == 'o':
                min_motor_frequency = int(decrypted_response[0])
                max_motor_frequency = int(decrypted_response[1])
                motor_ramp_time = int(decrypted_response[2])

                return True, min_motor_frequency, max_motor_frequency, motor_ramp_time

    def Is_Motor_Busy(self):
        self.Write_To_HR320('E')
        response = self.Read_From_HR320(is_known_bytes = True, is_carriage_return_terminated = False, expected_bytes = 2)
        print("Response: ", response)

        if response == 'b':
            return False, -1
        else:
            confirmation_character, decrypted_response = self.Decrypt_Response(response)
            if confirmation_character == 'o':

                if decrypted_response[0] == 'q':
                    return True, True
                elif decrypted_response[0] == 'z':
                    return True, False

    def Move_Motor_Relative(self, target_wavelength):
        self.target_wavelength = target_wavelength
        steps_to_move = self.Convert_Wavelength_To_Step_Position(self.target_wavelength - self.current_wavelength)
        self.target_motor_position = self.current_motor_position + steps_to_move

        response = None
        if steps_to_move > 0:
            self.Write_To_HR320('F', self.motor_id, steps_to_move)
        elif steps_to_move < 0:
            self.Write_To_HR320('F', self.motor_id, steps_to_move - self.backlash_steps)
        else:
            return False

        response = self.Read_From_HR320(is_known_bytes = True, is_carriage_return_terminated = False, expected_bytes = 1)
        if response == 'b':
            return False
        elif response == 'o':
            if steps_to_move > 0:
                self.is_motor_moving_in_positive_direction = True
            else:
                self.is_motor_moving_in_positive_direction = False

            return True

    def Backlash_Correction(self):
        self.Write_To_HR320('F', self.motor_id, self.backlash_steps)
        response = self.Read_From_HR320(is_known_bytes = True, is_carriage_return_terminated = False, expected_bytes = 1)

        if response == 'b':
            return False
        elif response == 'o':
            self.is_motor_moving_in_positive_direction = True
            return True

    def Set_Motor_Position(self, current_wavelength):
        self.current_wavelength = current_wavelength
        self.current_motor_position = self.Convert_Wavelength_To_Step_Position(self.current_wavelength)

        self.Write_To_HR320('G', self.motor_id, self.current_motor_position)
        response = self.Read_From_HR320(is_known_bytes = True, is_carriage_return_terminated = False, expected_bytes = 1)

        if response == 'b':
            return False
        elif response == 'o':
            return True

    def Read_Motor_Position(self):
        self.Write_To_HR320('H', self.motor_id)
        response = self.Read_From_HR320(is_known_bytes = False, is_carriage_return_terminated = True)

        if response == 'b':
            return False, -1
        else:
            confirmation_character, decrypted_response = self.Decrypt_Response(response)

            if confirmation_character == 'o':
                self.current_motor_position = int(decrypted_response[0])
                self.current_wavelength = self.Convert_Step_Position_To_Wavelength(self.current_motor_position)

                return True, self.current_wavelength

    def Get_Motor_Limit_Status(self):
        self.Write_To_HR320('K')
        response = self.Read_From_HR320(is_known_bytes = False, is_carriage_return_terminated = True)
        confirmation_character, decoded_response = self.Decrypt_Response(response)

        decoded_status = None
        if confirmation_character == 'o':
            decoded_status = self.Decrypt_Limit_Status(decoded_response[0])
        else:
            return False, -1, -1

        if decoded_status[4] or decoded_status[5]:
            if decoded_status[4]:
                print("Limit on First Monochromator Hit")
                return True, True, self.is_motor_moving_in_positive_direction
            elif decoded_status[5]:
                print("Limit on Second Monochromator Hit")
                return True, True, self.is_motor_moving_in_positive_direction
        else:
            print("No Limits Hit")
            return True, False, self.is_motor_moving_in_positive_direction

    def Stop_Motor(self):
        self.Write_To_HR320('L')
        response = self.Read_From_HR320(is_known_bytes = True, is_carriage_return_terminated = False, expected_bytes = 1)

        if response == 'b':
            return False
        elif response == 'o':
            return True

class Time_Resolved_Spectroscopy_Controller(QObject):
    gpibAddressesChanged = Signal()
    hr320ConnectionChanged = Signal()
    hr320CalibrationChanged = Signal()
    hr320MotorStatusChanged = Signal()
    hr320CheckBacklashCorrection = Signal()
    hr320CurrentWavelengthChanged = Signal(int)
    logMessage = Signal(str, str)

    def __init__(self):
        super().__init__()

        self.hr320CheckBacklashCorrection.connect(self.hr320_backlash_correction)

        self.hr320_gpib_address = None
        self.sr400_gpib_address = None
        self.ph300_gpib_address = None

        self.resource_manager = pyvisa.ResourceManager()
        self.gpib_addresses = [""]

        self.hr320_controller = None
        self.sr400_controller = None
        self.ph300_controller = None

        self.hr320_current_wavelength = 0
        self.hr320_target_wavelength = 0

        self.is_hr320_connected = False
        self.is_hr320_calibrated = False
        self.is_hr320_motor_busy = False
        self.is_hr320_backlash_correction_needed = False

        self.has_hr320_reached_target_wavelength = True

        self.is_calibration_cached = False
        self.Initialize_HR320_Calibration_Cache()

    def Initialize_HR320_Calibration_Cache(self):
        cache_file = Path.cwd() / 'Cache' / 'cache.txt'

        if cache_file.exists():
            self.is_calibration_cached = True
            with cache_file.open("r") as f:
                self.hr320_current_wavelength = float(f.read().strip())

    def Update_HR320_Calibration_Cache(self):
        if not self.is_calibration_cached:
            cache_dir = Path.cwd() / "Cache"
            cache_file = cache_dir / "cache.txt"

            cache_dir.mkdir(parents=True, exist_ok=True)

            with cache_file.open("w") as f:
                f.write(str(self.hr320_current_wavelength))

            self.is_calibration_cached = True
        else:
            cache_file = Path.cwd() / 'Cache' / 'cache.txt'
            with cache_file.open("w") as f:
                f.write(str(self.hr320_current_wavelength))

    def Get_GPIB_Addresses(self, resources):
        gpib_addresses = []
        for r in resources:
            if 'GPIB' in r:
                gpib_addresses.append(r)

        if len(gpib_addresses) == 0:
            return ['ASRL5::INSTR', 'ASRL6::INSTR']
        else:
            return gpib_addresses

    @Property(list, notify = gpibAddressesChanged)
    def gpibAddresses(self):
        return self.gpib_addresses

    @Property(bool, notify = hr320ConnectionChanged)
    def isHR320Connected(self):
        return self.is_hr320_connected

    @Property(bool, notify = hr320CalibrationChanged)
    def isHR320Calibrated(self):
        return self.is_hr320_calibrated

    @Property(bool, notify = hr320MotorStatusChanged)
    def isHR320Busy(self):
        return self.is_hr320_motor_busy

    @Property(float, notify = hr320CurrentWavelengthChanged)
    def currentWavelength(self):
        return self.hr320_current_wavelength

    @Slot()
    def refresh_gpib_addresses(self):
        resources = self.resource_manager.list_resources()
        self.gpib_addresses = self.Get_GPIB_Addresses(resources)
        self.gpibAddressesChanged.emit()

    @Slot(str)
    def initialize_HR320(self, gpib_address):
        self.hr320_gpib_address = gpib_address
        self.hr320_controller = HR320_Interface(self.hr320_gpib_address)
        is_booted, is_motor_initialized, is_motor_speed_set = self.hr320_controller.Initialize_HR320()

        if is_booted:
            self.logMessage.emit('HR320', 'Spectrometer Booted')
        else:
            self.logMessage.emit('HR320', 'Spectrometer Already Booted')

        if is_motor_initialized:
            self.logMessage.emit('HR320', 'Spectrometer Motor Initialized')
        else:
            self.logMessage.emit('HR320', 'Spectrometer Motor Failed to Start')

        if is_motor_speed_set:
            self.logMessage.emit('HR320', 'Spectrometer Motor Speed Set')
        else:
            self.logMessage.emit('HR320', 'Spectrometer Motor Failed to Set Speed')

        if is_motor_initialized and is_motor_speed_set:
            self.is_hr320_connected = True
            self.hr320ConnectionChanged.emit()

    @Slot(int)
    def calibrate_HR320(self, calibrated_wavelength):
        if self.is_hr320_motor_busy:
            return

        self.is_hr320_calibrated = self.hr320_controller.Set_Motor_Position(calibrated_wavelength)
        if self.is_hr320_calibrated:
            self.hr320_current_wavelength = calibrated_wavelength
            self.Update_HR320_Calibration_Cache()
            self.hr320CurrentWavelengthChanged.emit(self.hr320_current_wavelength)
            self.logMessage.emit('HR320', 'Spectrometer Position Calibrated')
        else:
            self.logMessage.emit('HR320', 'Spectrometer Failed to Calibrate')
        self.hr320CalibrationChanged.emit()

    @Slot(int)
    def move_HR320_motor(self, target_wavelength):
        if self.is_hr320_motor_busy:
            return

        self.hr320_target_wavelength = target_wavelength
        current_wavelength = self.hr320_current_wavelength
        is_motor_move_read = self.hr320_controller.Move_Motor_Relative(self.hr320_target_wavelength)

        if is_motor_move_read:
            self.has_hr320_reached_target_wavelength = False
            self.logMessage.emit('HR320', f'Spectrometer Moving To: {self.hr320_target_wavelength} nm')

            if self.hr320_target_wavelength < current_wavelength:
                self.is_hr320_backlash_correction_needed = True

            # Timer for HR320 Motor Status and Position
            self.hr320_motor_timer = QTimer()
            self.hr320_motor_timer.timeout.connect(self.update_HR320_motor_status)
            self.hr320_motor_timer.start(1000)  # every 1 second
        else:
            self.logMessage.emit('HR320', 'Spectrometer Failed to Move')

    @Slot()
    def hr320_backlash_correction(self):
        if self.is_hr320_backlash_correction_needed:
            if not self.is_hr320_motor_busy:
                is_motor_move_read = self.hr320_controller.Backlash_Correction()
                if is_motor_move_read:
                    self.is_hr320_backlash_correction_needed = False
                    self.logMessage.emit('HR320', 'Spectrometer Backlash Correction Initiated')
                else:
                    self.logMessage.emit('HR320', 'Spectrometer Backlash Correction Failed')

    @Slot()
    def stop_HR320_motor(self):
        is_motor_stop_read = self.hr320_controller.Stop_Motor()

        if is_motor_stop_read:
            self.logMessage.emit('HR320', 'Spectrometer Motor Stopped')

    @Slot()
    def update_HR320_motor_status(self):
        is_motor_busy_read, motor_busy_status = self.hr320_controller.Is_Motor_Busy()
        if is_motor_busy_read:
            if self.is_hr320_backlash_correction_needed:
                if not motor_busy_status:
                    self.is_hr320_motor_busy = motor_busy_status
                    self.hr320CheckBacklashCorrection.emit()
                else:
                    self.is_hr320_motor_busy = motor_busy_status
                    self.hr320MotorStatusChanged.emit()
            else:
                self.is_hr320_motor_busy = motor_busy_status
                self.hr320MotorStatusChanged.emit()

        is_position_read, current_wavelength = self.hr320_controller.Read_Motor_Position()
        if is_position_read and self.is_hr320_calibrated:
            self.hr320_current_wavelength = current_wavelength
            self.hr320CurrentWavelengthChanged.emit(self.hr320_current_wavelength)

            if not self.has_hr320_reached_target_wavelength:
                if not self.is_hr320_motor_busy and not self.is_hr320_backlash_correction_needed:
                    if self.hr320_current_wavelength == self.hr320_target_wavelength:
                        self.has_hr320_reached_target_wavelength = True
                        self.hr320_motor_timer.stop()
                        self.logMessage.emit('HR320', f'Spectrometer Reached Target Of: {self.hr320_target_wavelength} nm')

if __name__ == "__main__":
    # Set the Style
    QQuickStyle.setStyle("Fusion")

    # 1. Initialize the GUI application
    app = QGuiApplication(sys.argv)

    # 2. Create the QML engine loader
    engine = QQmlApplicationEngine()

    logger = Instrument_Log()
    time_resolved_spectroscopy_controller = Time_Resolved_Spectroscopy_Controller()
    time_resolved_spectroscopy_controller.logMessage.connect(logger.append_log)

    # --- Time Resolved Spectroscopy Interface Instantiation --- #
    engine.rootContext().setContextProperty("trs_controller", time_resolved_spectroscopy_controller)

    # -- Instantiation of Log String List as a QString List Model --- #
    engine.rootContext().setContextProperty("logger", logger)

    # 3. Load the QML file
    engine.load('user_interface.qml')

    # 4. Safety check: Exit if the QML file failed to load properly
    if not engine.rootObjects():
        sys.exit(-1)

    # 5. Start the event loop
    sys.exit(app.exec())
