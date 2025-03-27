from flask import Flask, jsonify, request, render_template, redirect, url_for
from flask_cors import CORS
import json
import sys
import os

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入项目的功能模块
from functions.user import user_login, get_account_info, get_local_users
from functions.activity import handle_activity_sign
from utils.file import get_json_object, store_user, delete_user, get_all_users
from sign_api import sign_by_index, sign_by_phone, sign_by_login

app = Flask(__name__)
CORS(app)  # 启用跨域支持

@app.route('/')
def index():
    """渲染主页"""
    return render_template('index.html')

@app.route('/api/users', methods=['GET'])
def get_users():
    """获取所有用户"""
    users = get_all_users()
    return jsonify({"status": True, "users": users})

@app.route('/api/users', methods=['POST'])
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
def remove_user(phone):
    """删除用户"""
    result = delete_user(phone)
    return jsonify({"status": True, "message": "用户删除成功"})

@app.route('/api/users/<phone>', methods=['PUT'])
def update_user(phone):
    """更新用户信息"""
    data = request.json
    
    if not data:
        return jsonify({"status": False, "message": "请提供更新数据"})
    
    # 获取当前用户信息
    user_data = get_json_object('configs/storage.json')
    
    # 查找并更新用户
    found = False
    for i, user in enumerate(user_data.get('users', [])):
        if user.get('phone') == phone:
            # 更新用户信息
            for key, value in data.items():
                # 不更新敏感字段
                if key not in ['params', 'password']:
                    user_data['users'][i][key] = value
            
            # 如果提供了密码，则重新登录获取新cookie
            if 'password' in data and data['password']:
                result = sign_by_login(phone, data['password'])
                if not result['status']:
                    return jsonify({"status": False, "message": f"用户密码更新失败: {result['message']}"})
            
            # 保存更新后的数据
            store_user(phone, user_data['users'][i])
            found = True
            break
    
    if not found:
        return jsonify({"status": False, "message": f"未找到手机号为 {phone} 的用户"})
    
    return jsonify({"status": True, "message": "用户信息更新成功"})

@app.route('/api/sign/all', methods=['POST'])
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 