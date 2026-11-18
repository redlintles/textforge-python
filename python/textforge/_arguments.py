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


def _numeric(value: int | str | Variable, parameter: str) -> int | str | Variable:
    """A numeric builder parameter: an integer, a variable or, since TextForge 0.3.0,
    text holding a ``[[ ]]`` expression or ``{{ }}`` template that the engine
    resolves when the instruction runs (for example ``"[[__LINES__ - 1]]"``).
    """
    if isinstance(value, str):
        return value
    return _number(value, parameter)


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


def _token(value: Pipeline | Instruction, parameter: str) -> Instruction:
    """Convert the instruction argument of builders that take Rust ``Into<TokenWrapper>``."""
    from . import Pipeline

    if isinstance(value, Variable):
        raise TypeError(f"{parameter} must be an Instruction or single-instruction Pipeline")
    if isinstance(value, (Instruction, Pipeline)):
        converted = _instruction(value, parameter)
        assert isinstance(converted, Instruction)
        return converted
    raise TypeError(f"{parameter} must be a single-instruction Pipeline or Instruction")
