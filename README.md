# dynamixel-controller

Python library for controlling Dynamixel motors with JSON-defined control tables and a simple per-motor API.

**This repository is a fork of [UGA-BSAIL/dynamixel-controller](https://github.com/UGA-BSAIL/dynamixel-controller)** by Hunter Halloran and the [University of Georgia Bio-Sensing and Instrumentation Lab](https://github.com/UGA-BSAIL). The original project is licensed under [Apache 2.0](LICENSE). This fork extends it with Protocol 2 group I/O (sync/bulk read and write), additional motor control tables, and related API updates. See [docs.md](docs.md) for the full API reference.

## Installation

### From this repository (recommended for this fork)

Clone and install in editable mode so local changes are picked up immediately:

```bash
git clone https://github.com/smpdl/dynamixel-controller.git
cd dynamixel-controller
pip install -e .
```

Or install directly from GitHub without cloning:

```bash
pip install git+https://github.com/smpdl/dynamixel-controller.git
```

**Requirements:** Python 3, [pyserial](https://pypi.org/project/pyserial/), and [deprecation](https://pypi.org/project/deprecation/) (installed automatically).

### Original package on PyPI

The upstream project is also published as `dynamixel-controller`:

```bash
pip install dynamixel-controller
```

That release does not include the fork-specific features below (group I/O, newer control tables). Use the install options above for this codebase.

## Usage

### Import

```python
from dynio import DynamixelIO, DynamixelMotor, DynamixelCommError, control_table_path, dxl
```

`dxl` is an alias for `dynio.dynamixel_controller` if you prefer the original import style.

### Open the bus

```python
dxl_io = DynamixelIO('/dev/ttyUSB0', 57600)  # port and baud rate for U2D2 or other adapter
```

On Windows, use a COM port (for example `COM3`) instead of `/dev/ttyUSB0`.

### Create motors

Pre-defined helpers load bundled control-table JSON from `dynio/DynamixelJSON/`:

```python
ax_12 = dxl_io.new_ax12(1)                    # AX-12, Protocol 1
mx_64_1 = dxl_io.new_mx64(2, protocol=1)      # MX-64, Protocol 1
mx_64_2 = dxl_io.new_mx64(3, protocol=2)      # MX-64, Protocol 2

# Protocol 2 models added in this fork
xc330 = dxl_io.new_xc330m288t(4)
xl430 = dxl_io.new_xl430w250t(5)
xm430 = dxl_io.new_xm430w350t(6)
```

Custom models can use any JSON control table:

```python
motor = dxl_io.new_motor(7, control_table_path('MyMotor.json'), protocol=2)
```

See [docs.md](docs.md) for all `new_*` helpers and motor APIs.

### Per-motor control

Common operations are methods on `DynamixelMotor`:

```python
motor.torque_enable()
motor.torque_disable()
motor.set_acceleration(acceleration)
motor.set_velocity_mode()
motor.set_velocity(velocity)
motor.set_position_mode()
motor.set_position(position)
motor.set_angle(angle)
motor.set_extended_position_mode()
position = motor.get_position()
angle = motor.get_angle()
current = motor.get_current()
```

Any control-table field can be read or written by name (see [ROBOTIS e-Manual](http://emanual.robotis.com/) for register definitions):

```python
motor.write_control_table("LED", 1)
speed = motor.read_control_table("Present_Speed")
```

### Group I/O (Protocol 2, this fork)

Read or write the same register on multiple motors in one bus transaction with **sync** operations, or mix different registers per motor with **bulk** operations. All motors in a group transaction must use the same protocol (typically Protocol 2).

```python
m1 = dxl_io.new_xm430w350t(1)
m2 = dxl_io.new_xm430w350t(2)
m3 = dxl_io.new_xm430w350t(3)

# Sync read: one register, many motors
positions = dxl_io.sync_read([m1, m2, m3], "Present_Position")
# {1: 2048, 2: 1024, 3: 3072}

# Sync write: one register, many motors
dxl_io.sync_write(
    {m1: 2048, m2: 1024, m3: 3072},
    register_name="Goal_Position",
)

# Bulk read: different registers per motor in one transaction
readings = dxl_io.bulk_read([
    (m1, "Present_Position"),
    (m2, "Present_Current"),
    (m3, "Hardware_Error_Status"),
])

# Bulk write: mixed registers (Protocol 2 only)
dxl_io.bulk_write([
    (m1, "Goal_Position", 2048),
    (m2, "Goal_Position", 1024),
    (m3, "LED", 1),
])
```

Bus failures raise `DynamixelCommError` (for example port not open or a failed group transaction).

## Documentation

Full API documentation: [docs.md](docs.md)

## Acknowledgments

- **Original library:** [UGA-BSAIL/dynamixel-controller](https://github.com/UGA-BSAIL/dynamixel-controller) — Hunter Halloran (Jyumpp), University of Georgia Bio-Sensing and Instrumentation Lab. Copyright 2020 UGA BSAIL, Apache License 2.0.
- **Dynamixel SDK:** vendored from [ROBOTIS-GIT/DynamixelSDK](https://github.com/ROBOTIS-GIT/DynamixelSDK) (see [NOTICE.md](NOTICE.md)).

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Especially encouraged: new control-table JSON files under `dynio/DynamixelJSON/`.

## License

[Apache 2.0](https://choosealicense.com/licenses/apache-2.0/) — see [LICENSE](LICENSE).
