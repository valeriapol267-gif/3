"""Декодирование команд варианта 22 с переменной длиной."""

from machine import encode_instruction
from spec import COMMANDS, OPCODE_WIDTH, AssemblyError


def command_for(first_byte):
    """Определяет спецификацию команды по младшим пяти битам байта."""
    opcode = first_byte & ((1 << OPCODE_WIDTH) - 1)
    command = COMMANDS.get(opcode)
    if command is None:
        raise AssemblyError(f"Неизвестный код операции: {opcode}")
    return command


def decode_instruction(block):
    """Восстанавливает поля и проверяет длину и резервные биты."""
    if not block:
        raise AssemblyError("Пустая команда")
    command = command_for(block[0])
    if len(block) != command.size:
        raise AssemblyError(f"Команда должна занимать {command.size} байт")
    word = int.from_bytes(block, byteorder="little")
    instruction = {"A": command.opcode}
    for field in command.fields:
        instruction[field.name] = (
            word >> field.shift
        ) & ((1 << field.width) - 1)
    if encode_instruction(instruction) != block:
        raise AssemblyError("Резервные биты должны быть нулевыми")
    return instruction
