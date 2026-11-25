"""Проверки декодирования и общей памяти варианта 22."""

import unittest

from decoder import decode_instruction
from machine import encode_program
from memory import MEMORY_SIZE, ExecutionError, Memory
from parser import parse_program
from spec import AssemblyError
from test_machine import EXPECTED_BYTES
from test_parser import EXPECTED, ROOT
from vm import VirtualMachine


def assemble(text):
    """Собирает текст в непрерывную последовательность машинных байтов."""
    return b"".join(encode_program(parse_program(text)))


def execute(text):
    """Собирает и исполняет программу в новой УВМ."""
    machine = VirtualMachine(assemble(text))
    machine.run()
    return machine


class DecoderTests(unittest.TestCase):
    """Проверки независимых байтов спецификации и повреждений."""

    def test_specification(self):
        """Команды длиной 8 и 7 байт дают ожидаемые поля."""
        for block, expected in zip(EXPECTED_BYTES, EXPECTED):
            with self.subTest(block=block):
                self.assertEqual(decode_instruction(block), expected)

    def test_invalid_blocks(self):
        """Отклоняются обрывы, неизвестный код, резерв и лишние байты."""
        blocks = [b"", bytes(7)]
        for block in EXPECTED_BYTES:
            blocks.extend([
                block[:-1], block + b"\x00",
                block[:-1] + bytes([block[-1] | 128]),
            ])
        for block in blocks:
            with self.subTest(block=block):
                with self.assertRaises(AssemblyError):
                    decode_instruction(block)


class MemoryTests(unittest.TestCase):
    """Типы значений, адреса и включительные границы дампа."""

    def test_values_and_dump(self):
        """Незаписанные ячейки равны нулю; дробные данные сохраняются."""
        memory = Memory(b"\x05")
        memory.write(10, 1.5)
        self.assertEqual(memory.dump(9, 10), {"9": 0, "10": 1.5})
        self.assertEqual(memory.dump(0, 0), {"0": 5})

    def test_invalid_addresses(self):
        """Косвенные адреса тоже должны быть целыми и 22-битными."""
        memory = Memory(b"")
        for address in (-1, MEMORY_SIZE, 2.0, True):
            with self.subTest(address=address):
                with self.assertRaises(ExecutionError):
                    memory.read(address)
                with self.assertRaises(ExecutionError):
                    memory.write(address, 1)

    def test_invalid_values_and_bytes(self):
        """Нечисловые данные и повреждённые байты кода отклоняются."""
        memory = Memory(b"")
        for value in (True, "1", float("nan"), float("inf")):
            with self.subTest(value=value):
                with self.assertRaises(ExecutionError):
                    memory.write(0, value)
        for value in (-1, 256, 2.0):
            memory.write(0, value)
            with self.assertRaises(ExecutionError):
                memory.read_bytes(0, 1)

    def test_invalid_ranges(self):
        """Перевёрнутый диапазон и выход за память отклоняются."""
        for start, end in ((2, 1), (-1, 0), (0, MEMORY_SIZE)):
            with self.subTest(start=start, end=end):
                with self.assertRaises(ExecutionError):
                    Memory(b"").dump(start, end)


class VirtualMachineTests(unittest.TestCase):
    """Косвенная адресация и выборка команд из изменяемой общей памяти."""

    def test_copy_array(self):
        """Копирование сохраняет исходный массив и создаёт его копию."""
        text = (ROOT / "examples/copy.asm").read_text(encoding="utf-8")
        machine = execute(text)
        self.assertEqual(machine.memory.dump(1000, 1002), {
            "1000": 10, "1001": 20, "1002": 30,
        })
        self.assertEqual(machine.memory.dump(2000, 2002), {
            "2000": 10, "2001": 20, "2002": 30,
        })
        self.assertEqual((machine.pc, machine.steps), (114, 15))

    def test_read_code_as_data(self):
        """Обычная операция памяти читает байт кода по адресу ноль."""
        machine = execute("M[500] = 0\nM[1000] = M[M[500]]")
        self.assertEqual(machine.memory.read(1000), 5)

    def test_self_modifying_code(self):
        """Изменение байта будущей команды влияет на её исполнение."""
        machine = execute("M[8] = 69\nM[1000] = 0")
        self.assertEqual(machine.memory.read(1000), 2)
        self.assertEqual(machine.memory.read(8), 69)

    def test_corrupted_future_command(self):
        """Неверный код операции и небайтовое значение дают адрес ошибки."""
        for value in (0, 999):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ExecutionError, "Байт 8"):
                    execute(f"M[8] = {value}\nM[1000] = 1")

    def test_empty_and_truncated_programs(self):
        """Пустой файл и оборванная последняя команда не выполняются."""
        for code in (b"", b"\x05", assemble("M[1000] = 1") + b"\x02"):
            with self.subTest(code=code):
                with self.assertRaises(ExecutionError):
                    VirtualMachine(code).run()

    def test_invalid_indirect_address(self):
        """Константа может быть допустима как число, но не как указатель."""
        for operation in ("M[1000] = M[M[500]]", "M[M[500]] = M[1000]"):
            with self.subTest(operation=operation):
                with self.assertRaises(ExecutionError):
                    execute(f"M[500] = {MEMORY_SIZE}\n{operation}")

    def test_maximum_address_and_constant(self):
        """Старшая ячейка вмещает всю 30-битную константу."""
        machine = execute("M[4194303] = 1073741823")
        self.assertEqual(machine.memory.read(4194303), 1073741823)
