"""Helpers for Dynamixel group (sync/bulk) communication."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterable, Union

from dynamixel_sdk import (
    DXL_HIBYTE, 
    DXL_HIWORD,
    DXL_LOBYTE,
    DXL_LOWORD,
)

if TYPE_CHECKING:
    from dynio.dynamixel_controller import DynamixelMotor

BulkReadSpec = Union[
    "DynamixelMotor",
    tuple["DynamixelMotor", str],
    tuple["DynamixelMotor", int, int],
]

BulkWriteSpec = Union[
    tuple["DynamixelMotor", str, int],
    tuple["DynamixelMotor", int, int, int],
]

WriteTarget = Union["DynamixelMotor", int]


class DynamixelCommError(Exception):
    """Raised when a group transaction fails on the bus."""

    def __init__(self, message: str, comm_result: int | None = None):
        super().__init__(message)
        self.comm_result = comm_result


def motor_register(motor: DynamixelMotor, register_name: str) -> tuple[int, int]:
    """Return (address, size) for a named control-table entry."""
    table = motor.CONTROL_TABLE
    if register_name not in table:
        raise ValueError(
            f"Register '{register_name}' is not in the control table for motor id={motor.dxl_id}."
        )
    address, size = table[register_name]
    return int(address), int(size)


def encode_register_value(value: int, size: int) -> list[int]:
    """Encode an integer as little-endian register bytes for sync/bulk write."""
    value = int(value)
    # just get the lower 8 bits for a 1-byte register
    if size == 1:
        return [value & 0xFF] 
    if size == 2:
        return [DXL_LOBYTE(value), DXL_HIBYTE(value)]
    if size == 4:
        return [
            DXL_LOBYTE(DXL_LOWORD(value)),
            DXL_HIBYTE(DXL_LOWORD(value)),
            DXL_LOBYTE(DXL_HIWORD(value)),
            DXL_HIBYTE(DXL_HIWORD(value)),
        ]
    raise ValueError(f"Unsupported register size: {size}")


def normalize_motor_list(motors: Iterable[DynamixelMotor]) -> list[DynamixelMotor]:
    """Normalize a list of motors to a list of DynamixelMotor objects."""
    motors = list(motors)
    if not motors:
        raise ValueError("At least one motor is required.")
    return motors


def resolve_sync_register(
    motors: list[DynamixelMotor], register_name: str
) -> tuple[int, int, int]:
    """Validate motors share protocol and register layout; return (protocol, address, size)."""
    protocol = motors[0].PROTOCOL
    address, size = motor_register(motors[0], register_name)
    for motor in motors[1:]:
        if motor.PROTOCOL != protocol:
            raise ValueError(
                f"All motors must use the same bus protocol (id={motors[0].dxl_id} uses "
                f"{protocol}, id={motor.dxl_id} uses {motor.PROTOCOL})."
            )
        other_address, other_size = motor_register(motor, register_name)
        if (other_address, other_size) != (address, size):
            raise ValueError(
                f"Register '{register_name}' must share the same address and size for sync "
                f"operations (id={motors[0].dxl_id}: {address}/{size}, "
                f"id={motor.dxl_id}: {other_address}/{other_size})."
            )
    return protocol, address, size


def parse_bulk_read_specs(
    specs: Iterable[BulkReadSpec],
) -> list[tuple[DynamixelMotor, int, int]]:
    parsed: list[tuple[DynamixelMotor, int, int]] = []
    for spec in specs:
        if isinstance(spec, tuple):
            if len(spec) == 2:
                motor, register_name = spec
                parsed.append((motor, *motor_register(motor, register_name)))
            elif len(spec) == 3:
                motor, address, size = spec
                parsed.append((motor, int(address), int(size)))
            else:
                raise ValueError(f"Invalid bulk read spec: {spec!r}")
        else:
            raise ValueError(
                "Bulk read requires (motor, register_name) or (motor, address, size) specs."
            )
    if not parsed:
        raise ValueError("At least one bulk read spec is required.")
    return parsed


def parse_bulk_write_specs(
    specs: Iterable[BulkWriteSpec],
) -> list[tuple[DynamixelMotor, int, int, list[int]]]:
    parsed: list[tuple[DynamixelMotor, int, int, list[int]]] = []
    for spec in specs:
        if len(spec) == 3:
            motor, register_name, value = spec
            address, size = motor_register(motor, register_name)
            parsed.append((motor, address, size, encode_register_value(value, size)))
        elif len(spec) == 4:
            motor, address, size, value = spec
            size = int(size)
            parsed.append(
                (motor, int(address), size, encode_register_value(value, size))
            )
        else:
            raise ValueError(f"Invalid bulk write spec: {spec!r}")
    if not parsed:
        raise ValueError("At least one bulk write spec is required.")
    return parsed


def normalize_sync_write_targets(
    writes: dict[WriteTarget, Any],
    register_name: str | None,
) -> tuple[list[DynamixelMotor], list[int], str | None]:
    """Return (motors, values, register_name) from a sync_write mapping."""
    if not writes:
        raise ValueError("writes must not be empty.")

    motors: list[DynamixelMotor] = []
    values: list[int] = []
    resolved_register: str | None = register_name

    for target, payload in writes.items():
        motor = target if hasattr(target, "CONTROL_TABLE") else None
        if motor is None:
            raise ValueError("sync_write keys must be DynamixelMotor instances.")

        if isinstance(payload, tuple) and len(payload) == 2:
            reg_name, value = payload
            value = int(value)
            if resolved_register is None:
                resolved_register = reg_name
            elif resolved_register != reg_name:
                raise ValueError("All sync_write entries must use the same register.")
        else:
            if resolved_register is None and register_name is None:
                raise ValueError(
                    "register_name is required when write values are plain integers."
                )
            value = int(payload)

        motors.append(motor)
        values.append(value)

    if resolved_register is None:
        raise ValueError("register_name could not be determined from writes.")

    return motors, values, resolved_register
