#!/usr/bin/env python3
"""
项目结构展示脚本
"""

import os
from pathlib import Path

def show_tree(directory, prefix="", max_depth=3, current_depth=0):
    """递归显示目录树结构"""
    if current_depth >= max_depth:
        return
    
    directory = Path(directory)
    if not directory.exists():
        return
    
    items = sorted(directory.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
    
    for i, item in enumerate(items):
        if item.name.startswith('.'):
            continue
            
        is_last = i == len(items) - 1
        current_prefix = "└── " if is_last else "├── "
        print(f"{prefix}{current_prefix}{item.name}")
        
        if item.is_dir():
            extension = "    " if is_last else "│   "
            show_tree(item, prefix + extension, max_depth, current_depth + 1)

if __name__ == "__main__":
    print("离线文档知识图谱系统 - 项目结构")
    print("=" * 50)
    show_tree(".", max_depth=4)
