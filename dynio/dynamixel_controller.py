################################################################################
# Copyright 2020 University of Georgia Bio-Sensing and Instrumentation Lab
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################

# Author: Hunter Halloran (Jyumpp)

from dynamixel_sdk import *
import json
import os
import pkg_resources
from deprecation import deprecated

from dynio.group_io import (
    DynamixelCommError,
    encode_register_value,
    normalize_motor_list,
    normalize_sync_write_targets,
    parse_bulk_read_specs,
    parse_bulk_write_specs,
    resolve_sync_register,
)

def control_table_path(filename):
    """Resolve a control-table JSON file bundled with this package."""
    path = pkg_resources.resource_filename(__name__, f"DynamixelJSON/{filename}")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Control table JSON not found: {path}")
    return path

class DynamixelIO:
    """Creates communication handler for Dynamixel motors"""

    def __init__(self,
                 device_name='/dev/ttyUSB0',
                 baud_rate=57600):
        if device_name is None:
            self._sync_read_groups = {}
            return
        self.port_handler = PortHandler(device_name)
        self.packet_handler = [PacketHandler(1), PacketHandler(2)]
        if not self.port_handler.setBaudRate(baud_rate):
            raise (NameError("BaudChangeError"))

        if not self.port_handler.openPort():
            raise (NameError("PortOpenError"))

        self._sync_read_groups = {}

    def _require_connected(self):
        if not getattr(self, "port_handler", None):
            raise DynamixelCommError("DynamixelIO is not connected to a serial port.")

    def _raise_on_comm_failure(self, protocol, comm_result):
        if comm_result != COMM_SUCCESS:
            handler = self.packet_handler[protocol - 1]
            raise DynamixelCommError(handler.getTxRxResult(comm_result), comm_result=comm_result)

    def __check_error(self, protocol, dxl_comm_result, dxl_error):
        """Prints the error message when not successful"""
        if dxl_comm_result != COMM_SUCCESS:
            print("%s" % self.packet_handler[protocol - 1].getTxRxResult(dxl_comm_result))
        elif dxl_error != 0:
            print("%s" % self.packet_handler[protocol - 1].getRxPacketError(dxl_error))

    def write_control_table(self, protocol, dxl_id, value, address, size):
        """Writes a specified value to a given address in the control table"""
        dxl_comm_result = 0
        dxl_error = 0

        # the following has to be done inelegantly due to the dynamixel sdk having separate functions per packet size.
        # future versions of this library may replace usage of the dynamixel sdk to increase efficiency and remove this
        # bulky situation.
        if size == 1:
            dxl_comm_result, dxl_error = self.packet_handler[protocol - 1].write1ByteTxRx(self.port_handler, dxl_id,
                                                                                          address, value)
        elif size == 2:
            dxl_comm_result, dxl_error = self.packet_handler[protocol - 1].write2ByteTxRx(self.port_handler, dxl_id,
                                                                                          address, value)
        elif size == 4:
            dxl_comm_result, dxl_error = self.packet_handler[protocol - 1].write4ByteTxRx(self.port_handler, dxl_id,
                                                                                          address, value)
        self.__check_error(protocol, dxl_comm_result, dxl_error)

    def read_control_table(self, protocol, dxl_id, address, size):
        """Returns the held value from a given address in the control table"""
        ret_val = 0
        dxl_comm_result = 0
        dxl_error = 0

        # the following has to be done inelegantly due to the dynamixel sdk having separate functions per packet size.
        # future versions of this library may replace usage of the dynamixel sdk to increase efficiency and remove this
        # bulky situation.
        if size == 1:
            ret_val, dxl_comm_result, dxl_error = self.packet_handler[protocol - 1].read1ByteTxRx(self.port_handler,
                                                                                                  dxl_id, address)
        elif size == 2:
            ret_val, dxl_comm_result, dxl_error = self.packet_handler[protocol - 1].read2ByteTxRx(self.port_handler,
                                                                                                  dxl_id, address)
        elif size == 4:
            ret_val, dxl_comm_result, dxl_error = self.packet_handler[protocol - 1].read4ByteTxRx(self.port_handler,
                                                                                                  dxl_id, address)
        self.__check_error(protocol, dxl_comm_result, dxl_error)
        return ret_val

    def new_motor(self, dxl_id, json_file, protocol=2, control_table_protocol=None):
        """Returns a new DynamixelMotor object of a given protocol with a given control table"""
        return DynamixelMotor(dxl_id, self, json_file, protocol, control_table_protocol)

    def new_ax12(self, dxl_id):
        """Returns a new DynamixelMotor object for an AX12"""
        return DynamixelMotor(dxl_id, self,
                              pkg_resources.resource_filename(__name__, "DynamixelJSON/AX12.json"))

    def new_mx12(self, dxl_id):
        """Returns a new DynamixelMotor object for an MX12"""
        return DynamixelMotor(dxl_id, self,
                              pkg_resources.resource_filename(__name__, "DynamixelJSON/MX12.json"))

    def new_mx28(self, dxl_id, protocol=1, control_table_protocol=None):
        """Returns a new DynamixelMotor object for an MX28"""
        return DynamixelMotor(dxl_id, self,
                              pkg_resources.resource_filename(__name__, "DynamixelJSON/MX28.json"),
                              protocol=protocol, control_table_protocol=control_table_protocol)

    def new_mx64(self, dxl_id, protocol=1, control_table_protocol=None):
        """Returns a new DynamixelMotor object for an MX64"""
        return DynamixelMotor(dxl_id, self,
                              pkg_resources.resource_filename(__name__, "DynamixelJSON/MX64.json"),
                              protocol=protocol, control_table_protocol=control_table_protocol)

    def new_mx106(self, dxl_id, protocol=1, control_table_protocol=None):
        """Returns a new DynamixelMotor object for an MX106"""
        return DynamixelMotor(dxl_id, self,
                              pkg_resources.resource_filename(__name__, "DynamixelJSON/MX106.json"),
                              protocol=protocol, control_table_protocol=control_table_protocol)

    def new_xc330m288t(self, dxl_id, protocol=2, control_table_protocol=None):
        """Returns a new DynamixelMotor object for an XC330-M288-T (Protocol 2)."""
        return self.new_motor(
            dxl_id, pkg_resources.resource_filename(__name__, "DynamixelJSON/XC330M288T.json"), protocol, control_table_protocol
        )

    def new_xl430w250t(self, dxl_id, protocol=2, control_table_protocol=None):
        """Returns a new DynamixelMotor object for an XL430-W250-T (Protocol 2)."""
        return self.new_motor(
            dxl_id, pkg_resources.resource_filename(__name__, "DynamixelJSON/XL430W250T.json"), protocol, control_table_protocol
        )

    def new_xm430w350t(self, dxl_id, protocol=2, control_table_protocol=None):
        """Returns a new DynamixelMotor object for an XM430-W350-T (Protocol 2)."""
        return self.new_motor(
            dxl_id, pkg_resources.resource_filename(__name__, "DynamixelJSON/XM430W350T.json"), protocol, control_table_protocol
        )

    def new_xm540w270t(self, dxl_id, protocol=2, control_table_protocol=None):
        """Returns a new DynamixelMotor object for an XM540-W270-T (Protocol 2)."""
        return self.new_motor(
            dxl_id, pkg_resources.resource_filename(__name__, "DynamixelJSON/XM540W270.json"), protocol, control_table_protocol
        )

    def sync_read(self, motors, register_name, protocol=None):
        """Read the same register from multiple motors in one Sync Read (Protocol 2).

        Returns a dict mapping dxl_id -> raw register value.
        """
        self._require_connected()
        motors = normalize_motor_list(motors)
        resolved_protocol, address, size = resolve_sync_register(motors, register_name)
        if protocol is not None and protocol != resolved_protocol:
            raise ValueError(
                f"Requested protocol {protocol} does not match motors (use {resolved_protocol})."
            )
        protocol = resolved_protocol
        if protocol != 2:
            raise ValueError("sync_read requires Protocol 2 motors.")

        motor_ids = tuple(motor.dxl_id for motor in motors)
        cache_key = (protocol, address, size, motor_ids)
        group = self._sync_read_groups.get(cache_key)
        if group is None:
            handler = self.packet_handler[protocol - 1]
            group = GroupSyncRead(self.port_handler, handler, address, size)
            self._sync_read_groups[cache_key] = group

        group.clearParam()
        for motor in motors:
            group.addParam(motor.dxl_id)

        comm_result = group.txRxPacket()
        self._raise_on_comm_failure(protocol, comm_result)

        return {
            motor.dxl_id: group.getData(motor.dxl_id, address, size) for motor in motors
        }

    def sync_write(self, writes, register_name=None, protocol=None):
        """Write the same register on multiple motors in one Sync Write.

        ``writes`` maps each :class:`DynamixelMotor` to an integer value, or to
        ``(register_name, value)`` when ``register_name`` is omitted.
        """
        self._require_connected()
        motors, values, register_name = normalize_sync_write_targets(writes, register_name)
        resolved_protocol, address, size = resolve_sync_register(motors, register_name)
        if protocol is not None and protocol != resolved_protocol:
            raise ValueError(
                f"Requested protocol {protocol} does not match motors (use {resolved_protocol})."
            )
        protocol = resolved_protocol
        handler = self.packet_handler[protocol - 1]

        group = GroupSyncWrite(self.port_handler, handler, address, size)
        for motor, value in zip(motors, values):
            if not group.addParam(motor.dxl_id, encode_register_value(value, size)):
                raise DynamixelCommError(
                    f"Failed to add sync write param for motor id={motor.dxl_id}."
                )

        comm_result = group.txPacket()
        self._raise_on_comm_failure(protocol, comm_result)

    def bulk_read(self, specs, protocol=None):
        """Read registers via Fast Bulk Read; each motor may use a different address/length.

        Each entry in ``specs`` is ``(motor, register_name)`` or ``(motor, address, size)``.
        Returns a dict mapping dxl_id -> raw register value.
        """
        self._require_connected()
        parsed = parse_bulk_read_specs(specs)
        if protocol is None:
            protocol = parsed[0][0].PROTOCOL
        for motor, address, size in parsed:
            if motor.PROTOCOL != protocol:
                raise ValueError(
                    f"All motors must use protocol {protocol} (id={motor.dxl_id} uses "
                    f"{motor.PROTOCOL})."
                )

        handler = self.packet_handler[protocol - 1]
        group = GroupBulkRead(self.port_handler, handler)
        read_targets: list[tuple[int, int, int]] = []

        for motor, address, size in parsed:
            if not group.addParam(motor.dxl_id, address, size):
                raise DynamixelCommError(
                    f"Failed to add bulk read param for motor id={motor.dxl_id}."
                )
            read_targets.append((motor.dxl_id, address, size))

        comm_result = group.txRxPacket()
        self._raise_on_comm_failure(protocol, comm_result)

        return {
            dxl_id: group.getData(dxl_id, address, size)
            for dxl_id, address, size in read_targets
        }

    def bulk_write(self, specs, protocol=None):
        """Write registers via Bulk Write; each motor may use a different address/length.

        Each entry is ``(motor, register_name, value)`` or ``(motor, address, size, value)``.
        """
        self._require_connected()
        parsed = parse_bulk_write_specs(specs)
        if protocol is None:
            protocol = parsed[0][0].PROTOCOL
        if protocol != 2:
            raise ValueError("bulk_write requires Protocol 2.")

        for motor, _, _ in parsed:
            if motor.PROTOCOL != protocol:
                raise ValueError(
                    f"All motors must use protocol {protocol} (id={motor.dxl_id} uses "
                    f"{motor.PROTOCOL})."
                )

        handler = self.packet_handler[protocol - 1]
        group = GroupBulkWrite(self.port_handler, handler)
        for motor, address, size, data in parsed:
            if not group.addParam(motor.dxl_id, address, size, data):
                raise DynamixelCommError(
                    f"Failed to add bulk write param for motor id={motor.dxl_id}."
                )

        comm_result = group.txPacket()
        self._raise_on_comm_failure(protocol, comm_result)
    # the following functions are deprecated and will be removed in version 1.0 release. They have been restructured
    # to continue to function for the time being, but are the result of an older system of JSON config files which
    # initially stored less information about each motor, causing a different initialization function to be needed
    # for each version of the motor per protocol.

    @deprecated('0.8', '1.0', details="Use new_ax12() instead")
    def new_ax12_1(self, dxl_id):
        """Returns a new DynamixelMotor object for an AX12"""
        return DynamixelMotor(dxl_id, self,
                              pkg_resources.resource_filename(__name__, "DynamixelJSON/AX12.json"))

    # protocol 2 MX motors all use the same control table and could be initialized with the same control table layout,
    # but this decreases readability and should be called with the specific motor being used instead.
    @deprecated('0.8', '1.0', details="Use the specific new motor function instead")
    def new_mx_2(self, dxl_id):
        """Returns a new DynamixelMotor object of a given protocol for an MX series"""
        return DynamixelMotor(dxl_id, self,
                              pkg_resources.resource_filename(__name__, "DynamixelJSON/MX64.json"), 2)

    @deprecated('0.8', '1.0', details="Use new_mx12() instead")
    def new_mx12_1(self, dxl_id):
        """Returns a new DynamixelMotor object for an MX12"""
        return DynamixelMotor(dxl_id, self,
                              pkg_resources.resource_filename(__name__, "DynamixelJSON/MX12.json"))

    @deprecated('0.8', '1.0', details="Use new_mx28() instead")
    def new_mx28_1(self, dxl_id):
        """Returns a new DynamixelMotor object for an MX28"""
        return self.new_mx12_1(dxl_id)

    @deprecated('0.8', '1.0', details="Use new_mx64() instead")
    def new_mx64_1(self, dxl_id):
        """Returns a new DynamixelMotor object for an MX64"""
        return DynamixelMotor(dxl_id, self,
                              pkg_resources.resource_filename(__name__, "DynamixelJSON/MX64.json"))

    @deprecated('0.8', '1.0', details="Use new_mx106() instead")
    def new_mx106_1(self, dxl_id):
        """Returns a new DynamixelMotor object for an MX106"""
        return DynamixelMotor(dxl_id, self,
                              pkg_resources.resource_filename(__name__, "DynamixelJSON/MX106.json"))


class DynamixelMotor:
    """Creates the basis of individual motor objects"""

    def __init__(self, dxl_id, dxl_io, json_file, protocol=1, control_table_protocol=None):
        """Initializes a new DynamixelMotor object"""

        # protocol 2 series motors can run using protocol 1, but still use the new control table.
        # this sets the control table choice to the default if one is not explicitly requested.
        if protocol == 1 or control_table_protocol is None:
            control_table_protocol = protocol

        # loads the JSON config file and gathers the appropriate control table.
        fd = open(json_file)
        config = json.load(fd)
        fd.close()
        if control_table_protocol == 1:
            config = config.get("Protocol_1")
        else:
            config = config.get("Protocol_2")

        # sets the motor object values based on inputs or JSON options.
        self.CONTROL_TABLE_PROTOCOL = control_table_protocol
        self.dxl_id = dxl_id
        self.dxl_io = dxl_io
        self.PROTOCOL = protocol
        self.CONTROL_TABLE = config.get("Control_Table")
        self.min_position = config.get("Values").get("Min_Position")
        self.max_position = config.get("Values").get("Max_Position")
        self.max_angle = config.get("Values").get("Max_Angle")

    def write_control_table(self, data_name, value):
        """Writes a value to a control table area of a specific name"""
        self.dxl_io.write_control_table(self.PROTOCOL, self.dxl_id, value, self.CONTROL_TABLE.get(data_name)[0],
                                        self.CONTROL_TABLE.get(data_name)[1])

    def read_control_table(self, data_name):
        """Reads the value from a control table area of a specific name"""
        return self.dxl_io.read_control_table(self.PROTOCOL, self.dxl_id, self.CONTROL_TABLE.get(data_name)[0],
                                              self.CONTROL_TABLE.get(data_name)[1])

    def set_velocity_mode(self, goal_current=None):
        """Sets the motor to run in velocity (wheel) mode and sets the goal current if provided"""
        if self.CONTROL_TABLE_PROTOCOL == 1:
            # protocol 1 sets velocity mode by setting both angle limits to 0.
            self.write_control_table("CW_Angle_Limit", 0)
            self.write_control_table("CCW_Angle_Limit", 0)
            if goal_current is not None:
                # protocol 1 calls goal current Max Torque rather than Goal Current.
                self.write_control_table("Max_Torque", goal_current)
        elif self.CONTROL_TABLE_PROTOCOL == 2:
            # protocol 2 has a specific register for operating mode.
            self.write_control_table("Operating_Mode", 1)
            if goal_current is not None:
                self.write_control_table("Goal_Current", goal_current)

    def set_position_mode(self, min_limit=None, max_limit=None, goal_current=None):
        """Sets the motor to run in position (joint) mode and sets the goal current if provided.
        If position limits are not specified, the full range of motion is used instead"""
        if self.CONTROL_TABLE_PROTOCOL == 1:
            # protocol 1 sets position mode by having different values for min and max position.
            if min_limit is None or max_limit is None:
                min_limit = self.min_position
                max_limit = self.max_position
            self.write_control_table("CW_Angle_Limit", min_limit)
            self.write_control_table("CCW_Angle_Limit", max_limit)
            if goal_current is not None:
                # protocol 1 calls goal current Max Torque rather than Goal Current.
                self.write_control_table("Max_Torque", goal_current)
        elif self.CONTROL_TABLE_PROTOCOL == 2:
            # protocol 2 has a specific register for operating mode.
            self.write_control_table("Operating_Mode", 3)
            if min_limit is not None:
                self.write_control_table("Min_Position_Limit", min_limit)
            if max_limit is not None:
                self.write_control_table("Max_Position_Limit", max_limit)
            if goal_current is not None:
                self.write_control_table("Goal_Current", goal_current)

    def set_extended_position_mode(self, goal_current=None):
        """Sets the motor to run in extended position (multi-turn) mode"""
        if self.CONTROL_TABLE_PROTOCOL == 1:
            # protocol 1 sets multi turn mode by setting both angle limits to max value.
            self.write_control_table("CW_Angle_Limit", self.max_position)
            self.write_control_table("CCW_Angle_Limit", self.max_position)
            if goal_current is not None:
                # protocol 1 calls goal current Max Torque rather than Goal Current.
                self.write_control_table("Max_Torque", goal_current)
        elif self.CONTROL_TABLE_PROTOCOL == 2:
            # protocol 2 has a specific register for operating mode.
            self.write_control_table("Operating_Mode", 4)
            if goal_current is not None:
                self.write_control_table("Goal_Current", goal_current)

    def set_velocity(self, velocity):
        """Sets the goal velocity of the motor"""
        if self.CONTROL_TABLE_PROTOCOL == 1:
            # protocol 1 uses 1's compliment rather than 2's compliment for negative numbers.
            if velocity < 0:
                velocity = abs(velocity)
                velocity += 1024
            self.write_control_table("Moving_Speed", velocity)
        elif self.CONTROL_TABLE_PROTOCOL == 2:
            if self.read_control_table("Operating_Mode") == 1:
                self.write_control_table("Goal_Velocity", velocity)
            else:
                self.write_control_table("Profile_Velocity", velocity)

    def set_acceleration(self, acceleration):
        """Sets the goal acceleration of the motor"""
        if self.CONTROL_TABLE_PROTOCOL == 1:
            self.write_control_table("Goal_Acceleration", acceleration)
        elif self.CONTROL_TABLE_PROTOCOL == 2:
            self.write_control_table("Profile_Acceleration", acceleration)

    def set_position(self, position):
        """Sets the goal position of the motor"""
        self.write_control_table("Goal_Position", position)

    def set_angle(self, angle):
        """Sets the goal position of the motor with a given angle in degrees"""
        self.set_position(
            # formula for mapping the range from min to max angle to min to max position.
            int(((angle / self.max_angle) * ((self.max_position + 1) - self.min_position)) + self.min_position))

    def get_position(self):
        """Returns the motor position"""
        return self.read_control_table("Present_Position")

    def get_angle(self):
        """Returns the motor position as an angle in degrees"""
        return ((self.get_position() - self.min_position) / (
                (self.max_position + 1) - self.min_position)) * self.max_angle

    def get_current(self):
        """Returns the current motor load"""
        if self.CONTROL_TABLE_PROTOCOL == 1:
            current = self.read_control_table("Present_Load")
            if current < 0:
                return -1
            if current > 1023:
                # protocol 1 uses 1's compliment rather than 2's compliment for negative numbers.
                current -= 1023
                current *= -1
            return current
        elif self.CONTROL_TABLE_PROTOCOL == 2:
            table = self.CONTROL_TABLE
            if "Present_Current" in table:
                return self.read_control_table("Present_Current")
            if "Present_Load" in table:
                # XL430-W250-T reports load at address 126 (0.1% units, signed).
                return self.read_control_table("Present_Load")

    def torque_enable(self):
        """Enables motor torque"""
        self.write_control_table("Torque_Enable", 1)

    def torque_disable(self):
        """Disables motor torque"""
        self.write_control_table("Torque_Enable", 0)

    def get_model_number(self):
        """Returns the model number of the motor"""
        return self.read_control_table("Model_Number")
    
    def get_id(self):
        """Returns the ID of the motor"""
        return self.read_control_table("ID")
    
    def get_baud_rate(self):
        """Returns the baud rate of the motor"""
        return self.read_control_table("Baud_Rate")
    
    def get_present_temperature(self):
        """Returns the present temperature of the motor"""
        return self.read_control_table("Present_Temperature")

    def hardware_error_status(self):
        """Returns the hardware error status of the motor"""
        return self.read_control_table("Hardware_Error_Status")