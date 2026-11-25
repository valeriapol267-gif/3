"""CLI интерпретатора варианта 22 с дампом общей памяти в XML."""

import argparse
import sys
import xml.etree.ElementTree as etree
from pathlib import Path

from main import EXIT_ERROR, EXIT_OK, validate_paths
from memory import ExecutionError, check_range
from spec import AssemblyError
from vm import VirtualMachine


def parse_args(argv):
    """Читает бинарный файл, путь XML и включительный диапазон адресов."""
    parser = argparse.ArgumentParser(description="Интерпретатор, вариант 22")
    parser.add_argument("-i", "--input", required=True, help="входной .bin")
    parser.add_argument("-o", "--output", required=True, help="дамп XML")
    parser.add_argument(
        "--start", type=int, required=True, help="первый адрес",
    )
    parser.add_argument(
        "--end", type=int, required=True, help="последний адрес",
    )
    return parser.parse_args(argv)


def save_dump(memory, output, start, end):
    """Сохраняет выбранные ячейки памяти как XML с адресами и значениями."""
    root = etree.Element("memory", start=str(start), end=str(end))
    for address, value in memory.dump(start, end).items():
        etree.SubElement(root, "cell", address=address).text = str(value)
    tree = etree.ElementTree(root)
    etree.indent(tree, space="  ")
    tree.write(output, encoding="utf-8", xml_declaration=True)


def run(args):
    """Исполняет программу и записывает XML после успешного выполнения."""
    source, output = Path(args.input), Path(args.output)
    validate_paths(source, output)
    check_range(args.start, args.end)
    machine = VirtualMachine(source.read_bytes())
    machine.run()
    save_dump(machine.memory, output, args.start, args.end)
    print(f"Выполнено команд: {machine.steps}")
    print(f"Дамп памяти: {output}")


def main(argv=None):
    """Возвращает код завершения и выводит сообщение при ошибке."""
    args = parse_args(argv)
    try:
        run(args)
    except (AssemblyError, ExecutionError, OSError, UnicodeError) as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return EXIT_ERROR
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
