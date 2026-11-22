"""Проверка байтов варианта 22 по примерам из методички."""

import unittest

import test_main
from machine import encode_instruction, encode_program, format_bytes
from parser import parse_program
from spec import AssemblyError
from test_parser import EXPECTED, ROOT

EXPECTED_BYTES = (
    bytes.fromhex("25 1E 00 00 28 1F 00 00"),
    bytes.fromhex("02 34 00 D8 12 00 00"),
    bytes.fromhex("A7 22 00 78 18 00 00"),
    bytes.fromhex("71 30 00 C8 04 00 00"),
)


class MachineTests(unittest.TestCase):
    """Точные байты, границы команд, диапазоны и работа CLI."""

    def test_specification(self):
        """Все четыре команды совпадают с байтами из спецификации."""
        for fields, expected in zip(EXPECTED, EXPECTED_BYTES):
            with self.subTest(fields=fields):
                self.assertEqual(encode_instruction(fields), expected)

    def test_variable_sizes(self):
        """Блоки имеют длины 8, 7, 7, 7; общий размер равен 29."""
        text = (ROOT / "examples/spec.asm").read_text(encoding="utf-8")
        blocks = encode_program(parse_program(text))
        self.assertEqual(blocks, list(EXPECTED_BYTES))
        self.assertEqual([len(block) for block in blocks], [8, 7, 7, 7])
        self.assertEqual(len(b"".join(blocks)), 29)

    def test_maximum_values(self):
        """Старшие поля и резервные биты корректны на верхней границе."""
        cases = (
            ({"A": 5, "B": 1073741823, "C": 4194303},
             "E5 FF FF FF FF FF FF 01"),
            ({"A": 2, "B": 4194303, "C": 4194303},
             "E2 FF FF FF FF FF 01"),
            ({"A": 7, "B": 4194303, "C": 4194303},
             "E7 FF FF FF FF FF 01"),
            ({"A": 17, "B": 4194303, "C": 4194303},
             "F1 FF FF FF FF FF 01"),
        )
        for fields, expected in cases:
            with self.subTest(fields=fields):
                self.assertEqual(encode_instruction(fields),
                                 bytes.fromhex(expected))

    def test_zero_values(self):
        """Нулевые операнды сохраняют код операции и нужную длину."""
        cases = ((5, 8), (2, 7), (7, 7), (17, 7))
        for opcode, size in cases:
            fields = {"A": opcode, "B": 0, "C": 0}
            expected = bytes([opcode]) + bytes(size - 1)
            self.assertEqual(encode_instruction(fields), expected)

    def test_invalid_fields(self):
        """Неполные, лишние и некорректные поля отклоняются."""
        cases = (
            {}, {"A": 31}, {"A": True}, {"A": 5, "B": 1},
            {"A": 5, "B": -1, "C": 0},
            {"A": 5, "B": 1073741824, "C": 0},
            {"A": 5, "B": 0, "C": 4194304},
            {"A": 2, "B": 4194304, "C": 0},
            {"A": 2, "B": 0, "C": 1.5},
            {"A": 5, "B": 0, "C": 0, "D": 0},
        )
        for fields in cases:
            with self.subTest(fields=fields):
                with self.assertRaises(AssemblyError):
                    encode_instruction(fields)

    def fixture(self):
        """Создаёт временное файловое окружение для CLI."""
        fixture = test_main.MainTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        return fixture

    def test_cli_output(self):
        """CLI записывает 29 байт и печатает по строке на команду."""
        fixture = self.fixture()
        text = (ROOT / "examples/spec.asm").read_text(encoding="utf-8")
        fixture.source.write_text(text, encoding="utf-8")
        code, out, err = fixture.invoke("--test")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(fixture.output.read_bytes(), b"".join(EXPECTED_BYTES))
        expected = ["Размер двоичного файла: 29 байт"]
        expected.extend(format_bytes(block) for block in EXPECTED_BYTES)
        self.assertEqual(out.splitlines(), expected)
        code, out, err = fixture.invoke("--stage", "2")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out, "Размер двоичного файла: 29 байт\n")

    def test_invalid_source_preserves_output(self):
        """Ошибка исходника не заменяет прежний бинарный результат."""
        fixture = self.fixture()
        fixture.output.write_bytes(b"old result")
        fixture.source.write_text("M[0] = 1\nM[0] = -1", encoding="utf-8")
        code, out, err = fixture.invoke("--stage", "2")
        self.assertEqual((code, out), (1, ""))
        self.assertIn("Строка 2", err)
        self.assertEqual(fixture.output.read_bytes(), b"old result")


if __name__ == "__main__":
    unittest.main()
