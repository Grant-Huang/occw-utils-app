#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import subprocess
import sys
import time

def clear_flask_cache():
    """清空Flask应用的各种缓存"""
    
    print("🔄 开始清空Flask应用缓存...")
    print("=" * 50)
    
    # 1. 清空Python编译缓存
    print("\n📂 1. 清空Python编译缓存 (__pycache__)")
    print("-" * 30)
    
    cache_dirs = []
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            cache_dir = os.path.join(root, '__pycache__')
            cache_dirs.append(cache_dir)
    
    if cache_dirs:
        for cache_dir in cache_dirs:
            try:
                shutil.rmtree(cache_dir)
                print(f"✅ 已删除: {cache_dir}")
            except Exception as e:
                print(f"❌ 删除失败 {cache_dir}: {e}")
        print(f"📊 总共清理了 {len(cache_dirs)} 个__pycache__目录")
    else:
        print("ℹ️  没有发现__pycache__目录")
    
    # 2. 清空.pyc文件
    print("\n📄 2. 清空.pyc文件")
    print("-" * 30)
    
    pyc_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                pyc_file = os.path.join(root, file)
                pyc_files.append(pyc_file)
    
    if pyc_files:
        for pyc_file in pyc_files:
            try:
                os.remove(pyc_file)
                print(f"✅ 已删除: {pyc_file}")
            except Exception as e:
                print(f"❌ 删除失败 {pyc_file}: {e}")
        print(f"📊 总共清理了 {len(pyc_files)} 个.pyc文件")
    else:
        print("ℹ️  没有发现.pyc文件")
    
    # 3. 检查Flask进程
    print("\n🔍 3. 检查Flask进程")
    print("-" * 30)
    
    try:
        if os.name == 'nt':  # Windows
            result = subprocess.run(['tasklist'], capture_output=True, text=True)
            if 'python.exe' in result.stdout:
                print("⚠️  发现Python进程正在运行:")
                python_lines = [line for line in result.stdout.split('\n') if 'python.exe' in line]
                for line in python_lines:
                    print(f"   {line.strip()}")
                print("\n💡 建议手动关闭Flask服务后重新启动")
            else:
                print("✅ 没有发现Python进程")
        else:  # Unix/Linux
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            python_processes = [line for line in result.stdout.split('\n') if 'python' in line and 'app.py' in line]
            if python_processes:
                print("⚠️  发现Flask进程:")
                for process in python_processes:
                    print(f"   {process}")
                print("\n💡 建议使用 Ctrl+C 关闭Flask服务后重新启动")
            else:
                print("✅ 没有发现Flask进程")
    except Exception as e:
        print(f"❌ 检查进程失败: {e}")
    
    # 4. 清空临时文件
    print("\n🗑️  4. 清空临时文件")
    print("-" * 30)
    
    temp_patterns = ['*.tmp', '*.temp', 'temp_*', '*~']
    temp_files = []
    
    for root, dirs, files in os.walk('.'):
        for file in files:
            for pattern in temp_patterns:
                if pattern.startswith('*') and file.endswith(pattern[1:]):
                    temp_files.append(os.path.join(root, file))
                elif pattern.endswith('*') and file.startswith(pattern[:-1]):
                    temp_files.append(os.path.join(root, file))
    
    if temp_files:
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
                print(f"✅ 已删除: {temp_file}")
            except Exception as e:
                print(f"❌ 删除失败 {temp_file}: {e}")
        print(f"📊 总共清理了 {len(temp_files)} 个临时文件")
    else:
        print("ℹ️  没有发现临时文件")
    
    # 5. 给出重启建议
    print("\n🚀 5. 重启建议")
    print("-" * 30)
    print("为了确保所有缓存都被清空，建议按以下步骤操作：")
    print("1. 如果Flask服务正在运行，按 Ctrl+C 停止")
    print("2. 等待3秒")
    print("3. 重新启动Flask服务：")
    print("   python app.py")
    print("   或")
    print("   python start.py")
    print("\n🌐 浏览器缓存清理：")
    print("- Chrome: Ctrl+Shift+R 或 F12 -> Network -> Disable cache")
    print("- Firefox: Ctrl+Shift+R 或 F12 -> Network -> Disable cache")
    print("- Edge: Ctrl+Shift+R")
    
    print("\n" + "=" * 50)
    print("✅ Flask缓存清理完成！")

def restart_flask_service():
    """提供重启Flask服务的选项"""
    print("\n❓ 是否要自动重启Flask服务？(y/n): ", end="")
    choice = input().lower().strip()
    
    if choice in ['y', 'yes', '是']:
        print("\n🔄 正在重启Flask服务...")
        
        # 尝试启动Flask服务
        try:
            print("📍 当前目录:", os.getcwd())
            print("🚀 启动命令: python app.py")
            print("💡 按 Ctrl+C 可以停止服务")
            print("-" * 30)
            
            # 启动Flask应用
            subprocess.run([sys.executable, 'app.py'])
            
        except KeyboardInterrupt:
            print("\n⏹️  Flask服务已停止")
        except Exception as e:
            print(f"\n❌ 启动Flask服务失败: {e}")
            print("💡 请手动运行: python app.py")
    else:
        print("ℹ️  请手动重启Flask服务: python app.py")

if __name__ == "__main__":
    clear_flask_cache()
    restart_flask_service() 