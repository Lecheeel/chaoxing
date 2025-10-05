# -*- coding: utf-8 -*-
"""
签到模块蓝图
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
import os
import sys
import json
import re
from datetime import datetime, timedelta

# 安全导入功能模块
try:
    from functions.sign import sign_by_phone, sign_by_index, execute_sign
    sign_functions_available = True
except ImportError as e:
    print(f"签到功能模块导入失败: {e}")
    sign_functions_available = False

try:
    from functions.location import location_sign, location_sign_2
    location_functions_available = True
except ImportError as e:
    print(f"位置功能模块导入失败: {e}")
    location_functions_available = False

try:
    from utils.file import get_all_users, get_stored_user, get_json_object
    file_functions_available = True
except ImportError as e:
    print(f"文件功能模块导入失败: {e}")
    file_functions_available = False

def safe_get_users():
    """安全获取用户列表"""
    if file_functions_available:
        try:
            return get_all_users()
        except Exception as e:
            print(f"获取用户列表失败: {e}")
            return []
    return []

def sign_in_all(location_id=None):
    """批量签到的适配器函数"""
    try:
        users = safe_get_users()
        results = []
        for i, user in enumerate(users):
            result = sign_by_index(i, location_id)
            results.append({
                'user': user.get('phone', f'用户{i}'),
                'status': result.get('status', False),
                'message': result.get('message', '未知错误')
            })
        return results
    except Exception as e:
        return [{'user': '系统', 'status': False, 'message': str(e)}]

def sign_in_by_user(user_id, location_id=None):
    """单用户签到的适配器函数"""
    try:
        # 如果user_id是手机号，直接使用
        if isinstance(user_id, str) and len(user_id) == 11:
            return sign_by_phone(user_id, location_id)
        # 如果是索引，使用索引签到
        elif isinstance(user_id, int):
            return sign_by_index(user_id, location_id)
        # 如果是用户对象，提取手机号
        else:
            users = safe_get_users()
            if user_id < len(users):
                return sign_by_index(user_id, location_id)
            else:
                return {'status': False, 'message': '用户不存在'}
    except Exception as e:
        return {'status': False, 'message': str(e)}

def get_sign_activities(user_id):
    """获取签到活动的适配器函数"""
    try:
        # 这里需要根据实际的activity模块实现
        return []
    except:
        return []

def get_locations():
    """获取位置列表的适配器函数"""
    try:
        # 从配置文件中读取位置信息
        config = get_json_object('configs/storage.json')
        locations = []
        
        # 优先从locations字段读取（位置管理添加的位置）
        if 'locations' in config and config['locations']:
            for location in config['locations']:
                locations.append({
                    'id': location.get('id', 0),
                    'name': location.get('name', ''),
                    'address': location.get('address', ''),
                    'lat': location.get('lat', ''),
                    'lon': location.get('lon', ''),
                    'description': location.get('description', ''),
                    'created_at': location.get('created_at', '')
                })
        # 如果没有locations字段，则从presetAddress字段读取（兼容旧版本）
        elif 'presetAddress' in config:
            for i, addr in enumerate(config['presetAddress']):
                locations.append({
                    'id': i,
                    'name': addr.get('address', f'位置{i+1}'),
                    'address': addr.get('address', ''),
                    'lat': addr.get('lat', ''),
                    'lon': addr.get('lon', '')
                })
        
        return locations
    except:
        return []

def get_today_sign_stats():
    """获取今日签到统计"""
    try:
        from utils.stats import get_today_stats
        return get_today_stats()
    except Exception as e:
        print(f"获取签到统计失败: {e}")
        return {
            'success': 0,
            'failed': 0,
            'last_sign_time': '暂无记录'
        }

sign_bp = Blueprint('sign', __name__, url_prefix='/sign')

@sign_bp.route('/')
def index():
    """签到管理首页"""
    try:
        users = safe_get_users()
        locations = get_locations()
        return render_template('sign/index.html', users=users, locations=locations)
    except Exception as e:
        flash(f'获取数据失败: {str(e)}', 'error')
        return render_template('sign/index.html', users=[], locations=[])

@sign_bp.route('/manual')
def manual():
    """手动签到页面"""
    try:
        users = safe_get_users()
        locations = get_locations()
        return render_template('sign/manual.html', users=users, locations=locations)
    except Exception as e:
        flash(f'获取数据失败: {str(e)}', 'error')
        return render_template('sign/manual.html', users=[], locations=[])

@sign_bp.route('/activities')
def activities():
    """签到活动页面"""
    try:
        users = safe_get_users()
        return render_template('sign/activities.html', users=users)
    except Exception as e:
        flash(f'获取数据失败: {str(e)}', 'error')
        return render_template('sign/activities.html', users=[])

@sign_bp.route('/history')
def history():
    """签到历史页面"""
    return render_template('sign/history.html')

@sign_bp.route('/api/sign_status')
def get_sign_status():
    """获取签到状态"""
    try:
        users = safe_get_users()
        active_users = [user for user in users if user.get('active', True)]
        
        # 获取今日签到统计
        today_stats = get_today_sign_stats()
        
        status = {
            'total_users': len(users),
            'active_users': len(active_users),
            'inactive_users': len(users) - len(active_users),
            'today_success': today_stats.get('success', 0),
            'today_failed': today_stats.get('failed', 0),
            'last_sign_time': today_stats.get('last_sign_time', '暂无记录')
        }
        
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取签到状态失败: {str(e)}'
        })

@sign_bp.route('/api/sign_all', methods=['POST'])
def sign_all():
    """全部签到"""
    try:
        if not sign_functions_available:
            return jsonify({
                'success': False,
                'message': '签到功能模块不可用'
            })
        
        # 获取请求数据
        data = request.get_json() or {}
        location_id = data.get('location_id')
        
        # 获取位置信息
        location_info = None
        if location_id is not None:
            locations = get_locations()
            # 确保 location_id 是整数类型
            try:
                location_id = int(location_id)
                if 0 <= location_id < len(locations):
                    location_info = locations[location_id]
            except (ValueError, TypeError):
                # 如果转换失败，忽略位置信息
                location_id = None
            
        users = safe_get_users()
        active_users = [user for user in users if user.get('active', True)]
        
        results = []
        for user in active_users:
            try:
                # 找到用户在原始users列表中的索引
                user_index = None
                for i, orig_user in enumerate(users):
                    if orig_user.get('phone') == user.get('phone'):
                        user_index = i
                        break
                
                if user_index is not None:
                    # 如果有位置信息，传递给签到函数
                    if location_info:
                        result = sign_by_index(user_index, location_preset_item=location_id)
                    else:
                        result = sign_by_index(user_index)
                else:
                    # 如果找不到索引，使用手机号签到
                    if location_info:
                        result = sign_by_phone(user.get('phone'), location_preset_item=location_id)
                    else:
                        result = sign_by_phone(user.get('phone'))
                
                # 根据签到结果判断成功状态
                is_success = result.get('status', False) if isinstance(result, dict) else False
                message = result.get('message', str(result)) if isinstance(result, dict) else str(result)
                
                # 注意：统计记录已经在sign_by_index/sign_by_phone函数中处理了
                # 这里只需要记录结果
                results.append({
                    'user': user.get('username', '未知用户'),
                    'phone': user.get('phone', ''),
                    'success': is_success,
                    'message': message
                })
            except Exception as e:
                # 记录签到异常的统计
                try:
                    from utils.stats import record_sign_result
                    record_sign_result(
                        user_phone=user.get('phone', ''),
                        username=user.get('username', '未知用户'),
                        success=False,
                        message=f"签到异常: {str(e)}"
                    )
                except Exception as stats_e:
                    print(f"记录统计信息失败: {stats_e}")
                
                results.append({
                    'user': user.get('username', '未知用户'),
                    'phone': user.get('phone', ''),
                    'success': False,
                    'message': str(e)
                })
        
        return jsonify({
            'success': True,
            'data': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'批量签到失败: {str(e)}'
        })

@sign_bp.route('/api/sign_user', methods=['POST'])
def sign_user():
    """单个用户签到"""
    try:
        if not sign_functions_available:
            return jsonify({
                'success': False,
                'message': '签到功能模块不可用'
            })
            
        data = request.get_json()
        user_id = data.get('user_id')
        location_id = data.get('location_id')
        
        if user_id is None:
            return jsonify({
                'success': False,
                'message': '缺少用户ID'
            })
        
        users = safe_get_users()
        if user_id >= len(users):
            return jsonify({
                'success': False,
                'message': '用户ID无效'
            })
        
        # 获取位置信息
        location_info = None
        if location_id is not None:
            locations = get_locations()
            # 确保 location_id 是整数类型
            try:
                location_id = int(location_id)
                if 0 <= location_id < len(locations):
                    location_info = locations[location_id]
            except (ValueError, TypeError):
                # 如果转换失败，忽略位置信息
                location_id = None
        
        user = users[user_id]
        
        # 根据是否有位置信息调用不同的签到方法
        if location_info:
            result = sign_by_index(user_id, location_preset_item=location_id)
        else:
            result = sign_by_index(user_id)
        
        # 处理返回结果格式
        # 注意：统计记录已经在sign_by_index函数中处理了
        if isinstance(result, dict):
            is_success = result.get('status', False)
            message = result.get('message', str(result))
        else:
            is_success = False
            message = str(result)
        
        return jsonify({
            'success': True,
            'data': {
                'user': user.get('username', '未知用户'),
                'phone': user.get('phone', ''),
                'success': is_success,
                'message': message
            }
        })
    except Exception as e:
        # 记录签到异常的统计
        try:
            from utils.stats import record_sign_result
            # 尝试获取用户信息
            users = safe_get_users()
            data = request.get_json()
            user_id = data.get('user_id')
            if user_id is not None and user_id < len(users):
                user = users[user_id]
                record_sign_result(
                    user_phone=user.get('phone', ''),
                    username=user.get('username', '未知用户'),
                    success=False,
                    message=f"单个用户签到异常: {str(e)}"
                )
        except Exception as stats_e:
            print(f"记录统计信息失败: {stats_e}")
        
        return jsonify({
            'success': False,
            'message': f'签到失败: {str(e)}'
        })

@sign_bp.route('/api/location_sign', methods=['POST'])
def location_sign_api():
    """位置签到"""
    try:
        if not location_functions_available:
            return jsonify({
                'success': False,
                'message': '位置签到功能模块不可用'
            })
            
        data = request.get_json()
        
        # 这里需要根据实际参数调用location_sign函数
        result = location_sign(data)
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'位置签到失败: {str(e)}'
        })

@sign_bp.route('/api/sign_activity', methods=['POST'])
def api_sign_activity():
    """对指定活动进行签到"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        activity_id = data.get('activity_id')
        sign_type = data.get('sign_type', 'general')
        location_id = data.get('location_id')
        
        if not user_id or not activity_id:
            return jsonify({
                'success': False,
                'message': '用户ID和活动ID不能为空'
            }), 400
        
        # 根据签到类型执行不同的签到方法
        if sign_type == 'photo':
            from functions.photo import photo_sign
            result = photo_sign(user_id, activity_id)
        elif sign_type == 'location':
            from functions.location import location_sign
            result = location_sign(user_id, activity_id, location_id)
        elif sign_type == 'gesture':
            from functions.gesture import gesture_sign
            result = gesture_sign(user_id, activity_id)
        elif sign_type == 'qrcode':
            from functions.qrcode import qrcode_sign
            result = qrcode_sign(user_id, activity_id)
        else:
            from functions.general import general_sign
            result = general_sign(user_id, activity_id)
        
        return jsonify({
            'success': True,
            'message': '签到成功',
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'签到失败: {str(e)}'
        }), 500 