#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from webpanel.app import app
from schedule_task import initialize_scheduler

if __name__ == "__main__":
    # 设置端口，默认为5000
    port = 5000
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
        
    print("="*50)
    print("超星学习通自动签到系统 - Web管理面板")
    print("="*50)
    print(f"访问地址: http://127.0.0.1:{port}")
    print("使用Ctrl+C可以停止服务")
    print("="*50)
    
    # 初始化定时任务调度器
    initialize_scheduler()
    print("定时任务调度器已启动")
    print("="*50)
    
    # 启动Flask应用
    app.run(debug=True, host='0.0.0.0', port=port) 