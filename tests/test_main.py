"""Проверки CLI первого этапа и ошибок файлов."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from main import main


class MainTests(unittest.TestCase):
    """Запуск CLI с временными исходными и выходными файлами."""

    def setUp(self):
        """Готовит отдельную папку и корректный исходник с UTF-8 BOM."""
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        self.root = Path(holder.name)
        self.source = self.root / "source.asm"
        self.output = self.root / "program.bin"
        self.source.write_text(
            "M[M[153]] = sqrt(M[M[387]])\n", encoding="utf-8-sig"
        )

    def invoke(self, *extra):
        """Возвращает код, stdout и stderr вызова CLI."""
        args = ["-i", str(self.source), "-o", str(self.output), *extra]
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(args)
        return code, out.getvalue(), err.getvalue()

    def test_stage_one(self):
        """Первый этап печатает поля и не создаёт бинарный файл."""
        code, out, err = self.invoke("--stage", "1", "--test")
        self.assertEqual((code, err), (0, ""))
        self.assertIn("A=17, B=387, C=153", out)
        self.assertFalse(self.output.exists())

    def test_without_test_mode(self):
        """Обычный режим первого этапа не печатает внутренние поля."""
        code, out, err = self.invoke("--stage", "1")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out, "Команд разобрано: 1\n")

    def test_missing_source_and_output_directory(self):
        """Отсутствующий исходник и выходная папка дают код 1."""
        self.output = self.root / "missing" / "program.bin"
        self.assertEqual(self.invoke("--stage", "1")[0], 1)
        self.source.unlink()
        self.assertEqual(self.invoke("--stage", "1")[0], 1)

    def test_same_file(self):
        """Исходник защищён от записи в тот же путь."""
        before = self.source.read_bytes()
        self.output = self.source
        code, _, err = self.invoke("--stage", "1")
        self.assertEqual(code, 1)
        self.assertIn("должны различаться", err)
        self.assertEqual(self.source.read_bytes(), before)

    def test_invalid_source(self):
        """Ошибка программы выводится в stderr без traceback."""
        self.source.write_text("BAD R0", encoding="utf-8")
        code, out, err = self.invoke("--stage", "1")
        self.assertEqual((code, out), (1, ""))
        self.assertIn("Строка 1", err)


if __name__ == "__main__":
    unittest.main()
