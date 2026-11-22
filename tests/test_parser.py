"""Проверки алгебраического языка и полей варианта 22."""

import unittest
from pathlib import Path

from parser import format_fields, parse_program
from spec import AssemblyError

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = [
    {"A": 5, "B": 241, "C": 997},
    {"A": 2, "B": 416, "C": 603},
    {"A": 7, "B": 277, "C": 783},
    {"A": 17, "B": 387, "C": 153},
]


class ParserTests(unittest.TestCase):
    """Синтаксис, направления обращения к памяти и диапазоны полей."""

    def test_specification(self):
        """Все четыре строки дают поля, указанные в методичке."""
        text = (ROOT / "examples/spec.asm").read_text(encoding="utf-8")
        self.assertEqual(parse_program(text), EXPECTED)
        self.assertEqual(format_fields(EXPECTED[0]), "A=5, B=241, C=997")

    def test_comments_spaces_and_hex(self):
        """Пробелы, табуляция, регистр букв, hex и комментарии разрешены."""
        text = "# начало\n\n m [ 0x3E5 ]\t= 0xF1 # константа\n"
        self.assertEqual(parse_program(text), [EXPECTED[0]])
        text = "m [ m [ 153 ] ] = SQRT ( m [ m [ 387 ] ] )"
        self.assertEqual(parse_program(text), [EXPECTED[3]])

    def test_boundaries(self):
        """Минимумы и максимумы константы и адресов допустимы."""
        text = "\n".join([
            "M[0] = 0", "M[4194303] = 1073741823",
            "M[4194303] = M[M[0]]", "M[M[4194303]] = M[0]",
            "M[M[0]] = sqrt(M[M[4194303]])",
        ])
        self.assertEqual(len(parse_program(text)), 5)

    def test_invalid_syntax(self):
        """Неподдерживаемые выражения и неправильные скобки отклоняются."""
        cases = (
            "", "# пусто", "LOAD_CONST 241, 997", "M[0] = -1",
            "M[0] = 1.5", "M[0] = 1 + 2", "M[0] = 0x",
            "M[0] = M[1]", "M[M[0]] = 1", "M[0] = sqrt(M[M[1]])",
            "M[M[0]] = sqrt(M[1])", "M[M[0]] = abs(M[M[1]])",
            "M[0] == 1", "M[0 = 1", "M[0] = 1 junk",
        )
        for text in cases:
            with self.subTest(text=text):
                with self.assertRaises(AssemblyError):
                    parse_program(text)

    def test_out_of_range(self):
        """Каждое адресное поле и 30-битная константа проверяются."""
        cases = (
            "M[4194304] = 0", "M[0] = 1073741824",
            "M[0] = M[M[4194304]]", "M[4194304] = M[M[0]]",
            "M[M[4194304]] = M[0]", "M[M[0]] = M[4194304]",
            "M[M[4194304]] = sqrt(M[M[0]])",
            "M[M[0]] = sqrt(M[M[4194304]])",
        )
        for text in cases:
            with self.subTest(text=text):
                with self.assertRaises(AssemblyError):
                    parse_program(text)

    def test_line_number(self):
        """Номер ошибки учитывает комментарии и пустые строки."""
        with self.assertRaisesRegex(AssemblyError, "Строка 3"):
            parse_program("# комментарий\n\nM[0] = -1")


if __name__ == "__main__":
    unittest.main()
