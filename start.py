#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import subprocess
import time
import platform
import webbrowser

def check_python_version():
    """检查Python版本是否满足要求"""
    required_version = (3, 6)
    current_version = sys.version_info[:2]
    
    if current_version < required_version:
        print(f"错误: 需要Python 3.6或更高版本，当前版本为{sys.version}")
        return False
    return True

def check_dependencies():
    """检查依赖项是否已安装"""
    try:
        # 检查必要的依赖
        import requests
        import flask
        import schedule
        import psutil
        import Crypto
        return True
    except ImportError as e:
        print(f"错误: 缺少依赖项 - {e}")
        return False

def install_dependencies():
    """安装依赖项"""
    print("正在安装依赖项...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("依赖项安装完成！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"安装依赖项失败: {e}")
        return False

def is_port_in_use(port):
    """检查端口是否被占用"""
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    except:
        return False

def find_available_port(start_port=5000, max_attempts=10):
    """查找可用端口"""
    port = start_port
    for _ in range(max_attempts):
        if not is_port_in_use(port):
            return port
        port += 1
    print(f"警告: 无法找到可用端口，将尝试使用 {start_port}")
    return start_port

def start_daemon_mode(port):
    """以守护进程模式启动应用"""
    print("以守护进程模式启动应用...")
    
    # 检查是否为Windows系统
    is_windows = platform.system() == 'Windows'
    
    try:
        cmd = [sys.executable, "daemon.py", "-p", str(port)]
        
        # 在Windows上不使用-d参数
        if not is_windows:
            cmd.append("-d")
        
        if is_windows:
            # Windows系统下，使用subprocess.CREATE_NEW_CONSOLE标志创建一个新的控制台窗口
            # 注意：Windows下可能无法使用subprocess.Popen的creationflags参数
            try:
                import ctypes
                CREATE_NEW_CONSOLE = 0x00000010
                process = subprocess.Popen(
                    cmd, 
                    creationflags=CREATE_NEW_CONSOLE
                )
                print(f"应用已在新窗口中启动，端口: {port}")
            except (ImportError, AttributeError):
                # 如果无法使用creationflags，则使用普通方式启动
                print("无法创建新控制台窗口，将在当前窗口启动...")
                process = subprocess.Popen(cmd)
                print(f"应用已启动，端口: {port}")
        else:
            # Linux/Mac系统使用后台模式
            process = subprocess.Popen(cmd)
            print(f"守护进程已启动，端口: {port}")
        
        # 等待确认应用已启动
        time.sleep(3)
        print(f"访问地址: http://127.0.0.1:{port}")
        
        # 尝试自动打开浏览器
        try:
            webbrowser.open(f"http://127.0.0.1:{port}")
        except:
            pass
            
        return True
    except Exception as e:
        print(f"启动守护进程失败: {e}")
        return False

def start_direct_mode(port):
    """直接启动应用（非守护进程模式）"""
    print("直接启动应用...")
    
    try:
        cmd = [sys.executable, "app.py", str(port)]
        print(f"执行命令: {' '.join(cmd)}")
        print(f"访问地址: http://127.0.0.1:{port}")
        
        # 尝试自动打开浏览器
        try:
            webbrowser.open(f"http://127.0.0.1:{port}")
        except:
            pass
        
        # 启动应用并等待其完成（这将阻塞主进程）
        subprocess.call(cmd)
        return True
    except Exception as e:
        print(f"启动应用失败: {e}")
        return False

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="超星学习通自动签到系统启动脚本")
    parser.add_argument("-p", "--port", type=int, default=0, help="指定运行端口，默认自动选择")
    parser.add_argument("-d", "--direct", action="store_true", help="直接模式（非守护进程）")
    parser.add_argument("--install-deps", action="store_true", help="安装依赖项")
    
    args = parser.parse_args()
    
    # 打印欢迎信息
    print("=" * 60)
    print("  超星学习通自动签到系统 - 启动程序")
    print("=" * 60)
    print(f"操作系统: {platform.system()} {platform.release()}")
    
    # 检查Python版本
    if not check_python_version():
        return False
    
    # 安装依赖项（如果指定）
    if args.install_deps or not check_dependencies():
        if not install_dependencies():
            print("安装依赖项失败，程序将退出")
            return False
    
    # 确定端口
    port = args.port if args.port > 0 else find_available_port()
    
    # 启动系统
    if args.direct:
        return start_direct_mode(port)
    else:
        return start_daemon_mode(port)

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("程序启动失败")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n用户中断，程序退出")
    except Exception as e:
        print(f"发生异常: {e}")
        sys.exit(1) 