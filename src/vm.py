"""Интерпретатор варианта 22 с единой памятью команд и данных."""

from decoder import command_for, decode_instruction
from memory import ZERO, ExecutionError, Memory
from spec import LOAD_CONST, READ_MEM, WRITE_MEM, AssemblyError


class VirtualMachine:
    """Выбирает команды из изменяемой памяти и исполняет их по порядку."""

    def __init__(self, code):
        """Создаёт память, границу программы и счётчики исполнения."""
        if not code:
            raise ExecutionError("Пустая программа")
        self.memory = Memory(code)
        self.program_size = len(code)
        self.pc = ZERO
        self.steps = ZERO
        self.operations = {
            LOAD_CONST: self.load_constant,
            READ_MEM: self.read_memory,
            WRITE_MEM: self.write_memory,
        }

    def load_constant(self, instruction):
        """Выполняет M[C] = B."""
        self.memory.write(instruction["C"], instruction["B"])

    def read_memory(self, instruction):
        """Выполняет M[C] = M[M[B]]."""
        source = self.memory.read(instruction["B"])
        self.memory.write(instruction["C"], self.memory.read(source))

    def write_memory(self, instruction):
        """Выполняет M[M[B]] = M[C]."""
        target = self.memory.read(instruction["B"])
        self.memory.write(target, self.memory.read(instruction["C"]))

    def fetch(self):
        """Читает текущие байты команды из общей памяти и декодирует их."""
        first_byte = self.memory.read_bytes(self.pc, 1)[0]
        size = command_for(first_byte).size
        if self.pc + size > self.program_size:
            raise ExecutionError("Неполная команда в конце программы")
        block = self.memory.read_bytes(self.pc, size)
        return decode_instruction(block), size

    def run(self):
        """Исполняет команды до границы загруженного бинарного файла."""
        while self.pc < self.program_size:
            try:
                instruction, size = self.fetch()
                operation = self.operations.get(instruction["A"])
                if operation is None:
                    raise ExecutionError("Операция пока не реализована")
                operation(instruction)
            except (AssemblyError, ExecutionError) as exc:
                raise ExecutionError(f"Байт {self.pc}: {exc}") from exc
            self.pc += size
            self.steps += 1
