"""CLI первого этапа: разбор программы и вывод полей команд."""

import argparse
import sys
from pathlib import Path

from parser import format_fields, parse_program
from spec import AssemblyError

EXIT_OK = 0
EXIT_ERROR = 1
STAGE_PARSE = 1


def parse_args(argv):
    """Читает пути, тестовый режим и номер этапа."""
    parser = argparse.ArgumentParser(description="Ассемблер УВМ, вариант 22")
    parser.add_argument("-i", "--input", required=True, help="исходный .asm")
    parser.add_argument("-o", "--output", required=True, help="выходной .bin")
    parser.add_argument("--test", action="store_true", help="тестовый вывод")
    parser.add_argument(
        "--stage", type=int, choices=(STAGE_PARSE,), default=STAGE_PARSE
    )
    return parser.parse_args(argv)


def validate_paths(source, output):
    """Проверяет пути и запрещает запись поверх исходной программы."""
    if not source.is_file():
        raise AssemblyError(f"Исходный файл не найден: {source}")
    if source.resolve() == output.resolve():
        raise AssemblyError("Исходный и выходной файлы должны различаться")
    if output.exists() and source.samefile(output):
        raise AssemblyError("Исходный и выходной файлы должны различаться")
    if output.is_dir() or not output.parent.is_dir():
        raise AssemblyError(f"Некорректный выходной путь: {output}")


def run(args):
    """Разбирает исходник; на первом этапе бинарный файл не создаётся."""
    source, output = Path(args.input), Path(args.output)
    validate_paths(source, output)
    program = parse_program(source.read_text(encoding="utf-8-sig"))
    print(f"Команд разобрано: {len(program)}")
    if args.test:
        for instruction in program:
            print(format_fields(instruction))


def main(argv=None):
    """Возвращает 0 при успехе и 1 при ошибке программы или файлов."""
    args = parse_args(argv)
    try:
        run(args)
    except (AssemblyError, OSError, UnicodeError) as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return EXIT_ERROR
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
