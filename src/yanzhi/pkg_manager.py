# -*- coding: utf-8 -*-
"""知行包管理器

提供包的安装、发布、列表功能：
- 基于 Git 仓库协议
- yanpkg.toml 配置文件
- 依赖解析
"""
from __future__ import annotations

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Any


# 默认包仓库
DEFAULT_REGISTRY = 'https://github.com/zhixing-lang/packages'


@dataclass
class PackageInfo:
    """包信息"""
    name: str = ''
    version: str = '0.1.0'
    description: str = ''
    author: str = ''
    license: str = 'MIT'
    dependencies: dict[str, str] = field(default_factory=dict)
    source: str = ''  # Git 仓库地址


@dataclass
class YanpkgConfig:
    """yanpkg.toml 配置"""
    package: PackageInfo = field(default_factory=PackageInfo)

    def to_toml(self) -> str:
        """序列化为 TOML 格式"""
        lines = ['[package]']
        lines.append(f'name = "{self.package.name}"')
        lines.append(f'version = "{self.package.version}"')
        lines.append(f'description = "{self.package.description}"')
        lines.append(f'author = "{self.package.author}"')
        lines.append(f'license = "{self.package.license}"')
        if self.package.dependencies:
            lines.append('')
            lines.append('[dependencies]')
            for dep, ver in self.package.dependencies.items():
                lines.append(f'{dep} = "{ver}"')
        return '\n'.join(lines) + '\n'

    @classmethod
    def from_toml(cls, text: str) -> YanpkgConfig:
        """从 TOML 文本解析"""
        config = cls()
        section = None
        for line in text.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line == '[package]':
                section = 'package'
            elif line == '[dependencies]':
                section = 'dependencies'
            elif '=' in line:
                key, _, value = line.partition('=')
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if section == 'package':
                    if key == 'name':
                        config.package.name = value
                    elif key == 'version':
                        config.package.version = value
                    elif key == 'description':
                        config.package.description = value
                    elif key == 'author':
                        config.package.author = value
                    elif key == 'license':
                        config.package.license = value
                elif section == 'dependencies':
                    config.package.dependencies[key] = value
        return config


def get_packages_dir() -> Path:
    """获取包安装目录"""
    # 优先使用项目本地的 yan_packages/
    local = Path('yan_packages')
    if local.exists():
        return local
    # 否则使用用户目录
    home = Path.home()
    return home / '.zhixing' / 'packages'


def install_package(name: str, version: str = '') -> bool:
    """安装包"""
    packages_dir = get_packages_dir()
    packages_dir.mkdir(parents=True, exist_ok=True)

    # 检查是否已安装
    pkg_dir = packages_dir / name
    if pkg_dir.exists():
        print(f"  {name} 已安装")
        return True

    # 尝试从 Git 安装
    # 格式: registry/name
    git_url = f"{DEFAULT_REGISTRY}/{name}.git"

    print(f"  正在安装 {name}...")
    try:
        result = subprocess.run(
            ['git', 'clone', git_url, str(pkg_dir)],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            print(f"  已安装: {name}")
            return True
        else:
            # 清理失败的克隆
            if pkg_dir.exists():
                shutil.rmtree(pkg_dir)
            print(f"  安装失败: {result.stderr.strip()}")
            return False
    except FileNotFoundError:
        print("  错误: 需要安装 git")
        return False
    except subprocess.TimeoutExpired:
        print("  错误: 安装超时")
        return False


def uninstall_package(name: str) -> bool:
    """卸载包"""
    packages_dir = get_packages_dir()
    pkg_dir = packages_dir / name
    if not pkg_dir.exists():
        print(f"  {name} 未安装")
        return False
    shutil.rmtree(pkg_dir)
    print(f"  已卸载: {name}")
    return True


def list_packages() -> list[PackageInfo]:
    """列出已安装的包"""
    packages_dir = get_packages_dir()
    if not packages_dir.exists():
        return []

    packages = []
    for pkg_dir in sorted(packages_dir.iterdir()):
        if not pkg_dir.is_dir():
            continue
        # 读取包信息
        config_file = pkg_dir / 'yanpkg.toml'
        if config_file.exists():
            config = YanpkgConfig.from_toml(config_file.read_text(encoding='utf-8'))
            packages.append(config.package)
        else:
            packages.append(PackageInfo(name=pkg_dir.name))

    return packages


def resolve_dependencies(config: YanpkgConfig) -> list[str]:
    """解析依赖（简单拓扑排序）"""
    resolved = []
    visited = set()

    def visit(name: str, version: str = ''):
        if name in visited:
            return
        visited.add(name)
        # 递归解析依赖
        packages_dir = get_packages_dir()
        pkg_dir = packages_dir / name
        config_file = pkg_dir / 'yanpkg.toml'
        if config_file.exists():
            dep_config = YanpkgConfig.from_toml(config_file.read_text(encoding='utf-8'))
            for dep_name, dep_ver in dep_config.package.dependencies.items():
                visit(dep_name, dep_ver)
        resolved.append(name)

    for dep_name, dep_ver in config.package.dependencies.items():
        visit(dep_name, dep_ver)

    return resolved


def init_package(name: str) -> None:
    """初始化新包"""
    config = YanpkgConfig()
    config.package.name = name
    config.package.description = f'{name} 包'

    # 写入 yanpkg.toml
    toml_path = Path('yanpkg.toml')
    if toml_path.exists():
        print(f"  yanpkg.toml 已存在")
        return

    toml_path.write_text(config.to_toml(), encoding='utf-8')
    print(f"  已创建 yanpkg.toml")

    # 创建包目录结构
    src_dir = Path(name)
    src_dir.mkdir(exist_ok=True)
    init_file = src_dir / '__init__.yan'
    if not init_file.exists():
        init_file.write_text(f'# {name} 包\n', encoding='utf-8')
        print(f"  已创建 {name}/__init__.yan")


def publish_package() -> bool:
    """发布当前包"""
    toml_path = Path('yanpkg.toml')
    if not toml_path.exists():
        print("  错误: 未找到 yanpkg.toml")
        return False

    config = YanpkgConfig.from_toml(toml_path.read_text(encoding='utf-8'))
    if not config.package.name:
        print("  错误: yanpkg.toml 中缺少包名")
        return False

    print(f"  包名: {config.package.name}")
    print(f"  版本: {config.package.version}")
    print(f"  描述: {config.package.description}")

    # 检查 git 状态
    try:
        result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
        if result.stdout.strip():
            print("  警告: 有未提交的更改")
    except FileNotFoundError:
        pass

    print(f"  发布需要手动推送到 Git 仓库")
    return True
