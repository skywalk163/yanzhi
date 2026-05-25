"""
知行语言结构体系统
实现结构体定义、实例化和字段访问
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class StructDefinition:
    """结构体定义"""
    name: str
    fields: Dict[str, str]  # {字段名: 类型名}
    methods: Dict[str, Any] = field(default_factory=dict)  # {方法名: 函数}
    
    def create_instance(self, **kwargs) -> 'StructInstance':
        """创建实例"""
        # 检查必需字段
        for field_name in self.fields:
            if field_name not in kwargs:
                raise ValueError(f"结构体{self.name}缺少字段: {field_name}")
        
        # 检查未知字段
        for field_name in kwargs:
            if field_name not in self.fields:
                raise ValueError(f"结构体{self.name}没有字段: {field_name}")
        
        return StructInstance(self, kwargs)
    
    def add_method(self, name: str, func: Any):
        """添加方法"""
        self.methods[name] = func


@dataclass
class StructInstance:
    """结构体实例"""
    definition: StructDefinition
    fields: Dict[str, Any]
    
    def get_field(self, name: str) -> Any:
        """获取字段值"""
        if name in self.fields:
            return self.fields[name]
        if name in self.definition.methods:
            return self.definition.methods[name]
        raise AttributeError(f"结构体{self.definition.name}没有字段或方法: {name}")
    
    def set_field(self, name: str, value: Any) -> 'StructInstance':
        """设置字段值（返回新实例）"""
        if name not in self.fields:
            raise AttributeError(f"结构体{self.definition.name}没有字段: {name}")
        
        new_fields = self.fields.copy()
        new_fields[name] = value
        return StructInstance(self.definition, new_fields)
    
    def call_method(self, name: str, *args, **kwargs) -> Any:
        """调用方法"""
        if name not in self.definition.methods:
            raise AttributeError(f"结构体{self.definition.name}没有方法: {name}")
        
        method = self.definition.methods[name]
        # 将self作为第一个参数传递
        return method(self, *args, **kwargs)
    
    def __repr__(self) -> str:
        fields_str = ', '.join(f"{k}={v}" for k, v in self.fields.items())
        return f"{self.definition.name}({fields_str})"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, StructInstance):
            return False
        return (self.definition.name == other.definition.name and 
                self.fields == other.fields)


class StructRegistry:
    """结构体注册表"""
    
    def __init__(self):
        self.definitions: Dict[str, StructDefinition] = {}
    
    def register(self, definition: StructDefinition):
        """注册结构体"""
        self.definitions[definition.name] = definition
    
    def get(self, name: str) -> Optional[StructDefinition]:
        """获取结构体定义"""
        return self.definitions.get(name)
    
    def exists(self, name: str) -> bool:
        """检查结构体是否存在"""
        return name in self.definitions
    
    def create(self, name: str, **kwargs) -> StructInstance:
        """创建结构体实例"""
        definition = self.get(name)
        if definition is None:
            raise NameError(f"未定义的结构体: {name}")
        return definition.create_instance(**kwargs)


# 全局结构体注册表
_global_registry = None


def get_registry() -> StructRegistry:
    """获取全局结构体注册表"""
    global _global_registry
    if _global_registry is None:
        _global_registry = StructRegistry()
    return _global_registry


def define_struct(name: str, fields: Dict[str, str], methods: Dict[str, Any] = None) -> StructDefinition:
    """定义结构体"""
    registry = get_registry()
    definition = StructDefinition(name, fields, methods or {})
    registry.register(definition)
    return definition


def create_struct(name: str, **kwargs) -> StructInstance:
    """创建结构体实例"""
    return get_registry().create(name, **kwargs)


def get_field(obj: StructInstance, field: str) -> Any:
    """获取字段"""
    return obj.get_field(field)


def set_field(obj: StructInstance, field: str, value: Any) -> StructInstance:
    """设置字段"""
    return obj.set_field(field, value)


# 预定义一些常用结构体
def init_builtin_structs():
    """初始化内置结构体"""
    registry = get_registry()
    
    # Token结构体
    registry.register(StructDefinition(
        'Token',
        {'类型': '文', '值': '任意', '行': '数', '列': '数'}
    ))
    
    # Point结构体（示例）
    registry.register(StructDefinition(
        'Point',
        {'x': '数', 'y': '数'}
    ))


# 自动初始化
init_builtin_structs()
