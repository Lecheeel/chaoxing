from flask import Flask, jsonify, request, render_template, redirect, url_for, current_app
from flask_cors import CORS
import json
import sys
import os
import logging
import traceback
import time
from werkzeug.middleware.proxy_fix import ProxyFix

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入项目的功能模块
from functions.user import user_login, get_account_info, get_local_users
from functions.activity import handle_activity_sign
from utils.file import get_json_object, store_user, delete_user, get_all_users
from sign_api import sign_by_index, sign_by_phone, sign_by_login
# 导入定时任务管理模块
from schedule_task import (
    get_schedule_tasks, get_task, create_task,
    update_task, delete_task, execute_task
)
# 导入监控功能管理模块
from webpanel.monitor_service import (
    get_monitor_status, get_user_monitor_status, 
    start_monitor, stop_monitor, stop_all_monitors
)

app = Flask(__name__)
CORS(app)  # 启用跨域支持

# 使用ProxyFix中间件处理代理
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# 配置应用
app.config['JSON_AS_ASCII'] = False  # 确保JSON响应中的中文正确显示
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制请求大小为16MB
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False  # 禁用美化JSON

# 请求前钩子，记录每个请求
@app.before_request
def log_request_info():
    if app.debug:
        # 仅在调试模式下记录详细请求信息
        app.logger.debug('Headers: %s', request.headers)
        app.logger.debug('Body: %s', request.get_data())
    
    # 记录所有请求的基本信息
    app.logger.info(
        '%s %s %s %s',
        request.remote_addr,
        request.method,
        request.scheme,
        request.full_path
    )

# 请求后钩子，记录响应时间
@app.after_request
def after_request(response):
    response.headers.add('X-Content-Type-Options', 'nosniff')
    response.headers.add('X-Frame-Options', 'DENY')
    response.headers.add('X-XSS-Protection', '1; mode=block')
    return response

# 错误处理器
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({"status": False, "message": "API路径不存在"}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"status": False, "message": "请求方法不被允许"}), 405

@app.errorhandler(500)
def internal_server_error(e):
    app.logger.error("服务器内部错误: %s", str(e))
    app.logger.error(traceback.format_exc())
    return jsonify({"status": False, "message": "服务器内部错误"}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error("未处理的异常: %s", str(e))
    app.logger.error(traceback.format_exc())
    return jsonify({"status": False, "message": f"服务器错误: {str(e)}"}), 500

# 全局异常处理装饰器
def handle_errors(f):
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            app.logger.error(f"API错误 {f.__name__}: {str(e)}")
            app.logger.error(traceback.format_exc())
            return jsonify({"status": False, "message": f"处理请求时出错: {str(e)}"}), 500
    decorated_function.__name__ = f.__name__
    return decorated_function

# 添加错误处理装饰器到所有路由
@app.route('/')
@handle_errors
def index():
    """渲染主页"""
    return render_template('index.html')

@app.route('/api/users', methods=['GET'])
@handle_errors
def get_users():
    """获取所有用户"""
    users = get_all_users()
    return jsonify({"status": True, "users": users})

@app.route('/api/users', methods=['POST'])
@handle_errors
def add_user():
    """添加新用户"""
    data = request.json
    
    if not data or 'phone' not in data or 'password' not in data:
        return jsonify({"status": False, "message": "请提供手机号和密码"})
    
    # 使用user_login函数登录，而不是sign_by_login
    result = user_login(data['phone'], data['password'])
    
    # 检查登录结果
    if isinstance(result, str):
        return jsonify({"status": False, "message": f"登录失败: {result}"})
    
    # 获取用户名
    user_params = {**result, 'phone': data['phone'], 'password': data['password']}
    user_name = get_account_info(user_params)
    
    # 创建用户对象
    user_data = {
        'phone': data['phone'], 
        'password': data['password'],
        'params': result
    }
    
    # 保存用户名
    if user_name and user_name != "未知用户":
        user_data['username'] = user_name
    
    # 保存用户信息
    store_user(data['phone'], user_data)
    
    return jsonify({"status": True, "message": "用户添加成功"})

@app.route('/api/users/<phone>', methods=['DELETE'])
@handle_errors
def remove_user(phone):
    """删除用户"""
    result = delete_user(phone)
    return jsonify({"status": True, "message": "用户删除成功"})

@app.route('/api/users/<phone>', methods=['PUT'])
@handle_errors
def update_user(phone):
    """更新用户信息"""
    data = request.json
    
    if not data:
        return jsonify({"status": False, "message": "请提供更新数据"})
    
    # 获取当前用户信息
    user_data = get_json_object('configs/storage.json')
    
    # 查找用户
    found = False
    user_index = -1
    for i, user in enumerate(user_data.get('users', [])):
        if user.get('phone') == phone:
            user_index = i
            found = True
            break
    
    if not found:
        return jsonify({"status": False, "message": f"未找到手机号为 {phone} 的用户"})
    
    # 如果提供了新手机号且与原手机号不同
    new_phone = data.get('phone')
    if new_phone and new_phone != phone:
        # 检查新手机号是否已存在
        for user in user_data.get('users', []):
            if user.get('phone') == new_phone:
                return jsonify({"status": False, "message": f"手机号 {new_phone} 已存在"})
        
        # 更新手机号
        user_data['users'][user_index]['phone'] = new_phone
    
    # 更新其他信息
    for key, value in data.items():
        # 不重复更新手机号，也不更新敏感字段
        if key not in ['phone', 'params']:
            user_data['users'][user_index][key] = value
    
    # 如果提供了密码，则重新登录获取新cookie
    if 'password' in data and data['password']:
        result = user_login(new_phone or phone, data['password'])
        if isinstance(result, str):  # 登录失败
            return jsonify({"status": False, "message": f"用户密码更新失败: {result}"})
        
        # 更新登录参数
        user_data['users'][user_index]['params'] = result
    
    # 保存更新后的数据
    target_phone = new_phone if new_phone else phone
    
    # 如果更改了手机号，需要删除旧记录并创建新记录
    if new_phone and new_phone != phone:
        delete_user(phone)  # 删除旧记录
    
    # 保存更新后的用户信息
    store_user(target_phone, user_data['users'][user_index])
    
    return jsonify({"status": True, "message": "用户信息更新成功"})

@app.route('/api/sign/all', methods=['POST'])
@handle_errors
def sign_all():
    """批量签到所有用户"""
    data = request.json or {}
    exclude_inactive = data.get('exclude_inactive', True)
    
    # 获取所有用户
    users = get_all_users()
    results = []
    
    for user in users:
        # 如果设置排除未激活用户并且用户未激活，则跳过
        if exclude_inactive and not user.get('active', True):
            results.append({
                "phone": user.get('phone'),
                "name": user.get('username', '未知用户'),
                "status": False,
                "message": "用户未激活，已跳过"
            })
            continue
        
        # 执行签到
        location_preset_item = data.get('location_preset_item')
        location_address_info = data.get('location_address_info')
        location_random_offset = data.get('location_random_offset', True)
        
        result = sign_by_phone(
            user.get('phone'), 
            location_preset_item, 
            location_address_info, 
            location_random_offset
        )
        
        # 记录结果
        results.append({
            "phone": user.get('phone'),
            "name": user.get('username', '未知用户'),
            "status": result['status'],
            "message": result['message']
        })
    
    return jsonify({"status": True, "results": results})

@app.route('/api/sign/<phone>', methods=['POST'])
@handle_errors
def sign_user(phone):
    """为指定用户签到"""
    data = request.json or {}
    
    # 执行签到
    location_preset_item = data.get('location_preset_item')
    location_address_info = data.get('location_address_info')
    location_random_offset = data.get('location_random_offset', True)
    
    result = sign_by_phone(
        phone, 
        location_preset_item, 
        location_address_info, 
        location_random_offset
    )
    
    return jsonify(result)

@app.route('/api/location/presets', methods=['GET'])
@handle_errors
def get_location_presets():
    """获取所有用户的位置预设"""
    users = get_all_users()
    presets = {}
    
    for user in users:
        phone = user.get('phone')
        if phone and 'monitor' in user and 'presetAddress' in user['monitor']:
            presets[phone] = {
                'username': user.get('username', '未知用户'),
                'presets': user['monitor']['presetAddress']
            }
    
    return jsonify({"status": True, "presets": presets})

@app.route('/api/location/presets/<phone>', methods=['POST'])
@handle_errors
def add_location_preset(phone):
    """为指定用户添加位置预设"""
    data = request.json
    
    if not data or 'lat' not in data or 'lon' not in data or 'address' not in data:
        return jsonify({"status": False, "message": "请提供完整的位置信息（经纬度和地址）"})
    
    # 获取用户信息
    users_data = get_json_object('configs/storage.json')
    
    # 查找并更新用户
    found = False
    for i, user in enumerate(users_data.get('users', [])):
        if user.get('phone') == phone:
            # 确保monitor和presetAddress字段存在
            if 'monitor' not in user:
                users_data['users'][i]['monitor'] = {}
            if 'presetAddress' not in users_data['users'][i]['monitor']:
                users_data['users'][i]['monitor']['presetAddress'] = []
            
            # 添加新的位置预设
            preset = {
                'lat': data['lat'],
                'lon': data['lon'],
                'address': data['address']
            }
            users_data['users'][i]['monitor']['presetAddress'].append(preset)
            
            # 保存更新后的数据
            store_user(phone, users_data['users'][i])
            found = True
            break
    
    if not found:
        return jsonify({"status": False, "message": f"未找到手机号为 {phone} 的用户"})
    
    return jsonify({"status": True, "message": "位置预设添加成功"})

@app.route('/api/location/presets/<phone>/<int:index>', methods=['DELETE'])
@handle_errors
def delete_location_preset(phone, index):
    """删除指定用户的位置预设"""
    # 获取用户信息
    users_data = get_json_object('configs/storage.json')
    
    # 查找并更新用户
    found = False
    for i, user in enumerate(users_data.get('users', [])):
        if user.get('phone') == phone:
            # 检查monitor和presetAddress字段是否存在
            if ('monitor' in user and 
                'presetAddress' in user['monitor'] and 
                len(user['monitor']['presetAddress']) > index):
                
                # 删除指定索引的位置预设
                user['monitor']['presetAddress'].pop(index)
                
                # 保存更新后的数据
                store_user(phone, user)
                found = True
            break
    
    if not found:
        return jsonify({"status": False, "message": f"未找到手机号为 {phone} 的位置预设或索引无效"})
    
    return jsonify({"status": True, "message": "位置预设删除成功"})

# 定时任务管理API

@app.route('/api/schedule', methods=['GET'])
@handle_errors
def get_schedules():
    """获取所有定时任务"""
    tasks = get_schedule_tasks()
    return jsonify({"status": True, "tasks": tasks})

@app.route('/api/schedule/<int:task_id>', methods=['GET'])
@handle_errors
def get_schedule(task_id):
    """获取指定任务详情"""
    task = get_task(task_id)
    if not task:
        return jsonify({"status": False, "message": f"未找到ID为 {task_id} 的任务"})
    
    return jsonify({"status": True, "task": task})

@app.route('/api/schedule', methods=['POST'])
@handle_errors
def add_schedule():
    """添加新定时任务"""
    data = request.json
    
    if not data:
        return jsonify({"status": False, "message": "请提供任务数据"})
    
    # 检查必填字段
    required_fields = ['name', 'type', 'user_type']
    for field in required_fields:
        if field not in data:
            return jsonify({"status": False, "message": f"缺少必填字段: {field}"})
    
    # 检查用户选择
    if 'user_ids' not in data or not data['user_ids']:
        # 兼容旧版本，检查user_id字段
        if 'user_id' not in data or not data['user_id']:
            return jsonify({"status": False, "message": "请至少选择一个用户"})
        else:
            # 将单个user_id转换为user_ids数组
            data['user_ids'] = [data['user_id']]
    
    # 根据任务类型检查其他必填字段
    task_type = data.get('type')
    if task_type == 'daily' or task_type == 'weekly':
        if 'time' not in data:
            return jsonify({"status": False, "message": "每日/每周任务必须指定时间"})
        
        if task_type == 'weekly' and ('days' not in data or not data['days']):
            return jsonify({"status": False, "message": "每周任务必须指定星期几"})
    
    elif task_type == 'interval':
        if 'interval' not in data:
            return jsonify({"status": False, "message": "间隔任务必须指定间隔值"})
        
        if 'unit' not in data:
            return jsonify({"status": False, "message": "间隔任务必须指定时间单位"})
    
    else:
        return jsonify({"status": False, "message": f"不支持的任务类型: {task_type}"})
    
    # 创建任务
    success = create_task(data)
    
    if success:
        return jsonify({"status": True, "message": "任务创建成功"})
    else:
        return jsonify({"status": False, "message": "任务创建失败"})

@app.route('/api/schedule/<int:task_id>', methods=['PUT'])
@handle_errors
def update_schedule(task_id):
    """更新定时任务"""
    data = request.json
    
    if not data:
        return jsonify({"status": False, "message": "请提供更新数据"})
    
    # 检查任务是否存在
    task = get_task(task_id)
    if not task:
        return jsonify({"status": False, "message": f"未找到ID为 {task_id} 的任务"})
    
    # 检查用户选择
    if 'user_ids' in data and not data['user_ids']:
        return jsonify({"status": False, "message": "请至少选择一个用户"})
    
    # 更新任务
    success = update_task(task_id, data)
    
    if success:
        return jsonify({"status": True, "message": "任务更新成功"})
    else:
        return jsonify({"status": False, "message": "任务更新失败"})

@app.route('/api/schedule/<int:task_id>', methods=['DELETE'])
@handle_errors
def delete_schedule(task_id):
    """删除定时任务"""
    # 检查任务是否存在
    task = get_task(task_id)
    if not task:
        return jsonify({"status": False, "message": f"未找到ID为 {task_id} 的任务"})
    
    # 删除任务
    success = delete_task(task_id)
    
    if success:
        return jsonify({"status": True, "message": "任务删除成功"})
    else:
        return jsonify({"status": False, "message": "任务删除失败"})

@app.route('/api/schedule/<int:task_id>/execute', methods=['POST'])
@handle_errors
def execute_schedule(task_id):
    """立即执行指定的定时任务"""
    # 检查任务是否存在
    task = get_task(task_id)
    if not task:
        return jsonify({"status": False, "message": f"未找到ID为 {task_id} 的任务"})
    
    # 执行任务
    result = execute_task(task_id)
    
    if result and result.get('status', False):
        return jsonify({"status": True, "message": "任务执行成功", "result": result})
    else:
        return jsonify({"status": False, "message": f"任务执行失败: {result.get('message', '未知错误')}", "result": result})

# 健康检查端点
@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({"status": True, "time": time.time()})

# 监控管理 API
@app.route('/api/monitors', methods=['GET'])
@handle_errors
def get_all_monitors():
    """获取所有用户的监控状态"""
    monitors = get_monitor_status()
    return jsonify({"status": True, "monitors": monitors})

@app.route('/api/monitors/<phone>', methods=['GET'])
@handle_errors
def get_monitor(phone):
    """获取指定用户的监控状态"""
    monitor = get_user_monitor_status(phone)
    if not monitor:
        return jsonify({"status": False, "message": f"未找到用户 {phone} 的监控状态"})
    return jsonify({"status": True, "monitor": monitor})

@app.route('/api/monitors/<phone>/start', methods=['POST'])
@handle_errors
def start_user_monitor(phone):
    """启动指定用户的监控"""
    data = request.json or {}
    delay = int(data.get('delay', 0))
    location_preset_index = data.get('location_preset_index')
    
    result = start_monitor(phone, delay, location_preset_index)
    return jsonify(result)

@app.route('/api/monitors/<phone>/stop', methods=['POST'])
@handle_errors
def stop_user_monitor(phone):
    """停止指定用户的监控"""
    result = stop_monitor(phone)
    return jsonify({"status": result, "message": "监控已停止" if result else "停止监控失败"})

@app.route('/api/monitors/stop-all', methods=['POST'])
@handle_errors
def stop_all_user_monitors():
    """停止所有用户的监控"""
    results = stop_all_monitors()
    return jsonify({"status": True, "results": results})

# 应用启动时的初始化
def init_app():
    """应用初始化函数"""
    # 确保配置目录存在
    if not os.path.exists('configs'):
        os.makedirs('configs')
    
    # 确保存储文件存在
    storage_path = 'configs/storage.json'
    if not os.path.exists(storage_path):
        with open(storage_path, 'w', encoding='utf-8') as f:
            json.dump({"users": []}, f, ensure_ascii=False, indent=2)
    
    # 确保任务文件存在
    tasks_path = 'configs/tasks.json'
    if not os.path.exists(tasks_path):
        with open(tasks_path, 'w', encoding='utf-8') as f:
            json.dump({"tasks": []}, f, ensure_ascii=False, indent=2)

    app.logger.info("Flask应用初始化完成")

# 调用初始化函数
init_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 