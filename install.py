#!/usr/bin/env python3
# install_submodules.py

import os
import subprocess
import sys
from pathlib import Path
import argparse

def install_submodule(path):
    """安装单个子模块"""
    try:
        print(f"正在安装: {path}")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-e", str(path)
        ], capture_output=True, text=True, check=True)
        
        print(f"✅ 成功安装: {path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 安装失败: {path}")
        print(f"错误信息: {e.stderr}")
        return False

def find_submodules(root_dir="./"):
    """查找所有子模块目录"""
    submodules = []
    root_path = Path(root_dir)
    
    # 查找所有包含 setup.py 或 pyproject.toml 的子目录
    for item in root_path.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            has_setup_py = (item / "setup.py").exists()
            has_pyproject = (item / "pyproject.toml").exists()
            if has_setup_py or has_pyproject:
                submodules.append(item)
    
    return submodules

def install_requirements(requirements_file):
    """安装requirements.txt中的依赖"""
    try:
        print(f"📦 安装依赖: {requirements_file}")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], capture_output=True, text=True, check=True)
        
        print(f"✅ 成功安装依赖: {requirements_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 安装依赖失败: {requirements_file}")
        print(f"错误信息: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"⚠️  未找到依赖文件: {requirements_file}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='安装项目依赖和子模块')
    parser.add_argument('--requirements', '-r', 
                       default='project_noui/requirements.txt',
                       help='requirements.txt文件路径 (默认: project_noui/requirements.txt)')
    parser.add_argument('--submodules-only', '-s', action='store_true',
                       help='仅安装子模块，不安装requirements.txt')
    parser.add_argument('--requirements-only', '-R', action='store_true',
                       help='仅安装requirements.txt，不安装子模块')
    
    args = parser.parse_args()
    
    success_count = 0
    total_count = 0

    # 安装子模块
    if not args.requirements_only:
        print("🔍 搜索子模块...")
        submodules = find_submodules()
        
        if not submodules:
            print("❌ 未找到任何子模块")
        else:
            print(f"📦 找到 {len(submodules)} 个子模块:")
            for module in submodules:
                print(f"  - {module.name}")
            
            print("\n🚀 开始安装子模块...")
            total_count += len(submodules)
            
            for module in submodules:
                if install_submodule(module):
                    success_count += 1
                print("-" * 50)
    
    # 安装requirements.txt中的依赖
    if not args.submodules_only:
        requirements_path = Path(args.requirements)
        if requirements_path.exists():
            total_count += 1
            if install_requirements(requirements_path):
                success_count += 1
            print("-" * 50)
        else:
            print(f"⚠️  未找到requirements文件: {requirements_path}")
    
    print(f"\n📊 安装完成: {success_count}/{total_count} 成功")

if __name__ == "__main__":
    main()    
