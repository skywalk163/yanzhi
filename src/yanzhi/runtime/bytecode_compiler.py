# -*- coding: utf-8 -*-
"""
[DEPRECATED] 字节码编译器（旧实现）

此文件包含重复的 OpCode 枚举、Instruction 和 VirtualMachine 实现。
已被 runtime/bytecode.py + runtime/vm.py + runtime/compiler_bc.py 取代。

请使用以下模块：
- 指令集定义 → bytecode.py (OpCode)
- 字节码编译器 → compiler_bc.py (compile_to_bytecode)
- 虚拟机执行器 → vm.py (VM)

此文件将在未来版本中彻底删除。
"""

# 仅保留导出以保证向后兼容
from yanzhi.runtime.bytecode import OpCode, Instruction, BytecodeChunk
from yanzhi.runtime.compiler_bc import compile_to_bytecode
from yanzhi.runtime.vm import VM, VMFunction
