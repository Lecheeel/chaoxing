# -*- coding: utf-8 -*-
"""
系统设置模块蓝图
"""

from flask import Blueprint, render_template, request, jsonify, flash
import os
import json
from datetime import datetime
from utils.file import get_json_object, save_json_object
from utils.schedule_task import (
    initialize_scheduler, 
    get_scheduler_status, 
    stop_scheduler_thread,
    get_schedule_tasks,
    create_task,
    update_task,
    delete_task,
    get_task,
    restart_scheduler
)
import sys
import psutil

# 安全导入位置功能
try:
    from functions.location import location_sign, location_sign_2
    location_functions_available = True
except ImportError as e:
    print(f"位置功能模块导入失败: {e}")
    location_functions_available = False

def get_locations():
    """获取位置列表的适配器函数"""
    try:
        # 从配置文件中读取预设位置
        config = get_json_object('configs/storage.json')
        return config.get('locations', [])
    except Exception as e:
        print(f"获取位置列表失败: {e}")
        return []

def add_location(location_data):
    """添加位置的适配器函数"""
    try:
        config = get_json_object('configs/storage.json')
        if 'locations' not in config:
            config['locations'] = []
        
        # 生成位置ID
        location_data['id'] = len(config['locations'])
        
        config['locations'].append(location_data)
        save_json_object('configs/storage.json', config)
        return {'status': True, 'message': '位置添加成功'}
    except Exception as e:
        return {'status': False, 'message': str(e)}

def delete_location(location_id):
    """删除位置的适配器函数"""
    try:
        config = get_json_object('configs/storage.json')
        locations = config.get('locations', [])
        
        # 确保 location_id 是整数类型
        try:
            location_id = int(location_id)
            if 0 <= location_id < len(locations):
                removed = locations.pop(location_id)
                config['locations'] = locations
                save_json_object('configs/storage.json', config)
                return {'status': True, 'message': f'位置 {removed.get("name", "")} 删除成功'}
            else:
                return {'status': False, 'message': '位置ID无效'}
        except (ValueError, TypeError):
            return {'status': False, 'message': '位置ID格式无效'}
    except Exception as e:
        return {'status': False, 'message': str(e)}

system_bp = Blueprint('system', __name__, url_prefix='/system')

@system_bp.route('/')
def index():
    """系统设置首页"""
    return render_template('system_settings.html')

@system_bp.route('/tasks')
def tasks():
    """定时任务管理"""
    try:
        tasks = get_schedule_tasks()
        return render_template('system/tasks.html', tasks=tasks)
    except Exception as e:
        flash(f'获取任务列表失败: {str(e)}', 'error')
        return render_template('system/tasks.html', tasks=[])

@system_bp.route('/locations')
def locations():
    """位置管理"""
    try:
        locations = get_locations()
        return render_template('system/locations.html', locations=locations)
    except Exception as e:
        flash(f'获取位置列表失败: {str(e)}', 'error')
        return render_template('system/locations.html', locations=[])

@system_bp.route('/logs')
def logs():
    """日志查看"""
    return render_template('system/logs.html')

@system_bp.route('/api/logs')
def get_logs():
    """获取系统日志"""
    try:
        lines = request.args.get('lines', 50, type=int)
        log_file = 'logs/scheduler.log'
        
        logs = []
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                # 取最后N行
                logs = all_lines[-lines:] if len(all_lines) > lines else all_lines
                # 移除换行符
                logs = [line.rstrip('\n') for line in logs]
        
        return jsonify({
            'success': True,
            'data': logs
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取日志失败: {str(e)}'
        })

@system_bp.route('/api/logs/list')
def get_log_files():
    """获取所有日志文件列表"""
    try:
        log_dir = 'logs'
        log_files = []
        
        if os.path.exists(log_dir):
            for filename in os.listdir(log_dir):
                if filename.endswith('.log'):
                    file_path = os.path.join(log_dir, filename)
                    if os.path.isfile(file_path):
                        stat = os.stat(file_path)
                        log_files.append({
                            'name': filename,
                            'size': stat.st_size,
                            'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                            'path': file_path
                        })
        
        # 按修改时间倒序排列
        log_files.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': log_files
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取日志文件列表失败: {str(e)}'
        })

@system_bp.route('/api/logs/<log_name>')
def get_log_content(log_name):
    """获取指定日志文件内容"""
    try:
        lines = request.args.get('lines', 100, type=int)
        log_file = f'logs/{log_name}'
        
        # 安全检查：确保只访问logs目录下的.log文件
        if not log_name.endswith('.log') or '/' in log_name or '\\' in log_name:
            return jsonify({
                'success': False,
                'message': '无效的日志文件名'
            }), 400
        
        logs = []
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                all_lines = f.readlines()
                # 取最后N行
                logs = all_lines[-lines:] if len(all_lines) > lines else all_lines
                # 移除换行符
                logs = [line.rstrip('\n') for line in logs]
        
        return jsonify({
            'success': True,
            'data': logs
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取日志内容失败: {str(e)}'
        })

@system_bp.route('/api/logs/<log_name>', methods=['DELETE'])
def delete_log(log_name):
    """删除指定日志文件"""
    try:
        # 安全检查：确保只访问logs目录下的.log文件
        if not log_name.endswith('.log') or '/' in log_name or '\\' in log_name:
            return jsonify({
                'success': False,
                'message': '无效的日志文件名'
            }), 400
        
        log_file = f'logs/{log_name}'
        
        if not os.path.exists(log_file):
            return jsonify({
                'success': False,
                'message': '日志文件不存在'
            }), 404
        
        # 删除文件
        os.remove(log_file)
        
        return jsonify({
            'success': True,
            'message': f'日志文件 {log_name} 删除成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除日志文件失败: {str(e)}'
        })

@system_bp.route('/api/logs/clear', methods=['POST'])
def clear_all_logs():
    """清空所有日志文件"""
    try:
        log_dir = 'logs'
        cleared_files = []
        
        if os.path.exists(log_dir):
            for filename in os.listdir(log_dir):
                if filename.endswith('.log'):
                    file_path = os.path.join(log_dir, filename)
                    if os.path.isfile(file_path):
                        # 清空文件内容而不是删除文件
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write('')
                        cleared_files.append(filename)
        
        return jsonify({
            'success': True,
            'message': f'已清空 {len(cleared_files)} 个日志文件',
            'data': cleared_files
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'清空日志文件失败: {str(e)}'
        })

@system_bp.route('/api/system_info')
def get_system_info():
    """获取系统信息"""
    try:
        # CPU和内存信息
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 系统运行时间（从启动开始）
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        
        system_info = {
            'cpu_percent': round(cpu_percent, 1),
            'memory_percent': round(memory.percent, 1),
            'memory_total': memory.total,
            'memory_available': memory.available,
            'disk_percent': round(disk.percent, 1),
            'disk_total': disk.total,
            'disk_free': disk.free,
            'uptime': str(uptime).split('.')[0],  # 移除微秒
            'python_version': sys.version.split()[0],
            'platform': sys.platform
        }
        
        return jsonify({
            'success': True,
            'data': system_info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取系统信息失败: {str(e)}'
        })

# 定时任务相关API
@system_bp.route('/api/scheduler_status')
def get_scheduler_status_api():
    """获取调度器状态"""
    try:
        status = get_scheduler_status()
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取调度器状态失败: {str(e)}'
        })

@system_bp.route('/api/scheduler/start', methods=['POST'])
def start_scheduler():
    """启动调度器"""
    try:
        initialize_scheduler()
        return jsonify({
            'success': True,
            'message': '调度器启动成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'启动调度器失败: {str(e)}'
        })

@system_bp.route('/api/scheduler/stop', methods=['POST'])
def stop_scheduler():
    """停止调度器"""
    try:
        stop_scheduler_thread()
        return jsonify({
            'success': True,
            'message': '调度器已停止'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'停止调度器失败: {str(e)}'
        })

@system_bp.route('/api/scheduler/restart', methods=['POST'])
def restart_scheduler_api():
    """重启调度器"""
    try:
        restart_scheduler()
        return jsonify({
            'success': True,
            'message': '调度器重启成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'重启调度器失败: {str(e)}'
        })

@system_bp.route('/api/tasks')
def get_tasks():
    """获取任务列表"""
    try:
        tasks = get_schedule_tasks()
        return jsonify({
            'success': True,
            'data': tasks
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取任务列表失败: {str(e)}'
        })

@system_bp.route('/api/tasks', methods=['POST'])
def create_task_api():
    """创建新任务"""
    try:
        print("=== 创建任务API被调用 ===")
        task_data = request.get_json()
        print(f"接收到的任务数据: {task_data}")
        
        task_id = create_task(task_data)
        print(f"任务创建成功，ID: {task_id}")
        
        return jsonify({
            'success': True,
            'data': {'id': task_id},
            'message': '任务创建成功'
        })
    except Exception as e:
        print(f"创建任务失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'创建任务失败: {str(e)}'
        })

@system_bp.route('/api/tasks/<int:task_id>')
def get_task_api(task_id):
    """获取指定任务信息"""
    try:
        task = get_task(task_id)
        if task:
            return jsonify({
                'success': True,
                'data': task
            })
        else:
            return jsonify({
                'success': False,
                'message': '任务不存在'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取任务信息失败: {str(e)}'
        })

@system_bp.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task_api(task_id):
    """更新任务"""
    try:
        task_data = request.get_json()
        success = update_task(task_id, task_data)
        if success:
            return jsonify({
                'success': True,
                'message': '任务更新成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '任务不存在'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'更新任务失败: {str(e)}'
        })

@system_bp.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task_api(task_id):
    """删除任务"""
    try:
        success = delete_task(task_id)
        if success:
            return jsonify({
                'success': True,
                'message': '任务删除成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '任务不存在'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除任务失败: {str(e)}'
        })

@system_bp.route('/api/tasks/<int:task_id>/execute', methods=['POST'])
def manual_execute_task_api(task_id):
    """手动执行任务"""
    try:
        from utils.schedule_task import execute_task
        
        # 执行任务
        result = execute_task(task_id)
        
        if result.get('status', False):
            return jsonify({
                'success': True,
                'message': result.get('message', '任务执行成功'),
                'data': {
                    'results': result.get('results', []),
                    'success_count': result.get('success_count', 0),
                    'failed_count': result.get('failed_count', 0)
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': result.get('message', '任务执行失败')
            }), 400
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'手动执行任务失败: {str(e)}'
        }), 500

@system_bp.route('/api/tasks/<int:task_id>/toggle', methods=['POST'])
def toggle_task_api(task_id):
    """切换任务状态"""
    try:
        task = get_task(task_id)
        if not task:
            return jsonify({
                'success': False,
                'message': '任务不存在'
            }), 404
        
        # 切换状态
        task['active'] = not task.get('active', True)
        success = update_task(task_id, task)
        
        if success:
            status = '启用' if task['active'] else '停用'
            return jsonify({
                'success': True,
                'message': f'任务已{status}'
            })
        else:
            return jsonify({
                'success': False,
                'message': '更新任务状态失败'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'切换任务状态失败: {str(e)}'
        })

@system_bp.route('/api/settings')
def get_settings():
    """获取系统设置"""
    try:
        # 从配置文件读取设置
        config = get_json_object('configs/settings.json')
        return jsonify({
            'success': True,
            'data': config
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取设置失败: {str(e)}'
        })

@system_bp.route('/api/settings', methods=['POST'])
def save_settings():
    """保存系统设置"""
    try:
        settings = request.get_json()
        save_json_object('configs/settings.json', settings)
        return jsonify({
            'success': True,
            'message': '设置保存成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'保存设置失败: {str(e)}'
        })

# 位置管理相关API
@system_bp.route('/api/locations')
def get_locations_api():
    """获取位置列表API"""
    try:
        locations = get_locations()
        return jsonify({
            'success': True,
            'data': locations
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取位置列表失败: {str(e)}'
        })

@system_bp.route('/api/locations', methods=['POST'])
def add_location_api():
    """添加位置API"""
    try:
        location_data = request.get_json()
        
        # 验证必填字段
        required_fields = ['name', 'address', 'lat', 'lon']
        for field in required_fields:
            if field not in location_data or not location_data[field]:
                return jsonify({
                    'success': False,
                    'message': f'缺少必填字段: {field}'
                }), 400
        
        # 添加创建时间
        location_data['created_at'] = datetime.now().isoformat()
        
        result = add_location(location_data)
        if result['status']:
            return jsonify({
                'success': True,
                'message': '位置添加成功',
                'data': location_data
            })
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'添加位置失败: {str(e)}'
        }), 500

@system_bp.route('/api/locations/<int:location_id>', methods=['PUT'])
def update_location_api(location_id):
    """更新位置API"""
    try:
        location_data = request.get_json()
        
        # 验证必填字段
        required_fields = ['name', 'address', 'lat', 'lon']
        for field in required_fields:
            if field not in location_data or not location_data[field]:
                return jsonify({
                    'success': False,
                    'message': f'缺少必填字段: {field}'
                }), 400
        
        # 获取现有位置列表
        config = get_json_object('configs/storage.json')
        locations = config.get('locations', [])
        
        # 确保 location_id 是整数类型
        try:
            location_id = int(location_id)
            if 0 <= location_id < len(locations):
                # 保留原始创建时间
                location_data['created_at'] = locations[location_id].get('created_at', datetime.now().isoformat())
                location_data['id'] = location_id
                
                # 更新位置
                locations[location_id] = location_data
                config['locations'] = locations
                save_json_object('configs/storage.json', config)
            else:
                return jsonify({
                    'success': False,
                    'message': '位置ID无效'
                })
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'message': '位置ID格式无效'
            })
        
        return jsonify({
            'success': True,
            'message': '位置更新成功',
            'data': location_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'更新位置失败: {str(e)}'
        }), 500

@system_bp.route('/api/locations/<int:location_id>', methods=['DELETE'])
def delete_location_api(location_id):
    """删除位置API"""
    try:
        result = delete_location(location_id)
        if result['status']:
            return jsonify({
                'success': True,
                'message': result['message']
            })
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除位置失败: {str(e)}'
        }), 500 