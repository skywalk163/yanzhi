"""
知行语言模块加载器
实现模块导入和管理
"""

import os
import sys
from typing import Dict, List, Optional, Any
from pathlib import Path


class Module:
    """模块类"""
    
    def __init__(self, name: str, path: str):
        self.name = name
        self.path = path
        self.exports: Dict[str, Any] = {}
        self.default_export: Optional[Any] = None
        self.loaded = False
    
    def add_export(self, name: str, value: Any):
        """添加导出"""
        self.exports[name] = value
    
    def set_default(self, value: Any):
        """设置默认导出"""
        self.default_export = value
    
    def get_export(self, name: str) -> Any:
        """获取导出"""
        if name in self.exports:
            return self.exports[name]
        raise NameError(f"模块{self.name}中没有导出'{name}'")


class ModuleLoader:
    """模块加载器"""
    
    @staticmethod
    def _default_search_paths() -> List[str]:
        """获取默认搜索路径"""
        paths = [
            os.getcwd(),  # 当前目录
            os.path.join(os.getcwd(), 'src'),  # src目录
            os.path.join(os.getcwd(), 'src', 'yan', 'stdlib'),  # 标准库
        ]
        
        # 添加YAN_PATH环境变量中的路径
        yan_path = os.environ.get('YAN_PATH')
        if yan_path:
            paths.insert(0, yan_path)
        
        return paths
    
    def __init__(self, search_paths: List[str] = None):
        self.modules: Dict[str, Module] = {}
        self.search_paths = search_paths or []
        self.cache: Dict[str, Any] = {}
        
        # 添加默认搜索路径
        if not self.search_paths:
            self.search_paths = self._default_search_paths()
    
    def resolve_path(self, module_name: str) -> Optional[str]:
        """解析模块路径"""
        # 替换.为/
        module_path = module_name.replace('.', '/')
        
        # 尝试不同的扩展名
        extensions = ['.yan', '.py', '']
        
        for search_path in self.search_paths:
            for ext in extensions:
                full_path = os.path.join(search_path, module_path + ext)
                if os.path.exists(full_path):
                    return os.path.abspath(full_path)
        
        return None
    
    def load_module(self, module_name: str) -> Module:
        """加载模块"""
        # 检查缓存
        if module_name in self.modules:
            return self.modules[module_name]
        
        # 解析路径
        path = self.resolve_path(module_name)
        if path is None:
            raise ImportError(f"找不到模块: {module_name}")
        
        # 创建模块
        module = Module(module_name, path)
        self.modules[module_name] = module
        
        # 根据扩展名加载
        if path.endswith('.yan'):
            self._load_yan_module(module)
        elif path.endswith('.py'):
            self._load_py_module(module)
        else:
            # 尝试作为包加载
            self._load_package(module)
        
        module.loaded = True
        return module
    
    def load(self, module_name: str) -> Module:
        """加载模块（load_module的别名）"""
        return self.load_module(module_name)
    
    def _load_yan_module(self, module: Module):
        """加载.yan模块"""
        # 读取源码
        with open(module.path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # 编译和执行
        # 这里需要导入编译器，避免循环依赖
        from ..compiler.lexer import lex
        from ..compiler.parser import parse
        from ..runtime.evaluator import evaluate
        
        tokens = lex(source)
        ast = parse(tokens)
        
        # 创建模块环境
        from ..runtime.evaluator import Evaluator
        evaluator = Evaluator()
        
        # 执行模块代码
        result = evaluator.eval(ast)
        
        # 提取导出
        # TODO: 从AST中提取导出语句
        # 暂时将所有定义作为导出
        for name, value in evaluator.env.items():
            if not name.startswith('_'):
                module.add_export(name, value)
    
    def _load_py_module(self, module: Module):
        """加载Python模块"""
        # 使用Python的导入机制
        module_name = module.name.replace('/', '.')
        
        try:
            py_module = __import__(module_name)
            module.loaded = True
            
            # 提取所有非私有成员
            for name in dir(py_module):
                if not name.startswith('_'):
                    module.add_export(name, getattr(py_module, name))
        
        except ImportError as e:
            raise ImportError(f"无法导入Python模块{module_name}: {e}")
    
    def _load_package(self, module: Module):
        """加载包（目录）"""
        # 查找__init__.yan或__init__.py
        init_yan = os.path.join(module.path, '__init__.yan')
        init_py = os.path.join(module.path, '__init__.py')
        
        if os.path.exists(init_yan):
            module.path = init_yan
            self._load_yan_module(module)
        elif os.path.exists(init_py):
            module.path = init_py
            self._load_py_module(module)
        else:
            # 空包，加载目录下所有模块
            for filename in os.listdir(module.path):
                if filename.endswith('.yan') or filename.endswith('.py'):
                    sub_module_name = f"{module.name}.{filename.rsplit('.', 1)[0]}"
                    sub_module = self.load_module(sub_module_name)
                    # 合并导出
                    for name, value in sub_module.exports.items():
                        module.add_export(name, value)
    
    def import_module(self, module_name: str, alias: str = None) -> Dict[str, Any]:
        """导入模块"""
        module = self.load_module(module_name)
        
        if alias:
            # 返回带别名的字典
            return {alias: module}
        else:
            # 返回所有导出
            return module.exports
    
    def import_items(self, module_name: str, items: List[str]) -> Dict[str, Any]:
        """选择性导入"""
        module = self.load_module(module_name)
        result = {}
        
        for item in items:
            if item in module.exports:
                result[item] = module.exports[item]
            else:
                raise NameError(f"模块{module_name}中没有导出'{item}'")
        
        return result
    
    def add_builtin_module(self, name: str, exports: Dict[str, Any]):
        """添加内置模块"""
        module = Module(name, f"<builtin:{name}>")
        for export_name, value in exports.items():
            module.add_export(export_name, value)
        module.loaded = True
        self.modules[name] = module


# 全局模块加载器
_global_loader = None


def get_loader() -> ModuleLoader:
    """获取全局模块加载器"""
    global _global_loader
    if _global_loader is None:
        _global_loader = ModuleLoader()
    return _global_loader


def import_module(module_name: str, alias: str = None) -> Dict[str, Any]:
    """导入模块"""
    return get_loader().import_module(module_name, alias)


def import_items(module_name: str, items: List[str]) -> Dict[str, Any]:
    """选择性导入"""
    return get_loader().import_items(module_name, items)
