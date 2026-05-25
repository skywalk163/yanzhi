"""
言知·主题链补全
利用中文"主题突出"特性，实现省略主语/宾语的上下文自动恢复。

工作原理：
  - 维护一个主题栈，记录最近提到的主题（主语/宾语/动作对象）
  - 当检测到省略（缺少主语或宾语）时，从栈中查找最匹配的引用
  - 按"最近引用 + 类型匹配"规则补全

示例：
  灯亮了。        → 主题栈: [灯], 动作: 灯.亮()
  调暗一点。      → 省略主语, 补全: 灯.调暗(值=降低)
"""
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from ..compiler.ast import ASTNode


@dataclass
class TopicEntry:
    """主题条目"""
    name: str                    # 主题名称（如"灯"）
    type_hint: str = ""          # 类型提示（如"device", "sensor"）
    last_action: str = ""        # 最近动作
    confidence: float = 1.0       # 置信度


class TopicChain:
    """主题链跟踪器"""
    
    def __init__(self, max_window: int = 3):
        self.stack: List[TopicEntry] = []
        self.max_window = max_window
    
    def update(self, subject: str, action: str = "", type_hint: str = ""):
        """更新主题栈"""
        entry = TopicEntry(name=subject, type_hint=type_hint, last_action=action)
        # 如果已存在同名主题，更新位置
        self.stack = [e for e in self.stack if e.name != subject]
        self.stack.append(entry)
        # 限制窗口大小
        if len(self.stack) > self.max_window:
            self.stack.pop(0)
    
    def resolve(self, query: str, type_hint: str = "") -> Optional[str]:
        """解析省略引用，返回最匹配的主题名"""
        for entry in reversed(self.stack):
            if type_hint and entry.type_hint != type_hint:
                continue
            # TODO: 更智能的模糊匹配
            return entry.name
        return None
    
    def clear(self):
        """清除主题栈"""
        self.stack.clear()
