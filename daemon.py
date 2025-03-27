#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import signal
import subprocess
import logging
import argparse
import psutil
import atexit
import threading
import platform
from datetime import datetime
from logging.handlers import RotatingFileHandler

# 配置
APP_NAME = "超星学习通自动签到系统"
MAIN_SCRIPT = "app.py"  # 主应用脚本
CHECK_INTERVAL = 10  # 检查间隔(秒)
MAX_RESTART_COUNT = 5  # 最大重启次数(每天)
LOG_FILE = "logs/daemon.log"  # 守护进程日志

# 检测操作系统
IS_WINDOWS = platform.system() == 'Windows'

# 确保日志目录存在
if not os.path.exists('logs'):
    os.makedirs('logs')

# 配置日志
def setup_logging():
    logger = logging.getLogger('daemon')
    logger.setLevel(logging.INFO)
    
    # 防止重复添加处理器
    if not logger.handlers:
        # 文件处理器 (最大10MB, 保留5个备份)
        file_handler = RotatingFileHandler(
            LOG_FILE, 
            maxBytes=10*1024*1024, 
            backupCount=5,
            encoding='utf-8'
        )
        file_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(file_format)
        logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

# 应用进程
app_process = None
restart_count = 0
last_restart_day = None

def get_current_day():
    """获取当前日期，用于重置重启计数"""
    return datetime.now().strftime('%Y-%m-%d')

def signal_handler(sig, frame):
    """处理终止信号"""
    logger.info(f"收到信号 {sig}，正在停止守护进程...")
    
    if app_process:
        # 尝试正常停止子进程
        logger.info("正在停止应用进程...")
        try:
            if not IS_WINDOWS:
                # Linux/Mac下使用进程组信号
                os.killpg(os.getpgid(app_process.pid), signal.SIGINT)
            else:
                # Windows下直接终止进程
                app_process.terminate()
            
            # 等待进程终止
            for _ in range(5):  # 最多等待5秒
                if app_process.poll() is not None:
                    break
                time.sleep(1)
                
            # 如果仍在运行，则强制终止
            if app_process.poll() is None:
                logger.warning("应用进程未响应信号，强制终止...")
                app_process.terminate()
                app_process.wait(timeout=3)
                
        except Exception as e:
            logger.error(f"停止应用进程时出错: {e}")
            # 确保进程被终止
            try:
                app_process.kill()
            except:
                pass
    
    logger.info("守护进程已停止")
    sys.exit(0)

def check_process_cpu_memory(pid):
    """检查进程的CPU和内存使用情况"""
    try:
        process = psutil.Process(pid)
        cpu_percent = process.cpu_percent(interval=1)
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024)  # MB
        
        return cpu_percent, memory_mb
    except:
        return None, None

def start_app(port=5000):
    """启动应用进程"""
    global app_process
    
    logger.info(f"正在启动 {APP_NAME}...")
    
    try:
        # 使用subprocess启动应用
        cmd = [sys.executable, MAIN_SCRIPT, str(port)]
        
        # 根据不同平台设置启动参数
        popen_kwargs = {
            'stdout': subprocess.PIPE,
            'stderr': subprocess.STDOUT,
            'universal_newlines': True,
        }
        
        # 仅在非Windows系统使用preexec_fn
        if not IS_WINDOWS:
            popen_kwargs['preexec_fn'] = os.setsid  # 创建新的进程组，便于后续发送信号
        
        app_process = subprocess.Popen(cmd, **popen_kwargs)
        
        logger.info(f"应用已启动，PID: {app_process.pid}, 端口: {port}")
        
        # 启动日志监控线程
        monitor_log_thread = threading.Thread(target=monitor_app_log)
        monitor_log_thread.daemon = True
        monitor_log_thread.start()
        
        return True
    except Exception as e:
        logger.error(f"启动应用失败: {e}")
        return False

def monitor_app_log():
    """监控应用输出并转发到守护进程日志"""
    global app_process
    
    while app_process and app_process.poll() is None:
        try:
            # 读取一行日志
            line = app_process.stdout.readline()
            if line:
                line = line.strip()
                # 转发到守护进程日志
                if line:
                    logger.info(f"[APP] {line}")
        except Exception as e:
            logger.error(f"读取应用日志失败: {e}")
            break
    
    logger.info("应用日志监控线程已退出")

def restart_app(port=5000):
    """重启应用进程"""
    global app_process, restart_count, last_restart_day
    
    # 检查并重置每日重启计数
    current_day = get_current_day()
    if last_restart_day != current_day:
        restart_count = 0
        last_restart_day = current_day
    
    # 检查今日重启次数
    if restart_count >= MAX_RESTART_COUNT:
        logger.error(f"达到今日最大重启次数 ({MAX_RESTART_COUNT})，不再尝试重启")
        return False
    
    # 递增重启计数
    restart_count += 1
    
    # 停止旧进程
    if app_process:
        logger.info(f"正在停止旧进程 (PID: {app_process.pid})...")
        try:
            if not IS_WINDOWS:
                # Linux/Mac下使用进程组信号
                os.killpg(os.getpgid(app_process.pid), signal.SIGINT)
            else:
                # Windows下直接终止进程
                app_process.terminate()
            
            # 等待进程终止
            for _ in range(5):  # 最多等待5秒
                if app_process.poll() is not None:
                    break
                time.sleep(1)
                
            # 如果仍在运行，则强制终止
            if app_process.poll() is None:
                logger.warning("应用进程未响应，强制终止...")
                app_process.terminate()
                try:
                    app_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    logger.warning("终止超时，强制杀死进程...")
                    app_process.kill()
        except Exception as e:
            logger.error(f"停止旧进程时出错: {e}")
            # 确保进程被终止
            try:
                app_process.kill()
            except:
                pass
    
    # 等待一段时间再重启
    logger.info(f"等待3秒后重启应用 (今日第 {restart_count}/{MAX_RESTART_COUNT} 次重启)...")
    time.sleep(3)
    
    # 启动新进程
    return start_app(port)

def monitor_app(port=5000):
    """主监控循环，检查应用进程状态并在需要时重启"""
    global app_process, last_restart_day
    
    # 初始化每日重启计数
    last_restart_day = get_current_day()
    
    # 启动应用
    if not start_app(port):
        logger.error("首次启动应用失败，退出守护进程")
        return
    
    # 主循环
    while True:
        try:
            # 检查应用进程状态
            if app_process.poll() is not None:
                exit_code = app_process.returncode
                logger.warning(f"应用进程已退出，退出码: {exit_code}")
                
                # 重启应用
                if not restart_app(port):
                    logger.error("重启应用失败，守护进程将退出")
                    break
            else:
                # 检查进程资源使用情况
                cpu_percent, memory_mb = check_process_cpu_memory(app_process.pid)
                if cpu_percent is not None:
                    # 仅记录异常资源使用情况
                    if cpu_percent > 80 or memory_mb > 500:
                        logger.warning(f"应用资源使用: CPU {cpu_percent:.1f}%, 内存 {memory_mb:.1f}MB")
                
                # 检查进程是否响应
                try:
                    # 可以在这里实现更复杂的健康检查，如HTTP请求
                    pass
                except Exception as e:
                    logger.error(f"健康检查失败: {e}")
            
            # 等待下次检查
            time.sleep(CHECK_INTERVAL)
            
        except Exception as e:
            logger.error(f"监控循环出错: {e}")
            time.sleep(CHECK_INTERVAL)  # 发生错误时也等待

def main():
    """主函数，解析命令行参数并启动守护进程"""
    parser = argparse.ArgumentParser(description=f'{APP_NAME} 守护进程')
    parser.add_argument('-p', '--port', type=int, default=5000, help='应用监听端口，默认5000')
    parser.add_argument('-d', '--detach', action='store_true', help='后台运行')
    
    args = parser.parse_args()
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # 终止信号
    
    # 输出启动信息
    logger.info("=" * 50)
    logger.info(f"{APP_NAME} 守护进程启动")
    logger.info(f"操作系统: {platform.system()} {platform.release()}")
    logger.info(f"端口: {args.port}, 进程ID: {os.getpid()}")
    logger.info("=" * 50)
    
    # 如果需要后台运行，将进程分离 (仅支持非Windows系统)
    if args.detach and not IS_WINDOWS:
        try:
            # 分离前记录PID
            pid = os.fork()
            if pid > 0:
                logger.info(f"守护进程已分离，PID: {pid}")
                sys.exit(0)
        except OSError as e:
            logger.error(f"无法分离进程: {e}")
            sys.exit(1)
    elif args.detach and IS_WINDOWS:
        logger.warning("Windows系统不支持后台分离运行模式，将以前台模式运行")
    
    # 启动监控
    try:
        monitor_app(args.port)
    except KeyboardInterrupt:
        logger.info("收到键盘中断，退出守护进程")
    except Exception as e:
        logger.error(f"守护进程异常: {e}")
    finally:
        # 确保应用进程被终止
        if app_process and app_process.poll() is None:
            try:
                app_process.terminate()
                app_process.wait(timeout=3)
            except:
                pass

if __name__ == "__main__":
    main() 