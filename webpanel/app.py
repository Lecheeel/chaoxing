# -*- coding: utf-8 -*-
"""
Flask应用主文件
"""

from flask import Flask, render_template, request, jsonify
from werkzeug.exceptions import HTTPException
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from webpanel.blueprints.sign import sign_bp
from webpanel.blueprints.user import user_bp
from webpanel.blueprints.system import system_bp
from webpanel.blueprints.api import api_bp

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 确保日志目录存在
if not os.path.exists('logs'):
    os.makedirs('logs')

# 配置Web应用日志
def setup_webapp_logging():
    """配置Web应用日志"""
    logger = logging.getLogger('webpanel')
    logger.setLevel(logging.INFO)
    
    # 防止重复添加处理器
    if not logger.handlers:
        # 文件处理器 (最大10MB, 保留5个备份)
        file_handler = RotatingFileHandler(
            'logs/webpanel.log', 
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

# 配置应用日志
def setup_app_logging():
    """配置应用日志"""
    logger = logging.getLogger('app')
    logger.setLevel(logging.INFO)
    
    # 防止重复添加处理器
    if not logger.handlers:
        # 文件处理器 (最大10MB, 保留5个备份)
        file_handler = RotatingFileHandler(
            'logs/app.log', 
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

# 初始化日志记录器
webpanel_logger = setup_webapp_logging()
app_logger = setup_app_logging()

# 尝试导入调度器功能
try:
    from utils.schedule_task import initialize_scheduler
    scheduler_available = True
    app_logger.info("调度器模块导入成功")
except ImportError as e:
    print(f"调度器模块导入失败: {e}")
    app_logger.warning(f"调度器模块导入失败: {e}")
    scheduler_available = False

def create_app():
    """创建Flask应用实例"""
    app_logger.info("开始创建Flask应用实例")
    
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    app.config['SECRET_KEY'] = 'chaoxing-auto-sign-secret-key-2024'
    app.config['JSON_AS_ASCII'] = False  # 支持中文JSON输出
    
    # 注册蓝图
    app.register_blueprint(sign_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(api_bp)
    
    app_logger.info("Flask应用蓝图注册完成")
    
    # 注册错误处理器
    register_error_handlers(app)
    
    # 首页路由
    @app.route('/')
    def index():
        """首页"""
        return render_template('index.html')
    
    # 额外页面路由
    @app.route('/user_management')
    def user_management():
        # 重定向到用户蓝图的路由
        from flask import redirect, url_for
        return redirect(url_for('user.index'))
    
    @app.route('/system_settings')
    def system_settings():
        return render_template('system_settings.html')
    
    @app.route('/debug_user_api')
    def debug_user_api():
        """调试用户API的页面"""
        return render_template('debug_user_api.html')
    

    
    # 初始化调度器
    if scheduler_available:
        try:
            initialize_scheduler()
            app_logger.info("定时任务调度器初始化成功")
            print("定时任务调度器初始化成功")
        except Exception as e:
            app_logger.error(f"调度器初始化失败: {e}")
            print(f"调度器初始化失败: {e}")
    else:
        app_logger.warning("调度器功能不可用，跳过初始化")
        print("调度器功能不可用，跳过初始化")
    
    app_logger.info("Flask应用创建完成")
    return app

def register_error_handlers(app):
    """注册错误处理器"""
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(HTTPException)
    def handle_exception(e):
        return jsonify({
            'success': False,
            'message': e.description,
            'code': e.code
        }), e.code

def update_all_user_cookies():
    """更新所有用户的Cookie - 供定时任务调用"""
    try:
        # 导入必要的模块
        from utils.file import get_all_users, store_user
        from functions.user import user_login
        
        # 获取所有用户
        users = get_all_users()
        if not users:
            return {
                'status': False,
                'message': '没有找到任何用户'
            }
        
        success_count = 0
        failed_count = 0
        failed_users = []
        
        for user in users:
            phone = user.get('phone')
            if not phone:
                continue
                
            try:
                # 检查用户是否有密码信息
                if 'password' not in user:
                    failed_count += 1
                    failed_users.append(f"{phone}(密码信息缺失)")
                    continue
                
                # 重新登录获取新的Cookie
                result = user_login(phone, user['password'])
                if result.get('success'):
                    # 更新用户的Cookie信息
                    user['cookies'] = result.get('cookies', {})
                    if 'user_info' in result:
                        user['username'] = result['user_info'].get('username', user.get('username', '未知用户'))
                    
                    # 保存更新后的用户信息
                    store_user(phone, user)
                    success_count += 1
                else:
                    failed_count += 1
                    failed_users.append(f"{phone}({result.get('message', '登录失败')})")
                    
            except Exception as e:
                failed_count += 1
                failed_users.append(f"{phone}({str(e)})")
        
        return {
            'status': True,
            'message': f'Cookie更新完成，成功: {success_count}，失败: {failed_count}',
            'success_count': success_count,
            'failed_count': failed_count,
            'total_count': len(users),
            'failed_users': failed_users
        }
        
    except Exception as e:
        return {
            'status': False,
            'message': f'更新所有用户Cookie失败: {str(e)}'
        }

# 创建应用实例
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 