# -*- coding: utf-8 -*-
"""
API模块蓝图
"""

from flask import Blueprint, jsonify, request, send_file
from datetime import datetime, timedelta
import os
import json
import platform
import sys
import psutil
import zipfile
import tempfile
from werkzeug.utils import secure_filename

api_bp = Blueprint('api', __name__)

@api_bp.route('/health')
def health():
    """健康检查API"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@api_bp.route('/stats')
def stats():
    """系统统计API"""
    try:
        from functions.user import get_local_users
        
        users = get_local_users()
        
        stats = {
            'total_users': len(users),
            'total_locations': 0,  # 可以根据实际需要实现
            'today_signs': 0,  # 可以从日志文件中统计
            'system_uptime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取统计信息失败: {str(e)}'
        }), 500

# 用户相关API
@api_bp.route('/user/stats')
def user_stats():
    """用户统计API"""
    try:
        from functions.user import get_local_users
        
        users = get_local_users()
        active_users = len([u for u in users if u.get('status') == 'active'])
        
        stats = {
            'total': len(users),
            'active': active_users,
            'today_signins': 0,  # 可以从日志统计
            'success_rate': 85.5  # 示例数据
        }
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取用户统计失败: {str(e)}'
        }), 500

@api_bp.route('/user/list')
def user_list():
    """用户列表API"""
    try:
        from functions.user import get_local_users
        
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        search = request.args.get('search', '')
        status_filter = request.args.get('status', '')
        
        users = get_local_users()
        
        # 搜索过滤
        if search:
            users = [u for u in users if search.lower() in u.get('phone', '').lower() 
                    or search.lower() in u.get('name', '').lower()]
        
        # 状态过滤
        if status_filter:
            users = [u for u in users if u.get('status') == status_filter]
        
        # 分页
        total = len(users)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_users = users[start:end]
        
        # 格式化用户数据
        formatted_users = []
        for user in paginated_users:
            formatted_users.append({
                'phone': user.get('phone', ''),
                'name': user.get('name', ''),
                'school': user.get('school', ''),
                'last_login': user.get('last_login', ''),
                'status': user.get('status', 'inactive'),
                'signin_count': user.get('signin_count', 0),
                'default_location_id': user.get('default_location_id')
            })
        
        return jsonify({
            'success': True,
            'data': {
                'users': formatted_users,
                'pagination': {
                    'current_page': page,
                    'per_page': per_page,
                    'total': total,
                    'total_pages': (total + per_page - 1) // per_page
                }
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取用户列表失败: {str(e)}'
        }), 500

@api_bp.route('/user/add', methods=['POST'])
def add_user():
    """添加用户API"""
    try:
        data = request.form
        phone = data.get('phone')
        password = data.get('password')
        name = data.get('name', '')
        school = data.get('school', '')
        auto_login = data.get('auto_login') == 'true'
        
        if not phone or not password:
            return jsonify({
                'success': False,
                'message': '手机号和密码不能为空'
            }), 400
        
        # 这里应该调用实际的添加用户函数
        # 示例实现
        user_data = {
            'phone': phone,
            'password': password,
            'name': name,
            'school': school,
            'auto_login': auto_login,
            'status': 'active',
            'created_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'message': '用户添加成功',
            'data': user_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'添加用户失败: {str(e)}'
        }), 500

@api_bp.route('/user/get')
def get_user():
    """获取单个用户信息API"""
    try:
        phone = request.args.get('phone')
        if not phone:
            return jsonify({
                'success': False,
                'message': '用户手机号不能为空'
            }), 400
        
        from functions.user import get_local_users
        users = get_local_users()
        user = next((u for u in users if u.get('phone') == phone), None)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': user
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取用户信息失败: {str(e)}'
        }), 500

@api_bp.route('/user/update', methods=['PUT'])
def update_user():
    """更新用户API"""
    try:
        data = request.form
        phone = data.get('phone')
        
        if not phone:
            return jsonify({
                'success': False,
                'message': '用户手机号不能为空'
            }), 400
        
        # 这里应该调用实际的更新用户函数
        return jsonify({
            'success': True,
            'message': '用户更新成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'更新用户失败: {str(e)}'
        }), 500

@api_bp.route('/user/delete', methods=['DELETE'])
def delete_user():
    """删除用户API"""
    try:
        phone = request.form.get('phone')
        
        if not phone:
            return jsonify({
                'success': False,
                'message': '用户手机号不能为空'
            }), 400
        
        # 这里应该调用实际的删除用户函数
        return jsonify({
            'success': True,
            'message': '用户删除成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除用户失败: {str(e)}'
        }), 500

# 系统相关API
@api_bp.route('/system/schedule_tasks')
def schedule_tasks():
    """获取定时任务列表"""
    try:
        # 示例数据，实际应该从调度器获取
        tasks = [
            {
                'id': '1',
                'name': '自动签到任务',
                'schedule': '0 8 * * *',
                'status': 'active',
                'next_run': '2024-01-01 08:00:00'
            }
        ]
        
        scheduler = {
            'status': 'running',
            'uptime': '2天3小时',
            'active_tasks': len(tasks)
        }
        
        return jsonify({
            'success': True,
            'data': {
                'tasks': tasks,
                'scheduler': scheduler
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取定时任务失败: {str(e)}'
        }), 500

@api_bp.route('/system/logs')
def system_logs():
    """获取系统日志"""
    try:
        level = request.args.get('level', '')
        source = request.args.get('source', '')
        date = request.args.get('date', '')
        
        # 示例日志数据
        logs = [
            {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'level': 'INFO',
                'source': 'sign',
                'message': '用户签到成功'
            },
            {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'level': 'ERROR',
                'source': 'system',
                'message': '网络连接超时'
            }
        ]
        
        stats = {
            'today_error': 2,
            'today_warning': 5,
            'today_info': 15,
            'file_size': '2.5 MB',
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return jsonify({
            'success': True,
            'data': {
                'logs': logs,
                'stats': stats
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取日志失败: {str(e)}'
        }), 500

@api_bp.route('/system/monitor')
def system_monitor():
    """获取系统监控数据"""
    try:
        # 获取系统资源信息
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        resources = {
            'cpu_percent': cpu_percent,
            'memory_used': memory.used,
            'memory_total': memory.total,
            'disk_used': disk.used,
            'disk_total': disk.total
        }
        
        app = {
            'uptime': '2天3小时',
            'total_requests': 1250,
            'active_connections': 5,
            'avg_response_time': 45
        }
        
        # 历史数据（示例）
        history = []
        for i in range(10):
            history.append({
                'timestamp': (datetime.now() - timedelta(minutes=i)).strftime('%H:%M'),
                'cpu_percent': cpu_percent + (i * 2),
                'memory_percent': (memory.used / memory.total * 100) + (i * 1)
            })
        
        return jsonify({
            'success': True,
            'data': {
                'resources': resources,
                'app': app,
                'history': history[::-1]  # 反转顺序
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取监控数据失败: {str(e)}'
        }), 500

@api_bp.route('/system/config')
def get_system_config():
    """获取系统配置"""
    try:
        # 示例配置数据
        config = {
            'default_sign_type': 'location',
            'sign_timeout': 30,
            'retry_count': 3,
            'enable_auto_sign': True,
            'enable_email_notification': False,
            'smtp_server': '',
            'smtp_port': 587,
            'email_sender': '',
            'email_password': '',
            'api_interval': 1000,
            'concurrent_limit': 5,
            'enable_debug_mode': False,
            'enable_statistics': True
        }
        
        return jsonify({
            'success': True,
            'data': config
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取系统配置失败: {str(e)}'
        }), 500

@api_bp.route('/system/config', methods=['POST'])
def save_system_config():
    """保存系统配置"""
    try:
        config = request.get_json()
        
        # 这里应该保存配置到文件或数据库
        # 示例实现
        config_file = 'configs/system_config.json'
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'message': '系统配置保存成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'保存系统配置失败: {str(e)}'
        }), 500

@api_bp.route('/system/info')
def system_info():
    """获取系统信息"""
    try:
        import flask
        
        info = {
            'version': '1.0.0',
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'flask_version': flask.__version__,
            'os_info': f"{platform.system()} {platform.release()}",
            'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return jsonify({
            'success': True,
            'data': info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取系统信息失败: {str(e)}'
        }), 500

@api_bp.route('/system/backup/export')
def backup_export():
    """导出系统备份"""
    try:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
            with zipfile.ZipFile(tmp_file, 'w') as zipf:
                # 添加配置文件
                config_dir = 'configs'
                if os.path.exists(config_dir):
                    for root, dirs, files in os.walk(config_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            zipf.write(file_path, file_path)
                
                # 添加用户数据
                users_file = 'users.json'
                if os.path.exists(users_file):
                    zipf.write(users_file, users_file)
                
                # 添加备份元信息
                backup_info = {
                    'backup_time': datetime.now().isoformat(),
                    'version': '1.0.0',
                    'description': '系统备份文件'
                }
                zipf.writestr('backup_info.json', json.dumps(backup_info, ensure_ascii=False, indent=2))
            
            return send_file(
                tmp_file.name,
                as_attachment=True,
                download_name=f'chaoxing_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip',
                mimetype='application/zip'
            )
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'导出备份失败: {str(e)}'
        }), 500

@api_bp.route('/system/backup/restore', methods=['POST'])
def backup_restore():
    """恢复系统备份"""
    try:
        if 'backup_file' not in request.files:
            return jsonify({
                'success': False,
                'message': '未选择备份文件'
            }), 400
        
        file = request.files['backup_file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': '未选择备份文件'
            }), 400
        
        if file and file.filename.endswith('.zip'):
            # 保存上传的文件
            filename = secure_filename(file.filename)
            temp_path = os.path.join(tempfile.gettempdir(), filename)
            file.save(temp_path)
            
            # 解压备份文件
            with zipfile.ZipFile(temp_path, 'r') as zipf:
                zipf.extractall('.')
            
            # 清理临时文件
            os.remove(temp_path)
            
            return jsonify({
                'success': True,
                'message': '系统备份恢复成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '无效的备份文件格式'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'恢复备份失败: {str(e)}'
        }), 500

@api_bp.route('/system/scheduler/start', methods=['POST'])
def start_scheduler():
    """启动调度器"""
    try:
        # 这里应该调用实际的调度器启动函数
        return jsonify({
            'success': True,
            'message': '调度器启动成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'启动调度器失败: {str(e)}'
        }), 500

@api_bp.route('/system/scheduler/stop', methods=['POST'])
def stop_scheduler():
    """停止调度器"""
    try:
        # 这里应该调用实际的调度器停止函数
        return jsonify({
            'success': True,
            'message': '调度器已停止'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'停止调度器失败: {str(e)}'
        }), 500

@api_bp.route('/system/logs/clear', methods=['DELETE'])
def clear_logs():
    """清除系统日志"""
    try:
        # 这里应该清除实际的日志文件
        logs_dir = 'logs'
        if os.path.exists(logs_dir):
            for file in os.listdir(logs_dir):
                if file.endswith('.log'):
                    os.remove(os.path.join(logs_dir, file))
        
        return jsonify({
            'success': True,
            'message': '日志清除成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'清除日志失败: {str(e)}'
        }), 500 