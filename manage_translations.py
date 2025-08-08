#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
翻译管理工具
"""

import os
import sys
import argparse
from babel.messages import frontend as babel

def init_translations():
    """初始化翻译目录"""
    print("初始化翻译目录...")
    os.system('pybabel init -i messages.pot -d translations -l zh')
    os.system('pybabel init -i messages.pot -d translations -l en')
    os.system('pybabel init -i messages.pot -d translations -l fr')
    print("翻译目录初始化完成！")

def extract_messages():
    """提取消息"""
    print("提取消息...")
    os.system('pybabel extract -F babel.cfg -k _l -o messages.pot .')
    print("消息提取完成！")

def update_translations():
    """更新翻译"""
    print("更新翻译...")
    os.system('pybabel update -i messages.pot -d translations')
    print("翻译更新完成！")

def compile_translations():
    """编译翻译"""
    print("编译翻译...")
    os.system('pybabel compile -d translations')
    print("翻译编译完成！")

def main():
    parser = argparse.ArgumentParser(description='翻译管理工具')
    parser.add_argument('command', choices=['init', 'extract', 'update', 'compile', 'all'],
                       help='要执行的命令')
    
    args = parser.parse_args()
    
    if args.command == 'init':
        init_translations()
    elif args.command == 'extract':
        extract_messages()
    elif args.command == 'update':
        update_translations()
    elif args.command == 'compile':
        compile_translations()
    elif args.command == 'all':
        extract_messages()
        update_translations()
        compile_translations()

if __name__ == '__main__':
    main()
