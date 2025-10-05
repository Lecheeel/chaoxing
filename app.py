#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
超星学习通自动签到系统 - 主启动脚本
正常模式启动，包含完整的系统检查和直接运行功能
"""

import os
import sys
import json
import time
import platform
import argparse
import webbrowser
from datetime import datetime

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ 未安装python-dotenv，将使用默认配置")
    print("建议运行: pip install python-dotenv")

def get_env_config():
    """获取环境变量配置"""
    return {
        'port': int(os.getenv('PORT', 5000)),
        'open_browser': os.getenv('OPEN_BROWSER', 'true').lower() in ('true', '1', 'yes', 'on'),
        'debug': os.getenv('DEBUG', 'false').lower() in ('true', '1', 'yes', 'on'),
        'secret_key': os.getenv('SECRET_KEY', 'chaoxing-auto-sign-secret-key-2024'),
        'log_level': os.getenv('LOG_LEVEL', 'INFO')
    }

def print_banner():
    """打印启动横幅"""
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║                超星学习通自动签到系统                          ║")
    print("║                    Web管理面板                                ║")
    print(f"║  启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                         ║")
    print("╚═══════════════════════════════════════════════════════════════╝")

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    print(f"🐍 Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version >= (3, 6):
        print("   ✅ Python版本满足要求")
        return True
    else:
        print("   ❌ Python版本过低，需要3.6或更高版本")
        return False

def check_dependencies():
    """检查依赖库"""
    print("📚 检查依赖库:")
    
    deps = {
        'flask': 'Flask Web框架',
        'psutil': '系统信息库', 
        'schedule': '定时任务库',
        'requests': 'HTTP请求库'
    }
    
    missing = []
    for module, desc in deps.items():
        try:
            __import__(module)
            print(f"   ✅ {desc}")
        except ImportError:
            print(f"   ❌ {desc} - 未安装")
            missing.append(module)
    
    if missing:
        print(f"\n❌ 缺少依赖: {', '.join(missing)}")
        print("请运行: pip install flask psutil schedule requests")
        return False
    
    return True

def check_project_structure():
    """检查项目结构"""
    print("📁 检查项目结构:")
    
    required_items = [
        ('functions', '功能模块目录'),
        ('webpanel', 'Web面板目录'),
        ('webpanel/app.py', 'Web应用文件'),
        ('functions/sign.py', '签到功能文件'),
        ('functions/user.py', '用户管理文件')
    ]
    
    all_ok = True
    for item, desc in required_items:
        if os.path.exists(item):
            print(f"   ✅ {desc}")
        else:
            print(f"   ❌ {desc} - 不存在")
            all_ok = False
    
    return all_ok

def ensure_directories():
    """确保必要目录存在"""
    dirs = ['configs', 'logs']
    for dir_name in dirs:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
            print(f"   📁 已创建目录: {dir_name}")

def check_web_modules():
    """检查Web模块是否可以正常导入"""
    print("🌐 检查Web模块:")
    
    try:
        from webpanel.app import create_app
        print("   ✅ Web应用模块正常")
        return True
    except ImportError as e:
        print(f"   ❌ Web应用模块导入失败: {e}")
        return False

def is_port_available(port):
    """检查端口是否可用"""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', port))
            return True
    except:
        return False

def find_available_port(start_port=None):
    """查找可用端口"""
    # 如果没有指定起始端口，使用环境变量默认值
    if start_port is None:
        env_config = get_env_config()
        start_port = env_config['port']
    
    port = start_port
    while port < start_port + 10:
        if is_port_available(port):
            return port
        port += 1
    return start_port  # 如果都不可用，返回默认端口

def start_web_app(port, debug=False, open_browser=True):
    """启动Web应用"""
    try:
        from webpanel.app import create_app
        app = create_app()
        
        print("\n" + "="*60)
        print("🚀 启动Web管理面板")
        print("="*60)
        print(f"📱 本地访问: http://127.0.0.1:{port}")
        print(f"🌍 网络访问: http://0.0.0.0:{port}")
        print("="*60)
        print("⚠️  使用Ctrl+C可以停止服务")
        print("="*60)
        
        # 自动打开浏览器
        if open_browser:
            try:
                import threading
                def open_browser():
                    time.sleep(1.5)  # 等待服务器启动
                    webbrowser.open(f"http://127.0.0.1:{port}")
                
                browser_thread = threading.Thread(target=open_browser)
                browser_thread.daemon = True
                browser_thread.start()
            except:
                pass
        
        # 启动应用
        app.run(
            debug=debug,
            host='0.0.0.0', 
            port=port,
            use_reloader=False,
            threaded=True
        )
        
    except Exception as e:
        print(f"❌ 启动Web应用失败: {e}")
        return False
    
    return True

def main():
    """主函数"""
    # 获取环境变量配置
    env_config = get_env_config()
    
    parser = argparse.ArgumentParser(description="超星学习通自动签到系统 - 主启动脚本")
    parser.add_argument('-p', '--port', type=int, default=0, help='指定端口，默认使用环境变量PORT或自动选择')
    parser.add_argument('--debug', action='store_true', help='开启调试模式（覆盖环境变量）')
    parser.add_argument('--no-browser', action='store_true', help='不自动打开浏览器（覆盖环境变量）')  
    parser.add_argument('--skip-check', action='store_true', help='跳过系统检查')
    
    args = parser.parse_args()
    
    # 确定最终配置（命令行参数优先于环境变量）
    final_port = args.port if args.port > 0 else env_config['port']
    final_debug = args.debug or env_config['debug']
    final_open_browser = not args.no_browser and env_config['open_browser']
    
    # 设置调试模式
    if final_debug:
        from utils.debug import set_debug_mode
        set_debug_mode(True)
    
    print_banner()
    
    # 系统检查
    if not args.skip_check:
        print("\n🔍 正在进行系统检查...")
        print("-" * 40)
        
        checks = [
            ("Python版本", check_python_version),
            ("依赖库", check_dependencies), 
            ("项目结构", check_project_structure),
            ("Web模块", check_web_modules)
        ]
        
        failed_checks = []
        for check_name, check_func in checks:
            if not check_func():
                failed_checks.append(check_name)
        
        if failed_checks:
            print(f"\n❌ 系统检查失败: {', '.join(failed_checks)}")
            print("请修复上述问题后重新启动")
            return False
        
        print("\n✅ 系统检查通过!")
    
    # 确保目录存在
    ensure_directories()
    
    # 确定端口
    if final_port > 0:
        port = final_port
        if not is_port_available(port):
            print(f"⚠️ 端口 {port} 不可用，自动选择其他端口...")
            port = find_available_port()
    else:
        port = find_available_port()
    
    # 显示配置信息
    print(f"\n📋 启动配置:")
    print(f"   端口: {port}")
    print(f"   调试模式: {'开启' if final_debug else '关闭'}")
    print(f"   自动打开浏览器: {'开启' if final_open_browser else '关闭'}")
    
    # 启动Web应用
    try:
        return start_web_app(
            port=port,
            debug=final_debug,
            open_browser=final_open_browser
        )
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，正在关闭服务...")
        return True
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 程序已退出")
    except Exception as e:
        print(f"❌ 发生异常: {e}")
        sys.exit(1) 