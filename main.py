# This Python file uses the following encoding: utf-8
import sys
import pyvisa
import numpy as np
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtCore import QObject, Signal, Property, Slot, QTimer

class HR320_Emulator:
    def __init__(self, gpib_address):
        self.gpib_address = gpib_address
        self.buffer = b'b'

        self.min_step = 0
        self.max_step = 13000

        self.is_motor_initialized = False
        self.is_motor_speed_set = False
        self.is_motor_busy = False

        self.motor_id = None
        self.min_motor_frequency = None
        self.max_motor_frequency = None
        self.motor_ramp_time = None

        self.current_motor_position = 0
        self.target_motor_position = 0

    def write(self, query):
        if(query == 'O2000\x00'):
            self.buffer = b'*'
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
                if self.is_motor_intialized:
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
            elif query == 'C':
                if self.is_motor_initialized and self.is_motor_speed_set:
                    self.motor_id = int(delimited_parameters[0])
                    self.buffer = (str(self.min_motor_frequency) + str(self.max_motor_frequency) + str(self.motor_ramp_time)).encode('utf-8')
                else:
                    self.buffer = b'b'
            elif cmd == 'F':
                if self.is_motor_initialized and self.is_motor_speed_set:
                    self.motor_id = int(delimited_parameters[0])
                    self.target_motor_position = self.current_motor_position + int(delimited_parameters[1])
                    print("Target Motor Position: ", self.target_motor_position)
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
                    print("Target: ", self.target_motor_position)
                    print("Current: ", self.current_motor_position)
                    self.motor_id = int(delimited_parameters[0])
                    if self.current_motor_position < self.target_motor_position:
                        self.current_motor_position += 20
                    elif self.current_motor_position > self.target_motor_position:
                        self.current_motor_position -= 20
                    else:
                        self.is_motor_busy = False
                    self.buffer = ('o' + str(self.current_motor_position)).encode('utf-8')
                else:
                    self.buffer = b'b'

    def read_raw(self):
        flushed_buffer = self.buffer
        self.buffer = b'b'
        return flushed_buffer

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

    def Query(self, cmd, *params):
        query = cmd
        if params:
            if len(params) == 1:
                query += str(params[0])
            else:
                for i in range(0, len(params)):
                    if i == len(params) - 1:
                        query += str(params[i])
                    else:
                        query += str(params[i]) + ','

        if len(params) > 0:
            query += '\r'

        print("Testing Query: ", query)
        self.hr320.write(query)

        data = b'b'
        try:
            data = self.hr320.read_raw()
        except Exception as e:
            print("Done:", e)

        return data.decode('utf-8')

    def Decrypt_Response(self, response):
        cleaned_response = response.rstrip()
        delimited_response = cleaned_response.split(',')

        status_code = delimited_response[0][0]
        first_parameter = delimited_response[0][1:]

        decrypted_response = []
        decrypted_response.append(status_code)
        decrypted_response.append(first_parameter)

        if len(delimited_response) > 1:
            for i in range(1, len(delimited_response)):
                decrypted_response.append(delimited_response[i])

        return decrypted_response

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
        response = self.Query('O2000\x00')
        if response == '*':
            print('Spectrometer Booted')
            return True
        elif response == 'b':
            print('Spectrometer Failed To Boot')
            return False

    def Initialize_Motor(self):
        response = self.Query('A')
        if response == 'o':
            print('Motor Initialized')
            return True
        elif response == 'b':
            print('Motor Failed to Initialize')
            return False

    def Set_Motor_Speed(self):
        response = self.Query('B', self.motor_id, self.min_motor_frequency, self.max_motor_frequency, self.motor_ramp_time)
        if response == 'o':
            print('Motor Speed Set')
            return True
        elif response == 'b':
            print('Motor Speed Not Set')
            return False

    def Read_Motor_Speed(self):
        response = self.Query('C', self.motor_id)
        if response == 'b':
            print("Failed to Read Motor Speed")
            return False, -1, -1, -1
        else:
            decrypted_response = self.Decrypt_Response(response)
            if decrypted_response[0] == 'o':
                self.min_motor_frequency = int(decrypted_response[1])
                self.max_motor_frequency = int(decrypted_response[2])
                self.motor_ramp_time = int(decrypted_response[3])

                print("Minimum Motor Frequency: ", self.min_motor_frequency, " Hz")
                print("Maximum Motor Frequency: ", self.max_motor_frequency, " Hz")
                print("Motor Ramp Time: ", self.motor_ramp_time, " ms")
                return True, self.min_motor_frequency, self.max_motor_frequency, self.motor_ramp_time

    def Is_Motor_Busy(self):
        response = self.Query('E')

        if response == 'b':
            print('Failed to Query if Motor is Busy')
            return False, -1
        else:
            decrypted_response = self.Decrypt_Response(response)
            if decrypted_response[0] == 'o':
                print('Motor Busy Status Polled')

                if decrypted_response[1] == 'q':
                    print('Motor is Busy')
                    return True, True
                elif decrypted_response[1] == 'z':
                    print('Motor is Not Busy')
                    return True, False

    def Move_Motor_Relative(self, target_wavelength):
        self.target_wavelength = target_wavelength
        steps_to_move = self.Convert_Wavelength_To_Step_Position(self.target_wavelength - self.current_wavelength)
        self.target_motor_position = self.current_motor_position + steps_to_move

        response = None
        if steps_to_move > 0:
            response = self.Query('F', self.motor_id, steps_to_move)
        elif steps_to_move < 0:
            response = self.Query('F', self.motor_id, steps_to_move - self.backlash_steps)
        else:
            return False

        if response == 'b':
            print('Motor Failed to Move')
            return False
        elif response == 'o':
            if steps_to_move > 0:
                self.is_motor_moving_in_positive_direction = True
            else:
                self.is_motor_moving_in_positive_direction = False

            print('Motor has moved ', steps_to_move, " Steps")
            return True

    def Backlash_Correction(self):
        response = self.Query('F', self.motor_id, self.backlash_steps)

        if response == 'b':
            print('Motor Failed to Move')
            return False
        elif response == 'o':
            self.is_motor_moving_in_positive_direction = True
            print('Motor has moved ', self.backlash_steps, " Steps")
            return True

    def Set_Motor_Position(self, current_wavelength):
        self.current_wavelength = current_wavelength
        self.current_motor_position = self.Convert_Wavelength_To_Step_Position(self.current_wavelength)

        response = self.Query('G', self.motor_id, self.current_motor_position)
        print(response)

        if response == 'b':
            print("Motor Position Not Set")
            return False
        elif response == 'o':
            print("Motor Set to Position: ", self.current_motor_position)
            return True

    def Read_Motor_Position(self):
        response = self.Query('H', self.motor_id)

        if response == 'b':
            print('Failed to Read Motor Position')
            return False, -1
        else:
            decrypted_response = self.Decrypt_Response(response)

            if decrypted_response[0] == 'o':
                self.current_motor_position = int(decrypted_response[1])
                self.current_wavelength = self.Convert_Step_Position_To_Wavelength(self.current_motor_position)

                print('Current Motor Position is: ', self.current_motor_position)
                return True, self.current_wavelength

    def Get_Motor_Limit_Status(self):
        response = self.Query('K')
        print(response)
        decoded_response = self.Decrypt_Response(response)

        decoded_status = None
        if decoded_response[0] == 'o':
            decoded_status = self.Decrypt_Limit_Status(decoded_response[1])
        else:
            decoded_status = self.Decrypt_Limit_Status(decoded_response[0])

        if decoded_status[4] or decoded_status[5]:
            if decoded_status[4]:
                print("Limit on First Monochromator Hit")
                return True, self.is_motor_moving_in_positive_direction
            elif decoded_status[5]:
                print("Limit on Second Monochromator Hit")
                return True, self.is_motor_moving_in_positive_direction
        else:
            print("No Limits Hit")
            return False, self.is_motor_moving_in_positive_direction

    def Stop_Motor(self):
        response = self.Query('L')

        if response == 'b':
            print("Failed to Stop Motor")
            return False
        elif response == 'o':
            print("Motor Stopping")
            return True

class Time_Resolved_Spectroscopy_Controller(QObject):
    gpibAddressesChanged = Signal()
    hr320ConnectionChanged = Signal()
    hr320CalibrationChanged = Signal()
    hr320MotorStatusChanged = Signal()
    hr320CheckBacklashCorrection = Signal()
    hr320CurrentWavelengthChanged = Signal(int)

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

        if is_booted and is_motor_initialized and is_motor_speed_set:
            self.is_hr320_connected = True
            self.hr320ConnectionChanged.emit()

            # Timer for HR320 Motor Status
            self.hr320_motor_timer = QTimer()
            self.hr320_motor_timer.timeout.connect(self.update_HR320_motor_status)
            self.hr320_motor_timer.start(1000)  # every 1 second

    @Slot(int)
    def calibrate_HR320(self, calibrated_wavelength):
        if self.is_hr320_motor_busy:
            return

        self.is_hr320_calibrated = self.hr320_controller.Set_Motor_Position(calibrated_wavelength)
        if self.is_hr320_calibrated:
            self.hr320_current_wavelength = calibrated_wavelength
            self.Update_HR320_Calibration_Cache()
            self.hr320CurrentWavelengthChanged.emit(self.hr320_current_wavelength)
        self.hr320CalibrationChanged.emit()

    @Slot(int)
    def move_HR320_motor(self, target_wavelength):
        if self.is_hr320_motor_busy:
            return

        self.hr320_target_wavelength = target_wavelength
        current_wavelength = self.hr320_current_wavelength
        is_motor_move_read = self.hr320_controller.Move_Motor_Relative(self.hr320_target_wavelength)

        if is_motor_move_read:
            if self.hr320_target_wavelength < current_wavelength:
                self.is_hr320_backlash_correction_needed = True

    @Slot()
    def hr320_backlash_correction(self):
        if self.is_hr320_backlash_correction_needed:
            if not self.is_hr320_motor_busy:
                is_motor_move_read = self.hr320_controller.Backlash_Correction()
                if is_motor_move_read:
                    self.is_hr320_backlash_correction_needed = False

    @Slot()
    def update_HR320_motor_status(self):
        is_motor_busy_read, motor_busy_status = self.hr320_controller.Is_Motor_Busy()
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

if __name__ == "__main__":
    # Set the Style
    QQuickStyle.setStyle("Fusion")

    # 1. Initialize the GUI application
    app = QGuiApplication(sys.argv)

    # 2. Create the QML engine loader
    engine = QQmlApplicationEngine()

    # --- Time Resolved Spectroscopy Interface Instantiation ---
    time_resolved_spectroscopy_controller = Time_Resolved_Spectroscopy_Controller()
    engine.rootContext().setContextProperty("trs_controller", time_resolved_spectroscopy_controller)

    # 3. Load the QML file
    engine.load('user_interface.qml')

    # 4. Safety check: Exit if the QML file failed to load properly
    if not engine.rootObjects():
        sys.exit(-1)

    # 5. Start the event loop
    sys.exit(app.exec())
