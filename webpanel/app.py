from flask import Flask, jsonify, request, render_template, redirect, url_for, current_app
from flask_cors import CORS
import json
import sys
import os
import logging
import traceback
import time
from werkzeug.middleware.proxy_fix import ProxyFix
import datetime

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入项目的功能模块
from functions.user import user_login, get_account_info, get_local_users
from functions.activity import handle_activity_sign
from utils.file import get_json_object, store_user, delete_user, get_all_users, get_stored_user
from functions.sign import sign_by_index, sign_by_phone, sign_by_login
# 导入定时任务管理模块
from utils.schedule_task import (
    get_schedule_tasks, get_task, create_task,
    update_task, delete_task, execute_task
)

# 导入监听签到模块
from utils.monitor import (
    get_monitor_tasks, get_monitor_task, create_monitor_task,
    update_monitor_task, delete_monitor_task, toggle_monitor_task
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
        app.logger.error("请求缺少必要参数: 手机号或密码")
        return jsonify({"status": False, "message": "请提供手机号和密码"})
    
    app.logger.info(f"接收到添加用户请求，手机号: {data['phone']}")
    
    # 使用user_login函数登录，而不是sign_by_login
    app.logger.info(f"开始用户登录过程: {data['phone']}")
    result = user_login(data['phone'], data['password'])
    
    # 检查登录结果
    if isinstance(result, str):
        app.logger.error(f"用户登录失败: {data['phone']}, 原因: {result}")
        return jsonify({"status": False, "message": f"登录失败: {result}"})
    
    app.logger.info(f"用户登录成功: {data['phone']}")
    
    # 获取用户名
    app.logger.info(f"开始获取用户信息: {data['phone']}")
    user_params = {**result, 'phone': data['phone'], 'password': data['password']}
    user_name = get_account_info(user_params)
    app.logger.info(f"获取到用户名: {user_name}")
    
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
    app.logger.info(f"开始保存用户信息到本地: {data['phone']}")
    try:
        users = store_user(data['phone'], user_data)
        app.logger.info(f"用户信息保存完成，当前用户数量: {len(users)}")
        
        # 验证用户是否真的被添加了
        storage_data = get_json_object('configs/storage.json')
        found = False
        for user in storage_data.get('users', []):
            if user.get('phone') == data['phone']:
                found = True
                break
        
        if found:
            app.logger.info(f"验证成功：用户 {data['phone']} 已存储到本地")
        else:
            app.logger.warning(f"验证失败：用户 {data['phone']} 未找到于本地存储中")
    
        return jsonify({"status": True, "message": "用户添加成功"})
    except Exception as e:
        app.logger.error(f"保存用户信息时出错: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({"status": False, "message": f"保存用户信息失败: {str(e)}"})

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
    
    app.logger.info(f"更新用户信息请求: 手机号={phone}, 数据={data}")
    
    # 获取当前用户信息
    user_data = get_json_object('configs/storage.json')
    app.logger.info(f"当前存储的用户数量: {len(user_data.get('users', []))}")
    
    # 查找用户
    found = False
    user_index = -1
    for i, user in enumerate(user_data.get('users', [])):
        if user.get('phone') == phone:
            user_index = i
            found = True
            app.logger.info(f"找到用户: 索引={i}, 用户信息={user}")
            break
    
    if not found:
        app.logger.error(f"未找到手机号为 {phone} 的用户")
        return jsonify({"status": False, "message": f"未找到手机号为 {phone} 的用户"})
    
    # 如果提供了新手机号且与原手机号不同
    new_phone = data.get('phone')
    if new_phone and new_phone != phone:
        # 检查新手机号是否已存在
        for user in user_data.get('users', []):
            if user.get('phone') == new_phone:
                app.logger.error(f"手机号 {new_phone} 已存在")
                return jsonify({"status": False, "message": f"手机号 {new_phone} 已存在"})
        
        # 更新手机号
        user_data['users'][user_index]['phone'] = new_phone
        app.logger.info(f"更新用户手机号: {phone} -> {new_phone}")
    
    # 更新其他信息
    for key, value in data.items():
        # 不重复更新手机号，也不更新敏感字段
        if key not in ['phone', 'params']:
            old_value = user_data['users'][user_index].get(key)
            user_data['users'][user_index][key] = value
            app.logger.info(f"更新用户字段: {key}, 旧值={old_value}, 新值={value}")
    
    # 如果提供了密码，则重新登录获取新cookie
    if 'password' in data and data['password']:
        app.logger.info("检测到密码更新，正在重新登录获取新cookie")
        result = user_login(new_phone or phone, data['password'])
        if isinstance(result, str):  # 登录失败
            app.logger.error(f"用户密码更新失败: {result}")
            return jsonify({"status": False, "message": f"用户密码更新失败: {result}"})
        
        # 更新登录参数
        user_data['users'][user_index]['params'] = result
        app.logger.info("成功更新用户登录参数")
    
    # 保存更新后的数据
    target_phone = new_phone if new_phone else phone
    
    # 如果更改了手机号，需要删除旧记录并创建新记录
    if new_phone and new_phone != phone:
        app.logger.info(f"手机号已更改，正在删除旧记录: {phone}")
        delete_user(phone)  # 删除旧记录
    
    # 保存更新后的用户信息
    app.logger.info(f"正在保存更新后的用户信息: {user_data['users'][user_index]}")
    updated_users = store_user(target_phone, user_data['users'][user_index])
    app.logger.info(f"保存成功，更新后的用户数量: {len(updated_users)}")
    
    return jsonify({"status": True, "message": "用户信息更新成功"})

@app.route('/api/users/<phone>/update-cookie', methods=['POST'])
@handle_errors
def update_user_cookie(phone):
    """更新指定用户的cookie"""
    # 获取用户信息
    user_data = get_json_object('configs/storage.json')
    user = None
    for u in user_data.get('users', []):
        if u.get('phone') == phone:
            user = u
            break
    
    if not user:
        return jsonify({"status": False, "message": f"未找到手机号为 {phone} 的用户"})
    
    # 检查是否有密码
    if not user.get('password'):
        return jsonify({"status": False, "message": "用户未设置密码，无法更新cookie"})
    
    # 重新登录获取新cookie
    result = user_login(phone, user['password'])
    if isinstance(result, str):  # 登录失败
        return jsonify({"status": False, "message": f"更新cookie失败: {result}"})
    
    # 更新用户信息
    user['params'] = result
    
    # 保存更新后的数据
    store_user(phone, user)
    
    return jsonify({"status": True, "message": "Cookie更新成功"})

@app.route('/api/users/update-all-cookies', methods=['POST'])
@handle_errors
def update_all_user_cookies():
    """更新所有用户的cookie"""
    # 获取所有用户信息
    user_data = get_json_object('configs/storage.json')
    results = []
    
    for user in user_data.get('users', []):
        phone = user.get('phone')
        if not phone or not user.get('password'):
            results.append({
                "phone": phone,
                "status": False,
                "message": "用户未设置密码，跳过更新"
            })
            continue
        
        # 重新登录获取新cookie
        result = user_login(phone, user['password'])
        if isinstance(result, str):  # 登录失败
            results.append({
                "phone": phone,
                "status": False,
                "message": f"更新cookie失败: {result}"
            })
            continue
        
        # 更新用户信息
        user['params'] = result
        store_user(phone, user)
        results.append({
            "phone": phone,
            "status": True,
            "message": "Cookie更新成功"
        })
    
    # 检查是否有任何更新失败
    failed_updates = [r for r in results if not r['status']]
    if failed_updates:
        return jsonify({
            "status": False,
            "message": "部分用户Cookie更新失败",
            "results": results
        })
    
    return jsonify({
        "status": True,
        "message": "所有用户Cookie更新成功",
        "results": results
    })

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
        # 验证手机号格式
        phone = user.get('phone')
        if not phone or not isinstance(phone, str) or not phone.isdigit() or len(phone) != 11 or not phone.startswith('1'):
            results.append({
                "phone": phone or '未知',
                "name": user.get('username', '未知用户'),
                "status": False,
                "message": f"手机号格式不正确: {phone}"
            })
            continue
            
        # 如果设置排除未激活用户并且用户未激活，则跳过
        if exclude_inactive and not user.get('active', True):
            results.append({
                "phone": phone,
                "name": user.get('username', '未知用户'),
                "status": False,
                "message": "用户未激活，已跳过"
            })
            continue
        
        # 执行签到
        location_preset_item = data.get('location_preset_item')
        location_address_info = data.get('location_address_info')
        location_random_offset = data.get('location_random_offset', True)
        
        # 检查是否需要传递位置信息，只有当用户没有自己的预设位置时才需要
        user_has_location = False
        # 检查用户是否有预设位置（检查两个可能的存储位置）
        if 'presetAddress' in user and user['presetAddress']:
            user_has_location = True
        elif 'monitor' in user and 'presetAddress' in user['monitor'] and user['monitor']['presetAddress']:
            user_has_location = True
        
        # 如果用户没有自己的预设位置，才传入位置参数
        if not user_has_location:
            result = sign_by_phone(
                phone, 
                location_preset_item, 
                location_address_info, 
                location_random_offset
            )
        else:
            # 用户有自己的预设位置，不传入位置参数
            result = sign_by_phone(
                phone,
                None,
                None,
                location_random_offset
            )
        
        # 记录结果
        results.append({
            "phone": phone,
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
    
    # 验证手机号格式
    if not phone or not phone.isdigit() or len(phone) != 11 or not phone.startswith('1'):
        return jsonify({
            "status": False, 
            "message": f"无效的手机号格式: {phone}"
        })
    
    # 获取用户信息，检查是否存在
    user = get_stored_user(phone)
    if not user:
        return jsonify({
            "status": False,
            "message": f"未找到手机号为 {phone} 的用户，请确认storage.json中有此用户"
        })
    
    # 检查用户是否激活
    if not user.get('active', True):
        return jsonify({
            "status": False,
            "message": f"用户 {user.get('username', phone)} 当前未激活，请先激活用户"
        })
    
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
    
    # 检查是否在可签到范围内
    if result.get('result', '').startswith('[位置]不在可签到范围内'):
        result['message'] = '不在可签到范围内，请检查位置设置'
    
    return jsonify(result)

@app.route('/api/location/presets', methods=['GET'])
@handle_errors
def get_location_presets():
    """获取所有用户的位置预设"""
    users = get_all_users()
    presets = {}
    
    for user in users:
        phone = user.get('phone')
        # 检查用户是否有预设位置（老版本在monitor.presetAddress，新版本直接在presetAddress）
        if phone:
            user_presets = []
            if 'monitor' in user and 'presetAddress' in user['monitor']:
                user_presets = user['monitor']['presetAddress']
            elif 'presetAddress' in user:
                user_presets = user['presetAddress']
                
            if user_presets:
                presets[phone] = {
                    'username': user.get('username', '未知用户'),
                    'presets': user_presets
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
            # 确保presetAddress字段存在
            if 'presetAddress' not in users_data['users'][i]:
                users_data['users'][i]['presetAddress'] = []
            
            # 添加新的位置预设
            preset = {
                'lat': data['lat'],
                'lon': data['lon'],
                'address': data['address']
            }
            users_data['users'][i]['presetAddress'].append(preset)
            
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
            # 检查presetAddress字段是否存在
            if 'presetAddress' in user and len(user['presetAddress']) > index:
                # 删除指定索引的位置预设
                user['presetAddress'].pop(index)
                # 保存更新后的数据
                store_user(phone, user)
                found = True
                break
            # 兼容旧版本，检查monitor.presetAddress
            elif 'monitor' in user and 'presetAddress' in user['monitor'] and len(user['monitor']['presetAddress']) > index:
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
    required_fields = ['name', 'type']
    for field in required_fields:
        if field not in data:
            return jsonify({"status": False, "message": f"缺少必填字段: {field}"})
    
    # 根据任务类型检查其他必填字段
    task_type = data.get('type')
    if task_type == 'daily' or task_type == 'weekly':
        if 'time' not in data:
            return jsonify({"status": False, "message": "每日/每周任务必须指定时间"})
        
        if task_type == 'weekly' and ('days' not in data or not data['days']):
            return jsonify({"status": False, "message": "每周任务必须指定星期几"})
        
        # 检查用户选择
        if 'user_type' not in data:
            return jsonify({"status": False, "message": "缺少必填字段: user_type"})
        
        if data.get('user_type') == 'all':
            # 全部用户模式
            data['user_ids'] = ["all"]
        elif 'user_ids' not in data or not data['user_ids']:
            # 兼容旧版本，检查user_id字段
            if 'user_id' not in data or not data['user_id']:
                return jsonify({"status": False, "message": "请至少选择一个用户"})
            else:
                # 将单个user_id转换为user_ids数组
                data['user_ids'] = [data['user_id']]
    
    elif task_type == 'interval':
        if 'interval' not in data:
            return jsonify({"status": False, "message": "间隔任务必须指定间隔值"})
        
        if 'unit' not in data:
            return jsonify({"status": False, "message": "间隔任务必须指定时间单位"})
        
        # 检查用户选择
        if 'user_type' not in data:
            return jsonify({"status": False, "message": "缺少必填字段: user_type"})
        
        if data.get('user_type') == 'all':
            # 全部用户模式
            data['user_ids'] = ["all"]
        elif 'user_ids' not in data or not data['user_ids']:
            # 兼容旧版本，检查user_id字段
            if 'user_id' not in data or not data['user_id']:
                return jsonify({"status": False, "message": "请至少选择一个用户"})
            else:
                # 将单个user_id转换为user_ids数组
                data['user_ids'] = [data['user_id']]
    
    elif task_type == 'cookie_update':
        if 'interval' not in data:
            return jsonify({"status": False, "message": "Cookie更新任务必须指定间隔值"})
        
        # 检查用户选择
        if 'user_type' not in data:
            return jsonify({"status": False, "message": "缺少必填字段: user_type"})
        
        if data['user_type'] == 'selected':
            if 'user_ids' not in data or not data['user_ids']:
                return jsonify({"status": False, "message": "请至少选择一个用户"})
        elif data['user_type'] == 'all':
            data['user_ids'] = []  # 对于全部用户，不需要 user_ids
        else:
            return jsonify({"status": False, "message": "无效的用户选择类型"})
    
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
    
    # 确保task_id是整数
    task_id = int(task_id)
    
    # 检查任务是否存在
    task = get_task(task_id)
    if not task:
        return jsonify({"status": False, "message": f"未找到ID为 {task_id} 的任务"})
    
    # 检查用户选择
    if 'user_type' in data and data['user_type'] == 'all':
        # 全部用户模式
        data['user_ids'] = ["all"]
    elif 'user_ids' in data and not data['user_ids']:
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

@app.route('/api/schedule/<int:task_id>/toggle', methods=['POST'])
@handle_errors
def toggle_schedule(task_id):
    """切换定时任务的激活状态"""
    # 检查任务是否存在
    task = get_task(task_id)
    if not task:
        return jsonify({"status": False, "message": f"未找到ID为 {task_id} 的任务"})
    
    # 切换任务状态
    task['active'] = not task.get('active', True)
    success = update_task(task_id, task)
    
    if success:
        return jsonify({"status": True, "message": "任务状态更新成功", "active": task['active']})
    else:
        return jsonify({"status": False, "message": "任务状态更新失败"})

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

@app.route('/api/logs', methods=['GET'])
@handle_errors
def get_logs():
    """获取系统日志"""
    log_type = request.args.get('type', 'scheduler')
    limit = int(request.args.get('limit', 100))
    
    logs = []
    
    # 确保logs目录存在
    if not os.path.exists('logs'):
        return jsonify({"status": True, "logs": [], "message": "日志目录不存在"})
    
    # 根据请求的日志类型选择相应的日志文件
    log_path = None
    if log_type == 'scheduler':
        log_path = 'logs/scheduler.log'
    elif log_type == 'app':
        log_path = 'logs/app.log'
    elif log_type == 'daemon':
        log_path = 'logs/daemon.log'
    
    # 如果找到对应的日志文件，读取内容
    if log_path and os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            # 读取最后的limit行
            logs = [line.strip() for line in f.readlines()]
            logs = logs[-limit:] if len(logs) > limit else logs
    
    return jsonify({"status": True, "logs": logs})

@app.route('/api/logs/analyze', methods=['GET'])
@handle_errors
def analyze_logs():
    """分析日志数据，提取签到情况统计"""
    # 确保logs目录存在
    if not os.path.exists('logs'):
        return jsonify({
            "status": True, 
            "stats": {
                "total_tasks": 0,
                "successful_tasks": 0,
                "failed_tasks": 0,
                "total_signs": 0,
                "successful_signs": 0,
                "failed_signs": 0,
                "recent_activities": []
            },
            "message": "日志目录不存在"
        })
    
    # 读取调度器日志
    log_path = 'logs/scheduler.log'
    if not os.path.exists(log_path):
        return jsonify({
            "status": True, 
            "stats": {
                "total_tasks": 0,
                "successful_tasks": 0,
                "failed_tasks": 0,
                "total_signs": 0,
                "successful_signs": 0,
                "failed_signs": 0,
                "recent_activities": []
            },
            "message": "日志文件不存在"
        })
    
    # 统计数据
    stats = {
        "total_tasks": 0,        # 总任务数
        "successful_tasks": 0,    # 成功的任务数
        "failed_tasks": 0,        # 失败的任务数
        "total_signs": 0,         # 总签到次数
        "successful_signs": 0,    # 成功的签到次数
        "failed_signs": 0,        # 失败的签到次数
        "recent_activities": []   # 最近活动
    }
    
    # 临时存储任务执行记录
    task_executions = {}
    
    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        
        # 逆序处理以提取最近的事件
        for line in reversed(lines):
            try:
                # 解析日志行
                if "开始执行任务" in line:
                    parts = line.split(" - ")
                    if len(parts) >= 3:
                        timestamp = parts[0]
                        message = parts[2].strip()
                        task_name = message.split("开始执行任务")[1].split("(ID:")[0].strip()
                        task_id = message.split("(ID:")[1].split(")")[0].strip()
                        
                        if len(stats["recent_activities"]) < 10:
                            stats["recent_activities"].append({
                                "timestamp": timestamp,
                                "task_name": task_name,
                                "task_id": task_id,
                                "type": "task_start",
                                "message": message
                            })
                        
                        stats["total_tasks"] += 1
                        task_executions[task_id] = {"success": False, "signs": 0, "successful_signs": 0}
                
                # 提取任务完成信息
                elif "任务执行完成" in line:
                    parts = line.split(" - ")
                    if len(parts) >= 3:
                        timestamp = parts[0]
                        message = parts[2].strip()
                        
                        if "全部成功" in message:
                            stats["successful_tasks"] += 1
                            # 提取用户数量
                            users_count = int(message.split("共")[1].split("个用户")[0].strip())
                            stats["total_signs"] += users_count
                            stats["successful_signs"] += users_count
                            
                            if len(stats["recent_activities"]) < 10:
                                stats["recent_activities"].append({
                                    "timestamp": timestamp,
                                    "type": "task_complete",
                                    "status": "success",
                                    "users_count": users_count,
                                    "message": message
                                })
                        
                        elif "部分成功" in message:
                            stats["successful_tasks"] += 1
                            # 提取成功/总数
                            success_total = message.split("部分成功")[1].strip()[1:-1].split("/")
                            success_count = int(success_total[0])
                            total_count = int(success_total[1])
                            
                            stats["total_signs"] += total_count
                            stats["successful_signs"] += success_count
                            stats["failed_signs"] += (total_count - success_count)
                            
                            if len(stats["recent_activities"]) < 10:
                                stats["recent_activities"].append({
                                    "timestamp": timestamp,
                                    "type": "task_complete",
                                    "status": "partial",
                                    "success_count": success_count,
                                    "total_count": total_count,
                                    "message": message
                                })
                        
                        elif "全部失败" in message:
                            stats["failed_tasks"] += 1
                            # 提取用户数量
                            users_count = int(message.split("共")[1].split("个用户")[0].strip())
                            stats["total_signs"] += users_count
                            stats["failed_signs"] += users_count
                            
                            if len(stats["recent_activities"]) < 10:
                                stats["recent_activities"].append({
                                    "timestamp": timestamp,
                                    "type": "task_complete",
                                    "status": "failed",
                                    "users_count": users_count,
                                    "message": message
                                })
                
                # 提取单个用户签到信息
                elif "为用户" in line and "执行" in line:
                    parts = line.split(" - ")
                    if len(parts) >= 3:
                        timestamp = parts[0]
                        message = parts[2].strip()
                        
                        # 任务成功
                        if "执行成功" in message:
                            if len(stats["recent_activities"]) < 10:
                                user_id = message.split("为用户")[1].split("执行成功")[0].strip()
                                task_name = message.split("任务")[1].split("为用户")[0].strip()
                                
                                stats["recent_activities"].append({
                                    "timestamp": timestamp,
                                    "type": "user_sign",
                                    "status": "success",
                                    "user_id": user_id,
                                    "task_name": task_name,
                                    "message": message
                                })
            
            except Exception as e:
                # 解析日志行出错，跳过
                continue
    
    # 按时间排序最近活动
    stats["recent_activities"] = sorted(stats["recent_activities"], 
                                       key=lambda x: x["timestamp"], 
                                       reverse=True)
    
    return jsonify({"status": True, "stats": stats})

@app.route('/api/stats/sign', methods=['GET'])
@handle_errors
def get_sign_stats():
    """获取签到统计数据"""
    # 分析签到情况
    all_users = get_all_users()
    
    stats = {
        "total_users": len(all_users),
        "active_users": sum(1 for user in all_users if user.get('active', True)),
        "inactive_users": sum(1 for user in all_users if not user.get('active', True)),
        "users_with_location": 0,
        "users_without_location": 0,
        "success_rate": 0.0
    }
    
    # 统计有位置和无位置的用户
    for user in all_users:
        has_location = False
        if 'presetAddress' in user and user['presetAddress']:
            has_location = True
        elif 'monitor' in user and 'presetAddress' in user['monitor'] and user['monitor']['presetAddress']:
            has_location = True
            
        if has_location:
            stats["users_with_location"] += 1
        else:
            stats["users_without_location"] += 1
    
    # 获取任务统计
    tasks = get_schedule_tasks()
    stats["total_tasks"] = len(tasks)
    stats["active_tasks"] = sum(1 for task in tasks if task.get('active', True))
    stats["inactive_tasks"] = sum(1 for task in tasks if not task.get('active', True))
    
    # 分析任务执行情况 - 不仅包括最后一次，还包括历史记录
    recent_signs = {
        "total": 0,
        "success": 0,
        "failed": 0
    }
    
    # 定义历史记录保存路径
    history_path = 'configs/sign_history.json'
    sign_history = []
    
    # 尝试读取历史记录
    try:
        if os.path.exists(history_path):
            with open(history_path, 'r', encoding='utf-8') as f:
                sign_history = json.load(f)
        
        # 如果没有历史记录或格式不正确，初始化为空列表
        if not isinstance(sign_history, list):
            sign_history = []
    except Exception as e:
        app.logger.error(f"读取签到历史记录失败: {str(e)}")
        sign_history = []
    
    # 获取当前任务的最新执行结果
    for task in tasks:
        if 'last_run' in task and task['last_run']:
            last_run = task['last_run']
            if 'details' in last_run:
                # 创建历史记录条目
                history_entry = {
                    'time': last_run.get('time', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                    'task_id': task.get('id'),
                    'task_name': task.get('name', f"任务{task.get('id')}"),
                    'details': last_run['details']
                }
                
                # 检查是否已存在相同时间的记录，避免重复
                is_duplicate = False
                for entry in sign_history:
                    if (entry.get('time') == history_entry.get('time') and
                        entry.get('task_id') == history_entry.get('task_id')):
                        is_duplicate = True
                        break
                
                # 如果不是重复记录，添加到历史
                if not is_duplicate:
                    sign_history.append(history_entry)
    
    # 保存更新后的历史记录
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(history_path), exist_ok=True)
        # 最多保留100条记录
        if len(sign_history) > 100:
            sign_history = sorted(sign_history, key=lambda x: x.get('time', ''), reverse=True)[:100]
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(sign_history, f, ensure_ascii=False, indent=4)
    except Exception as e:
        app.logger.error(f"保存签到历史记录失败: {str(e)}")
    
    # 统计历史记录中的签到情况 (最近7天)
    try:
        # 获取7天前的时间
        current_time = datetime.datetime.now()
        seven_days_ago = (current_time - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
        
        # 按时间排序
        sign_history = sorted(sign_history, key=lambda x: x.get('time', ''), reverse=True)
        
        # 统计最近7天的签到情况
        for entry in sign_history:
            entry_time = entry.get('time', '')
            # 如果没有时间信息或格式不正确，跳过
            if not entry_time:
                continue
                
            # 提取日期部分
            entry_date = entry_time.split(' ')[0] if ' ' in entry_time else entry_time
            
            # 只统计7天内的记录
            if entry_date >= seven_days_ago:
                for detail in entry.get('details', []):
                    recent_signs["total"] += 1
                    if detail.get('status', False):
                        recent_signs["success"] += 1
                    else:
                        recent_signs["failed"] += 1
    except Exception as e:
        app.logger.error(f"统计签到历史记录失败: {str(e)}")
        # 如果历史记录处理失败，回退到只统计最后一次执行的方法
        recent_signs = {"total": 0, "success": 0, "failed": 0}
        for task in tasks:
            if 'last_run' in task and task['last_run']:
                last_run = task['last_run']
                if 'details' in last_run:
                    for detail in last_run['details']:
                        recent_signs["total"] += 1
                        if detail.get('status', False):
                            recent_signs["success"] += 1
                        else:
                            recent_signs["failed"] += 1
    
    stats["recent_signs"] = recent_signs
    
    # 计算成功率
    if recent_signs["total"] > 0:
        stats["success_rate"] = recent_signs["success"] / recent_signs["total"] * 100
    
    return jsonify({"status": True, "stats": stats})

# 监听签到相关API路由
@app.route('/api/monitor/list', methods=['GET'])
@handle_errors
def get_monitors():
    """获取所有监听任务"""
    tasks = get_monitor_tasks()
    return jsonify({"code": 0, "message": "获取成功", "data": tasks})

@app.route('/api/monitor/add', methods=['POST'])
@handle_errors
def add_monitor():
    """添加监听任务"""
    data = request.json
    
    # 验证必要字段
    required_fields = ['phone', 'interval']
    for field in required_fields:
        if field not in data:
            return jsonify({"code": 1, "message": f"缺少必要字段: {field}"})
    
    # 验证用户存在
    user_data = get_json_object('configs/storage.json')
    user_exists = False
    for user in user_data.get('users', []):
        if user.get('phone') == data['phone']:
            user_exists = True
            break
    
    if not user_exists:
        return jsonify({"code": 1, "message": "用户不存在"})
    
    # 处理课程ID，如果未提供或为空，设为空数组表示监听所有课程
    course_ids = data.get('course_ids', [])
    if not isinstance(course_ids, list):
        return jsonify({"code": 1, "message": "课程ID格式不正确"})
    
    # 验证间隔时间
    if not isinstance(data['interval'], int) or data['interval'] < 10:
        return jsonify({"code": 1, "message": "轮询间隔必须是大于等于10的整数"})
    
    # 处理延迟范围
    delay_range = data.get('delay_range')
    if delay_range is not None:
        if not isinstance(delay_range, list) or len(delay_range) != 2:
            return jsonify({"code": 1, "message": "延迟范围必须是两个整数的数组"})
        if not all(isinstance(x, int) and x >= 0 for x in delay_range):
            return jsonify({"code": 1, "message": "延迟范围必须是非负整数"})
        if delay_range[0] > delay_range[1]:
            return jsonify({"code": 1, "message": "延迟范围的最小值不能大于最大值"})
    
    # 创建监听任务
    task_id = create_monitor_task(
        phone=data['phone'],
        course_ids=course_ids,
        interval=data['interval'],
        delay_range=delay_range
    )
    
    return jsonify({"code": 0, "message": "监听任务创建成功", "task_id": task_id})

@app.route('/api/monitor/update', methods=['POST'])
@handle_errors
def update_monitor():
    """更新监听任务"""
    data = request.json
    
    # 验证必要字段
    required_fields = ['id', 'phone', 'interval']
    for field in required_fields:
        if field not in data:
            return jsonify({"code": 1, "message": f"缺少必要字段: {field}"})
    
    # 验证任务存在
    task = get_monitor_task(data['id'])
    if not task:
        return jsonify({"code": 1, "message": "监听任务不存在"})
    
    # 验证用户存在
    user_data = get_json_object('configs/storage.json')
    user_exists = False
    for user in user_data.get('users', []):
        if user.get('phone') == data['phone']:
            user_exists = True
            break
    
    if not user_exists:
        return jsonify({"code": 1, "message": "用户不存在"})
    
    # 处理课程ID，如果未提供或为空，设为空数组表示监听所有课程
    course_ids = data.get('course_ids', [])
    if not isinstance(course_ids, list):
        return jsonify({"code": 1, "message": "课程ID格式不正确"})
    
    # 验证间隔时间
    if not isinstance(data['interval'], int) or data['interval'] < 10:
        return jsonify({"code": 1, "message": "轮询间隔必须是大于等于10的整数"})
    
    # 处理延迟范围
    delay_range = data.get('delay_range')
    if delay_range is not None:
        if not isinstance(delay_range, list) or len(delay_range) != 2:
            return jsonify({"code": 1, "message": "延迟范围必须是两个整数的数组"})
        if not all(isinstance(x, int) and x >= 0 for x in delay_range):
            return jsonify({"code": 1, "message": "延迟范围必须是非负整数"})
        if delay_range[0] > delay_range[1]:
            return jsonify({"code": 1, "message": "延迟范围的最小值不能大于最大值"})
    
    # 更新监听任务
    success = update_monitor_task(
        task_id=data['id'],
        phone=data['phone'],
        course_ids=course_ids,
        interval=data['interval'],
        active=data.get('active', True),
        delay_range=delay_range
    )
    
    if success:
        return jsonify({"code": 0, "message": "监听任务更新成功"})
    else:
        return jsonify({"code": 1, "message": "监听任务更新失败"})

@app.route('/api/monitor/delete', methods=['POST'])
@handle_errors
def delete_monitor():
    """删除监听任务"""
    data = request.json
    
    # 验证必要字段
    if 'id' not in data:
        return jsonify({"code": 1, "message": "缺少必要字段: id"})
    
    # 验证任务存在
    task = get_monitor_task(data['id'])
    if not task:
        return jsonify({"code": 1, "message": "监听任务不存在"})
    
    # 删除监听任务
    success = delete_monitor_task(data['id'])
    
    if success:
        return jsonify({"code": 0, "message": "监听任务删除成功"})
    else:
        return jsonify({"code": 1, "message": "监听任务删除失败"})

@app.route('/api/monitor/toggle', methods=['POST'])
@handle_errors
def toggle_monitor():
    """切换监听任务状态"""
    data = request.json
    
    # 验证必要字段
    required_fields = ['id', 'active']
    for field in required_fields:
        if field not in data:
            return jsonify({"code": 1, "message": f"缺少必要字段: {field}"})
    
    # 验证任务存在
    task = get_monitor_task(data['id'])
    if not task:
        return jsonify({"code": 1, "message": "监听任务不存在"})
    
    # 切换监听任务状态
    success = toggle_monitor_task(data['id'], data['active'])
    
    if success:
        return jsonify({"code": 0, "message": f"监听任务已{'激活' if data['active'] else '停用'}"})
    else:
        return jsonify({"code": 1, "message": "切换监听任务状态失败"})

@app.route('/api/monitor/reset-id', methods=['POST'])
@handle_errors
def reset_monitor_id():
    """重置监听任务ID计数器"""
    try:
        # 获取监听任务数据
        monitor_data = get_json_object(MONITOR_TASKS_FILE)
        
        # 如果没有任务，直接重置ID为1
        if len(monitor_data.get('tasks', [])) == 0:
            monitor_data['next_id'] = 1
            save_json_object(MONITOR_TASKS_FILE, monitor_data)
            return jsonify({"code": 0, "message": "监听任务ID已重置为1"})
        else:
            # 如果还有任务，不允许重置ID
            return jsonify({"code": 1, "message": "还有未删除的监听任务，请先删除所有任务再重置ID"})
    except Exception as e:
        return jsonify({"code": 1, "message": f"重置ID失败: {str(e)}"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 