"""Проверки CLI интерпретатора и XML-дампа."""

import io
import tempfile
import unittest
import xml.etree.ElementTree as etree
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import interpreter
from test_parser import ROOT
from test_vm import assemble


class InterpreterTests(unittest.TestCase):
    """Дамп создаётся после успешного исполнения и не затирает программу."""

    def setUp(self):
        """Создаёт временные пути и бинарную программу копирования."""
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.source = Path(directory.name) / "program.bin"
        self.output = Path(directory.name) / "dump.xml"
        text = (ROOT / "examples/copy.asm").read_text(encoding="utf-8")
        self.source.write_bytes(assemble(text))

    def invoke(self, *extra):
        """Запускает CLI с перехватом вывода и кода завершения."""
        args = [
            "-i", str(self.source), "-o", str(self.output),
            "--start", "2000", "--end", "2002", *extra,
        ]
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            result = interpreter.main(args)
        return result, out.getvalue(), err.getvalue()

    def test_xml_dump(self):
        """XML содержит границы, адреса и значения скопированного массива."""
        result, out, err = self.invoke()
        self.assertEqual((result, err), (0, ""))
        self.assertIn("Выполнено команд: 15", out)
        root = etree.parse(self.output).getroot()
        self.assertEqual(root.tag, "memory")
        self.assertEqual(root.attrib, {"start": "2000", "end": "2002"})
        self.assertEqual(
            [(cell.get("address"), cell.text) for cell in root],
            [("2000", "10"), ("2001", "20"), ("2002", "30")],
        )

    def test_same_path(self):
        """Дамп не записывается поверх входного бинарного файла."""
        original = self.source.read_bytes()
        result, out, err = self.invoke("-o", str(self.source))
        self.assertEqual((result, out), (1, ""))
        self.assertIn("должны различаться", err)
        self.assertEqual(self.source.read_bytes(), original)

    def test_invalid_program_preserves_dump(self):
        """Ошибка в конце программы не изменяет прежний файл результата."""
        self.output.write_text("old dump", encoding="utf-8")
        self.source.write_bytes(self.source.read_bytes() + b"\x00")
        result, out, err = self.invoke()
        self.assertEqual((result, out), (1, ""))
        self.assertIn("Байт 114", err)
        self.assertEqual(self.output.read_text("utf-8"), "old dump")

    def test_invalid_range(self):
        """Диапазон с концом меньше начала не создаёт выходного файла."""
        result, out, err = self.invoke("--start", "2003")
        self.assertEqual((result, out), (1, ""))
        self.assertIn("диапазона", err)
        self.assertFalse(self.output.exists())

    def test_missing_input(self):
        """Отсутствующий бинарный файл даёт сообщение и код 1."""
        self.source.unlink()
        result, out, err = self.invoke()
        self.assertEqual((result, out), (1, ""))
        self.assertIn("не найден", err)
