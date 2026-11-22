"""Разбор алгебраического ассемблера варианта 22."""

import re

from spec import (
    COMMANDS,
    LOAD_CONST,
    READ_MEM,
    SQRT,
    WRITE_MEM,
    AssemblyError,
    check_value,
)

NUMBER = r"(?:0[xX][0-9a-fA-F]+|[0-9]+)"


def memory(address):
    """Строит регулярное выражение обращения M[адрес]."""
    return rf"M\s*\[\s*{address}\s*\]"


B_VALUE = rf"(?P<B>{NUMBER})"
C_VALUE = rf"(?P<C>{NUMBER})"
B_DIRECT = memory(B_VALUE)
C_DIRECT = memory(C_VALUE)
B_INDIRECT = memory(B_DIRECT)
C_INDIRECT = memory(C_DIRECT)

PATTERNS = (
    (LOAD_CONST, rf"{C_DIRECT}\s*=\s*{B_VALUE}"),
    (READ_MEM, rf"{C_DIRECT}\s*=\s*{B_INDIRECT}"),
    (WRITE_MEM, rf"{B_INDIRECT}\s*=\s*{C_DIRECT}"),
    (SQRT, rf"{C_INDIRECT}\s*=\s*sqrt\s*\(\s*{B_INDIRECT}\s*\)"),
)
RULES = tuple(
    (opcode, re.compile(pattern, re.IGNORECASE))
    for opcode, pattern in PATTERNS
)


def parse_number(token, field):
    """Читает десятичное или hex-число и проверяет диапазон поля."""
    base = 16 if token.lower().startswith("0x") else 10
    try:
        value = int(token, base)
    except ValueError as exc:
        raise AssemblyError("Слишком длинное целое число") from exc
    check_value(value, field.width, field.name)
    return value


def parse_instruction(line):
    """Распознаёт одну из четырёх форм и возвращает поля A, B, C."""
    for opcode, pattern in RULES:
        match = pattern.fullmatch(line)
        if match is None:
            continue
        result = {"A": opcode}
        for field in COMMANDS[opcode].fields:
            result[field.name] = parse_number(match[field.name], field)
        return result
    raise AssemblyError("Неизвестная команда или неверный синтаксис")


def parse_program(text):
    """Разбирает строки, пропуская пустые строки и комментарии после #."""
    program = []
    for number, original in enumerate(text.splitlines(), start=1):
        line = original.split("#", 1)[0].strip()
        if not line:
            continue
        try:
            program.append(parse_instruction(line))
        except AssemblyError as exc:
            raise AssemblyError(f"Строка {number}: {exc}") from exc
    if not program:
        raise AssemblyError("Программа не содержит команд")
    return program


def format_fields(instruction):
    """Форматирует поля команды в виде A=5, B=241, C=997."""
    return ", ".join(f"{name}={value}" for name, value in instruction.items())
