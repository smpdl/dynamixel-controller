
# dynio

Public exports from `dynio`:

- `DynamixelIO`, `DynamixelMotor` — motor bus and per-motor API
- `DynamixelCommError` — raised when group transactions or connection checks fail
- `control_table_path` — resolve bundled control-table JSON paths
- `dxl` — alias for `dynio.dynamixel_controller`


# dynio.dynamixel_controller


## control_table_path
```python
control_table_path(filename)
```
Returns the filesystem path to a control-table JSON file bundled in `dynio/DynamixelJSON/`. Raises `FileNotFoundError` if the file is missing.


## DynamixelIO
```python
DynamixelIO(self, device_name='/dev/ttyUSB0', baud_rate=57600)
```
Creates communication handler for Dynamixel motors

### write_control_table
```python
DynamixelIO.write_control_table(protocol, dxl_id, value, address, size)
```
Writes a specified value to a given address in the control table

### read_control_table
```python
DynamixelIO.read_control_table(protocol, dxl_id, address, size)
```
Returns the held value from a given address in the control table

### new_motor
```python
DynamixelIO.new_motor(dxl_id,
                      json_file,
                      protocol=2,
                      control_table_protocol=None)
```
Returns a new DynamixelMotor object of a given protocol with a given control table

### new_ax12
```python
DynamixelIO.new_ax12(dxl_id)
```
Returns a new DynamixelMotor object for an AX12

### new_mx12
```python
DynamixelIO.new_mx12(dxl_id)
```
Returns a new DynamixelMotor object for an MX12

### new_mx28
```python
DynamixelIO.new_mx28(dxl_id, protocol=1, control_table_protocol=None)
```
Returns a new DynamixelMotor object for an MX28

### new_mx64
```python
DynamixelIO.new_mx64(dxl_id, protocol=1, control_table_protocol=None)
```
Returns a new DynamixelMotor object for an MX64

### new_mx106
```python
DynamixelIO.new_mx106(dxl_id, protocol=1, control_table_protocol=None)
```
Returns a new DynamixelMotor object for an MX106

### new_xc330m288t
```python
DynamixelIO.new_xc330m288t(dxl_id, protocol=2, control_table_protocol=None)
```
Returns a new DynamixelMotor object for an XC330-M288-T (Protocol 2)

### new_xl430w250t
```python
DynamixelIO.new_xl430w250t(dxl_id, protocol=2, control_table_protocol=None)
```
Returns a new DynamixelMotor object for an XL430-W250-T (Protocol 2)

### new_xm430w350t
```python
DynamixelIO.new_xm430w350t(dxl_id, protocol=2, control_table_protocol=None)
```
Returns a new DynamixelMotor object for an XM430-W350-T (Protocol 2)

### sync_read
```python
DynamixelIO.sync_read(motors, register_name, protocol=None)
```
Reads the same register from multiple motors in one Sync Read transaction (Protocol 2 only). All motors must share the same protocol and register layout. Returns a dict mapping {`dxl_id`: raw register value}. Raises `DynamixelCommError` on bus failure.

Example usage:
```python
from dynio import DynamixelIO

dxl_io = DynamixelIO('/dev/ttyUSB0', 57600)
m1 = dxl_io.new_xm430w350t(1)
m2 = dxl_io.new_xm430w350t(2)
m3 = dxl_io.new_xm430w350t(3)

# One transaction reads the same register from every motor (Protocol 2 only)
positions = dxl_io.sync_read([m1, m2, m3], "Present_Position")
# {1: 2048, 2: 1024, 3: 3072}  — raw register values keyed by motor ID
```

### sync_write
```python
DynamixelIO.sync_write(writes, register_name=None, protocol=None)
```
Writes the same register on multiple motors in one Sync Write transaction. `writes` maps each `DynamixelMotor` to an integer value, or to `(register_name, value)` when `register_name` is omitted. Raises `DynamixelCommError` on bus failure.

Example usage:
```python
# All motors, same register — pass values keyed by motor object
dxl_io.sync_write(
    {m1: 2048, m2: 1024, m3: 3072},
    register_name="Goal_Position",
)

# Or omit register_name and give (register_name, value) per motor
dxl_io.sync_write({
    m1: ("Goal_Position", 2048),
    m2: ("Goal_Position", 1024),
    m3: ("Goal_Position", 3072),
})
```

### bulk_read
```python
DynamixelIO.bulk_read(specs, protocol=None)
```
Reads registers via Fast Bulk Read; each motor may use a different address and length. Each entry in `specs` is `(motor, register_name)` or `(motor, address, size)`. Returns a dict mapping `dxl_id` → raw register value. Raises `DynamixelCommError` on bus failure.

Example usage:
```python
# Each motor can read a different register in one transaction
readings = dxl_io.bulk_read([
    (m1, "Present_Position"),
    (m2, "Present_Current"),
    (m3, "Hardware_Error_Status"),
])
# {1: 2048, 2: 42, 3: 0}

# Raw address/size when you already know the control-table layout
readings = dxl_io.bulk_read([
    (m1, 132, 4),   # Present_Position on XM430-W350-T
    (m2, 126, 2),   # Present_Current
])
```

### bulk_write
```python
DynamixelIO.bulk_write(specs, protocol=None)
```
Writes registers via Bulk Write (Protocol 2 only). Each entry is `(motor, register_name, value)` or `(motor, address, size, value)`. Raises `DynamixelCommError` on bus failure.

Example usage:
```python
# Mixed registers across motors in one transaction (Protocol 2 only)
dxl_io.bulk_write([
    (m1, "Goal_Position", 2048),
    (m2, "Goal_Position", 1024),
    (m3, "LED", 1),
])

# Raw address/size form
dxl_io.bulk_write([
    (m1, 116, 4, 2048),   # Goal_Position on XM430-W350-T
    (m2, 116, 4, 1024),
])
```

### new_ax12_1
```python
DynamixelIO.new_ax12_1(*args, **kwargs)
```
Returns a new DynamixelMotor object for an AX12

.. deprecated:: 0.8
   This will be removed in 1.0. Use new_ax12() instead

### new_mx_2
```python
DynamixelIO.new_mx_2(*args, **kwargs)
```
Returns a new DynamixelMotor object of a given protocol for an MX series

.. deprecated:: 0.8
   This will be removed in 1.0. Use the specific new motor function instead

### new_mx12_1
```python
DynamixelIO.new_mx12_1(*args, **kwargs)
```
Returns a new DynamixelMotor object for an MX12

.. deprecated:: 0.8
   This will be removed in 1.0. Use new_mx12() instead

### new_mx28_1
```python
DynamixelIO.new_mx28_1(*args, **kwargs)
```
Returns a new DynamixelMotor object for an MX28

.. deprecated:: 0.8
   This will be removed in 1.0. Use new_mx28() instead

### new_mx64_1
```python
DynamixelIO.new_mx64_1(*args, **kwargs)
```
Returns a new DynamixelMotor object for an MX64

.. deprecated:: 0.8
   This will be removed in 1.0. Use new_mx64() instead

### new_mx106_1
```python
DynamixelIO.new_mx106_1(*args, **kwargs)
```
Returns a new DynamixelMotor object for an MX106

.. deprecated:: 0.8
   This will be removed in 1.0. Use new_mx106() instead

## DynamixelMotor
```python
DynamixelMotor(self,
               dxl_id,
               dxl_io,
               json_file,
               protocol=1,
               control_table_protocol=None)
```
Creates the basis of individual motor objects

### write_control_table
```python
DynamixelMotor.write_control_table(data_name, value)
```
Writes a value to a control table area of a specific name

### read_control_table
```python
DynamixelMotor.read_control_table(data_name)
```
Reads the value from a control table area of a specific name

### set_velocity_mode
```python
DynamixelMotor.set_velocity_mode(goal_current=None)
```
Sets the motor to run in velocity (wheel) mode and sets the goal current if provided

### set_position_mode
```python
DynamixelMotor.set_position_mode(min_limit=None,
                                 max_limit=None,
                                 goal_current=None)
```
Sets the motor to run in position (joint) mode and sets the goal current if provided.
If position limits are not specified, the full range of motion is used instead

### set_extended_position_mode
```python
DynamixelMotor.set_extended_position_mode(goal_current=None)
```
Sets the motor to run in extended position (multi-turn) mode

### set_velocity
```python
DynamixelMotor.set_velocity(velocity)
```
Sets the goal velocity of the motor

### set_acceleration
```python
DynamixelMotor.set_acceleration(acceleration)
```
Sets the goal acceleration of the motor

### set_position
```python
DynamixelMotor.set_position(position)
```
Sets the goal position of the motor

### set_angle
```python
DynamixelMotor.set_angle(angle)
```
Sets the goal position of the motor with a given angle in degrees

### get_position
```python
DynamixelMotor.get_position()
```
Returns the motor position

### get_angle
```python
DynamixelMotor.get_angle()
```
Returns the motor position as an angle in degrees

### get_current
```python
DynamixelMotor.get_current()
```
Returns the current motor load. On Protocol 2, reads `Present_Current` when available, otherwise `Present_Load` (e.g. XL430-W250-T).

### torque_enable
```python
DynamixelMotor.torque_enable()
```
Enables motor torque

### torque_disable
```python
DynamixelMotor.torque_disable()
```
Disables motor torque

### get_model_number
```python
DynamixelMotor.get_model_number()
```
Returns the model number of the motor

### get_id
```python
DynamixelMotor.get_id()
```
Returns the ID of the motor

### get_baud_rate
```python
DynamixelMotor.get_baud_rate()
```
Returns the baud rate of the motor

### get_present_temperature
```python
DynamixelMotor.get_present_temperature()
```
Returns the present temperature of the motor

### hardware_error_status
```python
DynamixelMotor.hardware_error_status()
```
Returns the hardware error status of the motor


# dynio.group_io


## DynamixelCommError
```python
DynamixelCommError(message, comm_result=None)
```
Exception raised when a group transaction fails on the bus or when `DynamixelIO` is used without an open serial port. The `comm_result` attribute holds the SDK communication result code when available.
