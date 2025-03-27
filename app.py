#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
import time
import signal
import atexit
from logging.handlers import RotatingFileHandler
import traceback

# 设置环境变量，告诉Flask在生产环境中运行
os.environ['FLASK_ENV'] = 'production'

# 配置日志
def setup_logging():
    # 确保日志目录存在
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 配置根日志记录器
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 配置控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    
    # 配置文件处理器 (自动轮换，最大10MB，保留5个备份)
    file_handler = RotatingFileHandler(
        'logs/app.log', 
        maxBytes=10*1024*1024, 
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_format = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
    file_handler.setFormatter(file_format)
    
    # 添加处理器到根记录器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# 注册终止处理程序
def register_exit_handlers(scheduler_stop_func):
    def exit_handler():
        logging.info("程序正在退出，清理资源...")
        scheduler_stop_func()
        logging.info("资源清理完成，程序退出")
    
    def signal_handler(sig, frame):
        logging.info(f"接收到信号 {sig}，开始关闭程序...")
        exit_handler()
        sys.exit(0)
    
    # 注册普通退出处理程序
    atexit.register(exit_handler)
    
    # 注册信号处理程序
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # 终止信号

def restart_flask_app():
    from webpanel.app import app
    from schedule_task import stop_scheduler_thread, initialize_scheduler
    
    # 停止现有调度器
    stop_scheduler_thread()
    
    # 重新初始化调度器
    initialize_scheduler()
    
    # 重启Flask应用
    logging.info("正在重启Flask应用...")
    
    # 返回Flask应用实例
    return app

def main():
    # 设置日志
    logger = setup_logging()
    
    try:
        logging.info("=" * 50)
        logging.info("超星学习通自动签到系统 - 正在启动")
        logging.info("=" * 50)
        
        # 导入必要模块
        from webpanel.app import app
        from schedule_task import initialize_scheduler, stop_scheduler_thread
        
        # 注册退出处理程序
        register_exit_handlers(stop_scheduler_thread)
        
        # 初始化定时任务调度器
        initialize_scheduler()
        logging.info("定时任务调度器已启动")
        
        # 设置端口，默认为5000
        port = 5000
        if len(sys.argv) > 1 and sys.argv[1].isdigit():
            port = int(sys.argv[1])
        
        # 打印访问信息
        logging.info(f"访问地址: http://127.0.0.1:{port}")
        logging.info("使用Ctrl+C可以停止服务")
        logging.info("=" * 50)
        
        # 启动Flask应用 (生产环境模式)
        app.run(debug=False, host='0.0.0.0', port=port, threaded=True)
        
    except Exception as e:
        # 记录详细异常信息
        logging.error(f"程序启动失败: {str(e)}")
        logging.error(traceback.format_exc())
        
        # 尝试重启应用
        try:
            logging.info("尝试重启应用...")
            time.sleep(5)  # 等待5秒钟
            
            # 重启Flask应用
            app = restart_flask_app()
            
            # 重新启动应用
            logging.info("重启应用成功，继续运行...")
            app.run(debug=False, host='0.0.0.0', port=port, threaded=True)
            
        except Exception as restart_error:
            logging.error(f"重启应用失败: {str(restart_error)}")
            logging.error(traceback.format_exc())
            sys.exit(1)

if __name__ == "__main__":
    main() 