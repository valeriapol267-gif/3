"""Единая адресуемая память команд и числовых данных."""

from math import isfinite

from spec import ADDRESS_B

ZERO = 0
BYTE_MAX = 255
MEMORY_SIZE = 1 << ADDRESS_B.width


class ExecutionError(ValueError):
    """Ошибка памяти или выполнения программы УВМ."""


def check_address(address):
    """Проверяет целочисленный адрес в 22-битном пространстве."""
    if type(address) is not int or not ZERO <= address < MEMORY_SIZE:
        raise ExecutionError(f"Недопустимый адрес памяти: {address}")


def check_range(start, end):
    """Проверяет обе включительные границы диапазона дампа."""
    check_address(start)
    check_address(end)
    if start > end:
        raise ExecutionError("Начало диапазона больше конца")


class Memory:
    """Хранит байты кода и значения данных в одном словаре ячеек."""

    def __init__(self, code):
        """Загружает байты программы в ячейки с адреса ноль."""
        if len(code) > MEMORY_SIZE:
            raise ExecutionError("Программа не помещается в память")
        self.cells = dict(enumerate(code))

    def read(self, address):
        """Читает ячейку; незаписанные ячейки содержат ноль."""
        check_address(address)
        return self.cells.get(address, ZERO)

    def write(self, address, value):
        """Записывает целое или конечное вещественное число в ячейку."""
        check_address(address)
        valid = type(value) is int or (
            type(value) is float and isfinite(value)
        )
        if not valid:
            raise ExecutionError("Значение должно быть конечным числом")
        self.cells[address] = value

    def read_bytes(self, start, size):
        """Читает код из той же памяти, проверяя байтовые значения."""
        values = [self.read(address) for address in range(start, start + size)]
        for value in values:
            if type(value) is not int or not ZERO <= value <= BYTE_MAX:
                raise ExecutionError("В области команды находится не байт")
        return bytes(values)

    def dump(self, start, end):
        """Возвращает адреса и значения, включая код при его выборе."""
        check_range(start, end)
        return {
            str(address): self.read(address)
            for address in range(start, end + 1)
        }
