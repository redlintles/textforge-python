"""Type checks and Rust-builder conversions for the fluent construction facade."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._native import Instruction, Variable

if TYPE_CHECKING:
    from . import Pipeline


def _text(value: str | Variable, parameter: str) -> str | Variable:
    if not isinstance(value, (str, Variable)):
        raise TypeError(f"{parameter} must be str or Variable")
    return value


def _number(value: int | Variable, parameter: str) -> int | Variable:
    if isinstance(value, bool) or not isinstance(value, (int, Variable)):
        raise TypeError(f"{parameter} must be a nonnegative int or Variable")
    if isinstance(value, int) and not 0 <= value < 2**64:
        raise OverflowError(f"{parameter} must fit an unsigned 64-bit integer")
    return value


def _value(value: str | int | Variable, parameter: str) -> str | Variable:
    # Rust val/var/mut_var normalize literal numbers to text, preserving references.
    if isinstance(value, (str, Variable)):
        return value
    return str(_number(value, parameter))


def _instruction(
    value: Pipeline | Instruction | Variable, parameter: str
) -> Instruction | Variable:
    from . import Pipeline

    if isinstance(value, (Instruction, Variable)):
        return value
    if isinstance(value, Pipeline):
        if len(value._nodes) != 1 or not isinstance(value._nodes[0], Instruction):
            raise ValueError(f"{parameter} must contain exactly one instruction, without groups")
        return value._nodes[0]
    raise TypeError(f"{parameter} must be a single-instruction Pipeline, Instruction, or Variable")
