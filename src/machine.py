"""Упаковка команд варианта 22 в 8 или 7 байт little-endian."""

from spec import COMMANDS, OPCODE_WIDTH, AssemblyError, check_value


def encode_instruction(instruction):
    """Проверяет поля и кодирует команду с её собственным размером."""
    opcode = instruction.get("A")
    check_value(opcode, OPCODE_WIDTH, "A")
    command = COMMANDS.get(opcode)
    if command is None:
        raise AssemblyError(f"Неизвестный код операции: {opcode}")
    expected = {"A"} | {field.name for field in command.fields}
    if set(instruction) != expected:
        raise AssemblyError("Неверный набор полей команды")
    word = opcode
    for field in command.fields:
        value = instruction[field.name]
        check_value(value, field.width, field.name)
        word |= value << field.shift
    return word.to_bytes(command.size, byteorder="little")


def encode_program(program):
    """Возвращает список байтовых блоков, сохраняя границы команд."""
    return [encode_instruction(instruction) for instruction in program]


def format_bytes(block):
    """Форматирует одну команду как последовательность 0xXX через запятую."""
    return ", ".join(f"0x{value:02X}" for value in block)
