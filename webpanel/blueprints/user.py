# -*- coding: utf-8 -*-
"""
用户管理模块蓝图
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
import json
import os

# 安全导入功能模块
try:
    from utils.file import get_all_users, store_user, get_stored_user, delete_user, save_user_cookies
    file_functions_available = True
except ImportError as e:
    print(f"文件功能模块导入失败: {e}")
    file_functions_available = False

try:
    from functions.user import user_login, get_courses, get_account_info
    user_functions_available = True
except ImportError as e:
    print(f"用户功能模块导入失败: {e}")
    user_functions_available = False

def safe_get_users():
    """安全获取用户列表"""
    if file_functions_available:
        try:
            return get_all_users()
        except Exception as e:
            print(f"获取用户列表失败: {e}")
            return []
    return []

def get_user_by_id(user_id):
    """根据ID获取用户的适配器函数"""
    try:
        users = safe_get_users()
        if isinstance(user_id, str) and user_id.isdigit():
            user_id = int(user_id)
        if isinstance(user_id, int) and 0 <= user_id < len(users):
            return users[user_id]
        return None
    except:
        return None

def add_user(username, password, name):
    """添加用户的适配器函数"""
    try:
        # 这里需要根据实际需求实现用户添加功能
        return {'status': True, 'message': '用户添加功能待实现'}
    except Exception as e:
        return {'status': False, 'message': str(e)}

def update_user(user_id, user_data):
    """更新用户的适配器函数"""
    try:
        # 这里需要根据实际需求实现用户更新功能
        return {'status': True, 'message': '用户更新功能待实现'}
    except Exception as e:
        return {'status': False, 'message': str(e)}

def delete_user_adapter(user_id):
    """删除用户的适配器函数"""
    try:
        # 这里需要根据实际需求实现用户删除功能
        return {'status': True, 'message': '用户删除功能待实现'}
    except Exception as e:
        return {'status': False, 'message': str(e)}

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/')
def index():
    """用户管理首页"""
    try:
        users = safe_get_users()
        return render_template('user_management.html', users=users)
    except Exception as e:
        flash(f'获取用户列表失败: {str(e)}', 'error')
        return render_template('user_management.html', users=[])

@user_bp.route('/add', methods=['GET', 'POST'])
def add():
    """添加用户页面和处理表单提交"""
    if request.method == 'GET':
        # 检查是否有查询参数（处理GET方式的表单提交）
        phone = request.args.get('phone')
        password = request.args.get('password')
        active = request.args.get('active') == 'on'
        
        if phone and password:
            # 处理GET方式提交的用户添加
            try:
                if not file_functions_available:
                    flash('文件功能模块不可用', 'error')
                    return render_template('user/add.html')
                    
                if not user_functions_available:
                    flash('用户功能模块不可用', 'error')
                    return render_template('user/add.html')
                
                # 尝试登录验证
                result = user_login(phone, password)
                if result.get('success'):
                    # 获取用户信息
                    user_info = result.get('user_info', {})
                    
                    # 保存用户信息
                    user_data = {
                        'phone': phone,
                        'username': user_info.get('username', '未知用户'),
                        'password': password,  # 保存密码用于后续刷新Cookie
                        'cookies': result.get('cookies', {}),
                        'active': active
                    }
                    
                    store_user(phone, user_data)
                    flash('用户添加成功！', 'success')
                    return redirect(url_for('user.index'))
                else:
                    flash('用户验证失败: ' + result.get('message', '未知错误'), 'error')
                    
            except Exception as e:
                flash(f'添加用户失败: {str(e)}', 'error')
        
        # 获取位置列表
        try:
            from webpanel.blueprints.sign import get_locations
            locations = get_locations()
        except:
            locations = []
        
        return render_template('user/add.html', locations=locations)
    
    # 处理POST请求（表单提交）
    elif request.method == 'POST':
        try:
            if not file_functions_available:
                flash('文件功能模块不可用', 'error')
                return render_template('user/add.html')
                
            if not user_functions_available:
                flash('用户功能模块不可用', 'error')
                return render_template('user/add.html')
            
            phone = request.form.get('phone')
            password = request.form.get('password')
            active = request.form.get('active') == 'on'
            default_location_id = request.form.get('default_location_id')
            
            if not phone or not password:
                flash('手机号和密码不能为空', 'error')
                return render_template('user/add.html')
            
            # 尝试登录验证
            result = user_login(phone, password)
            if result.get('success'):
                # 获取用户信息
                user_info = result.get('user_info', {})
                
                # 保存用户信息
                user_data = {
                    'phone': phone,
                    'username': user_info.get('username', '未知用户'),
                    'password': password,  # 保存密码用于后续刷新Cookie
                    'cookies': result.get('cookies', {}),
                    'active': active,
                    'default_location_id': default_location_id
                }
                
                store_user(phone, user_data)
                flash('用户添加成功！', 'success')
                return redirect(url_for('user.index'))
            else:
                flash('用户验证失败: ' + result.get('message', '未知错误'), 'error')
                
        except Exception as e:
            flash(f'添加用户失败: {str(e)}', 'error')
        
        # 获取位置列表
        try:
            from webpanel.blueprints.sign import get_locations
            locations = get_locations()
        except:
            locations = []
        
        return render_template('user/add.html', locations=locations)

@user_bp.route('/edit/<user_id>')
def edit(user_id):
    """编辑用户页面"""
    try:
        user = get_user_by_id(user_id)
        if not user:
            flash('用户不存在', 'error')
            return redirect(url_for('user.index'))
        return render_template('user/edit.html', user=user)
    except Exception as e:
        flash(f'获取用户信息失败: {str(e)}', 'error')
        return redirect(url_for('user.index'))

@user_bp.route('/api/users')
def get_users_api():
    """获取所有用户"""
    try:
        users = safe_get_users()
        return jsonify({
            'success': True,
            'data': users
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取用户列表失败: {str(e)}'
        })

@user_bp.route('/api/locations')
def get_locations_for_user():
    """获取位置列表供用户选择"""
    try:
        # 导入位置获取函数
        from webpanel.blueprints.sign import get_locations
        locations = get_locations()
        
        # 添加默认位置选项
        location_options = [
            {'id': 'default', 'name': '默认位置', 'address': '使用系统默认位置', 'is_default': True}
        ]
        
        # 添加已配置的位置
        for location in locations:
            location_options.append({
                'id': location.get('id', 0),
                'name': location.get('name', ''),
                'address': location.get('address', ''),
                'lat': location.get('lat', ''),
                'lon': location.get('lon', ''),
                'is_default': False
            })
        
        return jsonify({
            'success': True,
            'data': location_options
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取位置列表失败: {str(e)}'
        })

@user_bp.route('/api/add', methods=['POST'])
def add_user_api():
    """添加用户"""
    try:
        if not file_functions_available:
            return jsonify({
                'success': False,
                'message': '文件功能模块不可用'
            })
            
        if not user_functions_available:
            return jsonify({
                'success': False,
                'message': '用户功能模块不可用'
            })
            
        data = request.get_json()
        phone = data.get('phone')
        password = data.get('password')
        default_location_id = data.get('default_location_id')
        
        if not phone or not password:
            return jsonify({
                'success': False,
                'message': '手机号和密码不能为空'
            })
        
        # 尝试登录验证
        result = user_login(phone, password)
        if result.get('success'):
            # 获取用户信息
            user_info = result.get('user_info', {})
            
            # 保存用户信息
            user_data = {
                'phone': phone,
                'username': user_info.get('username', '未知用户'),
                'password': password,  # 保存密码用于后续刷新Cookie
                'cookies': result.get('cookies', {}),
                'active': True,
                'default_location_id': default_location_id
            }
            
            store_user(phone, user_data)
            
            return jsonify({
                'success': True,
                'message': '用户添加成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '用户验证失败: ' + result.get('message', '未知错误')
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'添加用户失败: {str(e)}'
        })

@user_bp.route('/api/delete', methods=['DELETE'])
def delete_user_api():
    """删除用户"""
    try:
        if not file_functions_available:
            return jsonify({
                'success': False,
                'message': '文件功能模块不可用'
            })
            
        data = request.get_json()
        phone = data.get('phone')
        
        if not phone:
            return jsonify({
                'success': False,
                'message': '手机号不能为空'
            })
        
        # 这里调用的是utils.file中的delete_user函数
        from utils.file import delete_user as file_delete_user
        result = file_delete_user(phone)
        
        if result:
            return jsonify({
                'success': True,
                'message': '用户删除成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '用户不存在或删除失败'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除用户失败: {str(e)}'
        })

@user_bp.route('/api/toggle_status', methods=['POST'])
def toggle_user_status():
    """切换用户状态"""
    try:
        if not file_functions_available:
            return jsonify({
                'success': False,
                'message': '文件功能模块不可用'
            })
            
        data = request.get_json()
        phone = data.get('phone')
        
        if not phone:
            return jsonify({
                'success': False,
                'message': '手机号不能为空'
            })
        
        user = get_stored_user(phone)
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            })
        
        # 切换状态
        user['active'] = not user.get('active', True)
        store_user(phone, user)
        
        return jsonify({
            'success': True,
            'message': f'用户状态已切换为{"激活" if user["active"] else "停用"}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'切换用户状态失败: {str(e)}'
        })

@user_bp.route('/api/update', methods=['PUT'])
def update_user():
    """更新用户信息"""
    try:
        if not file_functions_available:
            return jsonify({
                'success': False,
                'message': '文件功能模块不可用'
            })
            
        data = request.get_json()
        phone = data.get('phone')
        
        if not phone:
            return jsonify({
                'success': False,
                'message': '手机号不能为空'
            })
        
        user = get_stored_user(phone)
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            })
        
        # 更新用户信息（用户名由系统自动获取，不允许手动修改）
        if data.get('password'):
            # 如果提供了新密码，需要重新登录验证
            if not user_functions_available:
                return jsonify({
                    'success': False,
                    'message': '用户功能模块不可用，无法更新密码'
                })
            
            result = user_login(phone, data.get('password'))
            if result.get('success'):
                # 更新用户信息和cookies
                user_info = result.get('user_info', {})
                user.update({
                    'username': user_info.get('username', user.get('username')),  # 重新获取最新用户名
                    'password': data.get('password'),  # 保存新密码
                    'cookies': result.get('cookies', {}),
                    'active': data.get('auto_login', user.get('active', True)),
                    'default_location_id': data.get('default_location_id', user.get('default_location_id'))
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '密码验证失败: ' + result.get('message', '未知错误')
                })
        else:
            # 仅更新状态和位置
            user.update({
                'active': data.get('auto_login', user.get('active', True)),
                'default_location_id': data.get('default_location_id', user.get('default_location_id'))
            })
        
        store_user(phone, user)
        
        return jsonify({
            'success': True,
            'message': '用户信息更新成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'更新用户失败: {str(e)}'
        })

@user_bp.route('/api/stats')
def get_user_stats():
    """获取用户统计信息"""
    try:
        users = safe_get_users()
        total_users = len(users)
        active_users = len([u for u in users if u.get('active', True)])
        
        # 这里可以添加更多统计逻辑，比如今日签到数、成功率等
        # 暂时使用占位符数据
        stats = {
            'total': total_users,
            'active': active_users,
            'today_signins': 0,  # 需要从签到记录获取
            'success_rate': 0    # 需要从签到记录计算
        }
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取统计信息失败: {str(e)}'
        })

@user_bp.route('/api/list')
def get_user_list():
    """获取用户列表（支持分页和搜索）"""
    try:
        print("=== 用户列表API被调用 ===")
        users = safe_get_users()
        print(f"获取到的原始用户数据: {users}")
        print(f"用户数量: {len(users)}")
        
        # 获取查询参数
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '').strip()
        print(f"查询参数: page={page}, per_page={per_page}, search='{search}', status='{status}'")
        
        # 过滤用户
        filtered_users = []
        for user in users:
            # 搜索过滤
            if search:
                if search not in str(user.get('phone', '')) and search not in str(user.get('username', '')):
                    continue
            
            # 状态过滤
            if status == 'active' and not user.get('active', True):
                continue
            elif status == 'inactive' and user.get('active', True):
                continue
            
            # 格式化用户数据
            formatted_user = {
                'phone': str(user.get('phone', '')),
                'name': str(user.get('username', '未知用户')),
                'school': str(user.get('school', '-')),
                'last_login': str(user.get('last_login', '-')),
                'status': 'active' if user.get('active', True) else 'inactive',
                'signin_count': int(user.get('signin_count', 0)),
                'default_location_id': user.get('default_location_id')
            }
            print(f"格式化用户数据: {formatted_user}")  # 调试信息
            filtered_users.append(formatted_user)
        
        # 分页计算
        total_users = len(filtered_users)
        total_pages = (total_users + per_page - 1) // per_page if total_users > 0 else 1
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        paginated_users = filtered_users[start_idx:end_idx]
        
        pagination_info = {
            'current_page': page,
            'total_pages': total_pages,
            'total_items': total_users,
            'per_page': per_page
        }
        
        result = {
            'success': True,
            'data': {
                'users': paginated_users,
                'pagination': pagination_info
            }
        }
        print(f"返回结果: {result}")
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取用户列表失败: {str(e)}'
        })

@user_bp.route('/api/get')
def get_single_user():
    """获取单个用户信息"""
    try:
        phone = request.args.get('phone')
        if not phone:
            return jsonify({
                'success': False,
                'message': '手机号不能为空'
            })
        
        user = get_stored_user(phone)
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            })
        
        formatted_user = {
            'phone': user.get('phone', ''),
            'username': user.get('username', '未知用户'),
            'auto_login': user.get('active', True),
            'default_location_id': user.get('default_location_id')
        }
        
        return jsonify({
            'success': True,
            'data': formatted_user
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取用户信息失败: {str(e)}'
        })

@user_bp.route('/api/batch_delete', methods=['DELETE'])
def batch_delete_users():
    """批量删除用户"""
    try:
        if not file_functions_available:
            return jsonify({
                'success': False,
                'message': '文件功能模块不可用'
            })
            
        data = request.get_json() or {}
        phones = data.get('phones', [])
        
        if not phones:
            return jsonify({
                'success': False,
                'message': '未选择要删除的用户'
            })
        
        deleted_count = 0
        from utils.file import delete_user as file_delete_user
        
        for phone in phones:
            try:
                if file_delete_user(phone):
                    deleted_count += 1
            except:
                pass
        
        return jsonify({
            'success': True,
            'message': f'成功删除 {deleted_count} 个用户'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'批量删除失败: {str(e)}'
        })

@user_bp.route('/api/batch_disable', methods=['POST'])
def batch_disable_users():
    """批量禁用用户"""
    try:
        if not file_functions_available:
            return jsonify({
                'success': False,
                'message': '文件功能模块不可用'
            })
            
        data = request.get_json() or {}
        phones = data.get('phones', [])
        
        if not phones:
            return jsonify({
                'success': False,
                'message': '未选择要禁用的用户'
            })
        
        updated_count = 0
        for phone in phones:
            try:
                user = get_stored_user(phone)
                if user:
                    user['active'] = False
                    store_user(phone, user)
                    updated_count += 1
            except:
                pass
        
        return jsonify({
            'success': True,
            'message': f'成功禁用 {updated_count} 个用户'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'批量禁用失败: {str(e)}'
        })

@user_bp.route('/api/batch_enable', methods=['POST'])
def batch_enable_users():
    """批量启用用户"""
    try:
        if not file_functions_available:
            return jsonify({
                'success': False,
                'message': '文件功能模块不可用'
            })
            
        data = request.get_json() or {}
        phones = data.get('phones', [])
        
        if not phones:
            return jsonify({
                'success': False,
                'message': '未选择要启用的用户'
            })
        
        updated_count = 0
        for phone in phones:
            try:
                user = get_stored_user(phone)
                if user:
                    user['active'] = True
                    store_user(phone, user)
                    updated_count += 1
            except:
                pass
        
        return jsonify({
            'success': True,
            'message': f'成功启用 {updated_count} 个用户'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'批量启用失败: {str(e)}'
        })

@user_bp.route('/api/refresh_cookie', methods=['POST'])
def refresh_user_cookie():
    """刷新单个用户的Cookie"""
    try:
        if not file_functions_available:
            return jsonify({
                'success': False,
                'message': '文件功能模块不可用'
            })
            
        if not user_functions_available:
            return jsonify({
                'success': False,
                'message': '用户功能模块不可用'
            })
            
        data = request.get_json()
        phone = data.get('phone')
        
        if not phone:
            return jsonify({
                'success': False,
                'message': '手机号不能为空'
            })
        
        # 获取用户信息
        user = get_stored_user(phone)
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            })
        
        # 检查用户是否有密码信息（用于重新登录）
        if 'password' not in user:
            return jsonify({
                'success': False,
                'message': '用户密码信息缺失，无法刷新Cookie'
            })
        
        # 重新登录获取新的Cookie
        result = user_login(phone, user['password'])
        if result.get('success'):
            # 更新用户的Cookie信息
            user['cookies'] = result.get('cookies', {})
            if 'user_info' in result:
                user['username'] = result['user_info'].get('username', user.get('username', '未知用户'))
            
            # 保存更新后的用户信息
            store_user(phone, user)
            
            return jsonify({
                'success': True,
                'message': 'Cookie刷新成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'重新登录失败: {result.get("message", "未知错误")}'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'刷新Cookie失败: {str(e)}'
        })

@user_bp.route('/api/batch_refresh_cookies', methods=['POST'])
def batch_refresh_cookies():
    """批量刷新用户Cookie"""
    try:
        if not file_functions_available:
            return jsonify({
                'success': False,
                'message': '文件功能模块不可用'
            })
            
        if not user_functions_available:
            return jsonify({
                'success': False,
                'message': '用户功能模块不可用'
            })
            
        data = request.get_json() or {}
        phones = data.get('phones', [])
        
        if not phones:
            return jsonify({
                'success': False,
                'message': '未选择要刷新的用户'
            })
        
        success_count = 0
        failed_count = 0
        failed_users = []
        
        for phone in phones:
            try:
                # 获取用户信息
                user = get_stored_user(phone)
                if not user:
                    failed_count += 1
                    failed_users.append(f"{phone}(用户不存在)")
                    continue
                
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
        
        response_data = {
            'success_count': success_count,
            'failed_count': failed_count,
            'total_count': len(phones)
        }
        
        if failed_users:
            response_data['failed_users'] = failed_users
        
        return jsonify({
            'success': True,
            'message': f'批量刷新完成，成功: {success_count}，失败: {failed_count}',
            'data': response_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'批量刷新Cookie失败: {str(e)}'
        })

@user_bp.route('/api/refresh_all_cookies', methods=['POST'])
def refresh_all_cookies():
    """刷新所有用户的Cookie"""
    try:
        if not file_functions_available:
            return jsonify({
                'success': False,
                'message': '文件功能模块不可用'
            })
            
        if not user_functions_available:
            return jsonify({
                'success': False,
                'message': '用户功能模块不可用'
            })
        
        # 获取所有用户
        users = safe_get_users()
        if not users:
            return jsonify({
                'success': False,
                'message': '没有找到任何用户'
            })
        
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
        
        response_data = {
            'success_count': success_count,
            'failed_count': failed_count,
            'total_count': len(users)
        }
        
        if failed_users:
            response_data['failed_users'] = failed_users
        
        return jsonify({
            'success': True,
            'message': f'全部刷新完成，成功: {success_count}，失败: {failed_count}',
            'data': response_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'全部刷新Cookie失败: {str(e)}'
        }) 