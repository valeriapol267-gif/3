"""Спецификация команд учебной виртуальной машины, вариант 22."""

from dataclasses import dataclass

MIN_VALUE = 0
OPCODE_WIDTH = 5
LOAD_CONST = 5
READ_MEM = 2
WRITE_MEM = 7
SQRT = 17


class AssemblyError(ValueError):
    """Ошибка исходной программы или внутренних полей команды."""


@dataclass(frozen=True)
class Field:
    """Имя поля, номер младшего бита и битовая ширина."""

    name: str
    shift: int
    width: int


@dataclass(frozen=True)
class Command:
    """Код операции, размер в байтах и поля операндов."""

    opcode: int
    size: int
    fields: tuple


CONSTANT_B = Field("B", 5, 30)
CONSTANT_C = Field("C", 35, 22)
ADDRESS_B = Field("B", 5, 22)
ADDRESS_C = Field("C", 27, 22)

COMMANDS = {
    LOAD_CONST: Command(LOAD_CONST, 8, (CONSTANT_B, CONSTANT_C)),
    READ_MEM: Command(READ_MEM, 7, (ADDRESS_B, ADDRESS_C)),
    WRITE_MEM: Command(WRITE_MEM, 7, (ADDRESS_B, ADDRESS_C)),
    SQRT: Command(SQRT, 7, (ADDRESS_B, ADDRESS_C)),
}


def check_value(value, width, name):
    """Проверяет беззнаковое целое заданной битовой ширины."""
    maximum = (1 << width) - 1
    if type(value) is not int or not MIN_VALUE <= value <= maximum:
        raise AssemblyError(f"Поле {name}: нужно целое от 0 до {maximum}")
