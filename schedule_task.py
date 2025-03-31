import time
import threading
import schedule
import datetime
import logging
import traceback
import os
from dateutil import parser

from utils.file import get_schedule_tasks, save_schedule_tasks, update_schedule_task
from utils.helper import colored_print
from utils.debug import is_debug_mode, debug_print
from sign_api import sign_by_phone, sign_by_index

# 全局线程对象，用于控制定时任务执行
scheduler_thread = None
stop_scheduler = False
scheduler_lock = threading.RLock()  # 用于线程安全操作
max_consecutive_errors = 5  # 最大连续错误次数
consecutive_errors = 0  # 当前连续错误次数
scheduler_healthy = True  # 调度器健康状态

# 确保日志目录存在
def ensure_log_dir():
    if not os.path.exists('logs'):
        os.makedirs('logs')

# 配置日志
def setup_scheduler_logging():
    ensure_log_dir()
    
    logger = logging.getLogger('scheduler')
    logger.setLevel(logging.INFO)
    
    # 防止重复添加处理器
    if not logger.handlers:
        # 文件处理器
        file_handler = logging.FileHandler('logs/scheduler.log', encoding='utf-8')
        file_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(file_format)
        logger.addHandler(console_handler)
    
    return logger

# 获取调度器日志记录器
scheduler_logger = setup_scheduler_logging()

def log_scheduler_event(message, level='info'):
    """记录调度器事件"""
    getattr(scheduler_logger, level)(message)
    if is_debug_mode():
        debug_print(message, "blue" if level == 'info' else "red")
    colored_print(message, "green" if level == 'info' else "red")

def initialize_scheduler():
    """初始化定时任务调度器"""
    global scheduler_thread, stop_scheduler, consecutive_errors, scheduler_healthy
    
    with scheduler_lock:
        # 重置停止标志和错误计数
        stop_scheduler = False
        consecutive_errors = 0
        scheduler_healthy = True
        
        # 如果已有线程在运行，则不再创建新线程
        if scheduler_thread and scheduler_thread.is_alive():
            log_scheduler_event("调度器已在运行，跳过初始化")
            return
        
        # 清除已有的任务
        schedule.clear()
        
        try:
            # 加载所有任务
            tasks = get_schedule_tasks()
            task_count = 0
            
            for task in tasks:
                if task.get('active', True):
                    register_task(task)
                    task_count += 1
            
            # 创建并启动线程
            scheduler_thread = threading.Thread(target=run_scheduler)
            scheduler_thread.daemon = True
            scheduler_thread.start()
            
            log_scheduler_event(f"定时任务调度器已启动，已加载 {task_count} 个活动任务")
        except Exception as e:
            error_msg = f"初始化调度器失败: {str(e)}"
            log_scheduler_event(error_msg, 'error')
            log_scheduler_event(traceback.format_exc(), 'error')
            scheduler_healthy = False
            raise

def run_scheduler():
    """运行定时任务调度器的后台线程"""
    global stop_scheduler, consecutive_errors, scheduler_healthy
    
    log_scheduler_event("调度器线程已启动")
    
    while not stop_scheduler:
        try:
            schedule.run_pending()
            # 成功执行一次后重置错误计数
            if consecutive_errors > 0:
                log_scheduler_event(f"调度器恢复正常运行，重置错误计数")
                consecutive_errors = 0
                scheduler_healthy = True
                
            time.sleep(1)
        except Exception as e:
            consecutive_errors += 1
            error_msg = f"调度器运行异常 ({consecutive_errors}/{max_consecutive_errors}): {str(e)}"
            log_scheduler_event(error_msg, 'error')
            
            if consecutive_errors >= max_consecutive_errors:
                log_scheduler_event("连续错误次数过多，标记调度器为不健康状态", 'error')
                scheduler_healthy = False
                
                # 尝试重新初始化调度器
                try:
                    log_scheduler_event("尝试重置调度器...", 'warning')
                    schedule.clear()
                    tasks = get_schedule_tasks()
                    for task in tasks:
                        if task.get('active', True):
                            register_task(task)
                    consecutive_errors = 0
                    scheduler_healthy = True
                    log_scheduler_event("调度器已成功重置", 'info')
                except Exception as reset_error:
                    log_scheduler_event(f"重置调度器失败: {str(reset_error)}", 'error')
            
            # 短暂暂停后继续
            time.sleep(5)
    
    log_scheduler_event("定时任务调度器已停止", 'warning')

def stop_scheduler_thread():
    """停止定时任务调度器"""
    global stop_scheduler
    with scheduler_lock:
        stop_scheduler = True
        log_scheduler_event("已发送停止信号给调度器线程")

def get_scheduler_status():
    """获取调度器当前状态"""
    global scheduler_thread, scheduler_healthy
    
    with scheduler_lock:
        is_running = scheduler_thread is not None and scheduler_thread.is_alive()
        
        return {
            "running": is_running,
            "healthy": scheduler_healthy,
            "error_count": consecutive_errors,
            "tasks_count": len(schedule.jobs)
        }

def register_task(task):
    """注册一个定时任务到调度器"""
    task_id = task.get('id')
    task_type = task.get('type')
    task_name = task.get('name', f'任务{task_id}')
    
    try:
        if task_type == 'daily':
            # 每日固定时间执行
            time_str = task.get('time')
            if time_str:
                job = schedule.every().day.at(time_str).do(execute_task, task_id=task_id)
                log_scheduler_event(f"已注册每日任务: {task_name} (ID: {task_id}), 时间: {time_str}")
        
        elif task_type == 'weekly':
            # 每周固定时间执行
            time_str = task.get('time')
            days = task.get('days', [])
            
            if time_str and days:
                days_names = []
                for day in days:
                    if day == 0:  # 周一
                        schedule.every().monday.at(time_str).do(execute_task, task_id=task_id)
                        days_names.append("周一")
                    elif day == 1:  # 周二
                        schedule.every().tuesday.at(time_str).do(execute_task, task_id=task_id)
                        days_names.append("周二")
                    elif day == 2:  # 周三
                        schedule.every().wednesday.at(time_str).do(execute_task, task_id=task_id)
                        days_names.append("周三")
                    elif day == 3:  # 周四
                        schedule.every().thursday.at(time_str).do(execute_task, task_id=task_id)
                        days_names.append("周四")
                    elif day == 4:  # 周五
                        schedule.every().friday.at(time_str).do(execute_task, task_id=task_id)
                        days_names.append("周五")
                    elif day == 5:  # 周六
                        schedule.every().saturday.at(time_str).do(execute_task, task_id=task_id)
                        days_names.append("周六")
                    elif day == 6:  # 周日
                        schedule.every().sunday.at(time_str).do(execute_task, task_id=task_id)
                        days_names.append("周日")
                
                days_str = ", ".join(days_names)
                log_scheduler_event(f"已注册每周任务: {task_name} (ID: {task_id}), 时间: {time_str}, 日期: {days_str}")
        
        elif task_type == 'interval':
            # 间隔执行任务
            interval = task.get('interval', 3600)  # 默认1小时
            unit = task.get('unit', 'seconds')
            
            if unit == 'minutes':
                job = schedule.every(interval).minutes.do(execute_task, task_id=task_id)
                unit_str = "分钟"
            elif unit == 'hours':
                job = schedule.every(interval).hours.do(execute_task, task_id=task_id)
                unit_str = "小时"
            else:  # seconds
                job = schedule.every(interval).seconds.do(execute_task, task_id=task_id)
                unit_str = "秒"
            
            log_scheduler_event(f"已注册间隔任务: {task_name} (ID: {task_id}), 间隔: {interval} {unit_str}")
    except Exception as e:
        error_msg = f"注册任务 {task_name} (ID: {task_id}) 失败: {str(e)}"
        log_scheduler_event(error_msg, 'error')
        log_scheduler_event(traceback.format_exc(), 'error')

def execute_task(task_id):
    """执行指定ID的定时任务"""
    tasks = get_schedule_tasks()
    task = None
    
    # 查找任务
    for t in tasks:
        if t.get('id') == task_id:
            task = t
            break
    
    if not task:
        log_scheduler_event(f"找不到ID为 {task_id} 的任务", 'error')
        return {"status": False, "message": f"找不到任务 ID: {task_id}"}
    
    # 检查任务是否激活
    if not task.get('active', True):
        log_scheduler_event(f"任务 {task_id} 已禁用，跳过执行", 'warning')
        return {"status": False, "message": "任务已禁用"}
    
    # 获取任务信息
    task_name = task.get('name', f'任务{task_id}')
    user_type = task.get('user_type', 'phone')
    user_ids = task.get('user_ids', [])
    
    # 兼容旧版本，如果没有user_ids但有user_id，则转换为列表
    if not user_ids and 'user_id' in task:
        user_ids = [task['user_id']]
    
    # 如果没有用户ID，则记录错误并返回
    if not user_ids:
        error_msg = f"任务 {task_name} 没有指定用户ID"
        log_scheduler_event(error_msg, 'error')
        
        # 更新任务的最后执行时间和结果
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        last_run = {
            'time': now,
            'status': False,
            'message': "没有指定用户ID"
        }
        
        task['last_run'] = last_run
        update_schedule_task(task_id, task)
        
        return {
            'status': False,
            'message': "没有指定用户ID"
        }
    
    # 位置信息设置
    location_preset_item = task.get('location_preset_item')
    location_random_offset = task.get('location_random_offset', True)
    
    # 自定义位置参数
    location_address = task.get('location_address')
    location_lon = task.get('location_lon')
    location_lat = task.get('location_lat')
    
    # 构建位置信息参数
    location_info = None
    if location_address and location_lon is not None and location_lat is not None:
        location_info = {
            'address': location_address,
            'lon': location_lon,
            'lat': location_lat
        }
    
    log_scheduler_event(f"开始执行任务 {task_name} (ID: {task_id})")
    
    # 存储所有执行结果
    all_results = []
    success_count = 0
    failed_count = 0
    
    # 依次为每个用户执行签到
    for user_id in user_ids:
        try:
            if user_type == 'phone':
                if location_info:
                    # 使用自定义位置参数
                    result = sign_by_phone(
                        user_id,
                        location_address_info=location_info,
                        location_random_offset=location_random_offset
                    )
                else:
                    # 使用预设位置
                    result = sign_by_phone(
                        user_id,
                        location_preset_item=location_preset_item,
                        location_random_offset=location_random_offset
                    )
            else:  # index
                if location_info:
                    # 使用自定义位置参数
                    result = sign_by_index(
                        int(user_id),
                        location_address_info=location_info,
                        location_random_offset=location_random_offset
                    )
                else:
                    # 使用预设位置
                    result = sign_by_index(
                        int(user_id),
                        location_preset_item=location_preset_item,
                        location_random_offset=location_random_offset
                    )
            
            # 记录此用户的结果
            all_results.append({
                'user_id': user_id,
                'status': result.get('status', False),
                'message': result.get('message', '未知结果')
            })
            
            # 统计成功失败数
            if result.get('status', False):
                success_count += 1
            else:
                failed_count += 1
            
            status_str = "成功" if result.get('status', False) else "失败"
            log_scheduler_event(
                f"任务 {task_name} 为用户 {user_id} 执行{status_str}: {result.get('message', '未知结果')}",
                'info' if result.get('status', False) else 'warning'
            )
            
        except Exception as e:
            # 处理单个用户的异常，不影响其他用户
            error_msg = f"任务 {task_name} 为用户 {user_id} 执行出错: {str(e)}"
            log_scheduler_event(error_msg, 'error')
            log_scheduler_event(traceback.format_exc(), 'error')
            
            all_results.append({
                'user_id': user_id,
                'status': False,
                'message': f"执行出错: {str(e)}"
            })
            failed_count += 1
    
    # 更新任务的最后执行时间和结果
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 根据结果生成摘要
    if success_count > 0 and failed_count == 0:
        status = True
        message = f"全部成功，共 {success_count} 个用户"
    elif success_count > 0 and failed_count > 0:
        status = True
        message = f"部分成功 ({success_count}/{success_count+failed_count})"
    else:
        status = False
        message = f"全部失败，共 {failed_count} 个用户"
    
    last_run = {
        'time': now,
        'status': status,
        'message': message,
        'details': all_results
    }
    
    task['last_run'] = last_run
    update_schedule_task(task_id, task)
    
    log_scheduler_event(f"任务 {task_name} 执行完成: {message}")
    
    return {
        'status': status,
        'message': message,
        'results': all_results,
        'success_count': success_count,
        'failed_count': failed_count
    }

def create_task(task_data):
    """创建新的定时任务"""
    tasks = get_schedule_tasks()
    
    # 生成新任务ID
    if tasks:
        max_id = max(task.get('id', 0) for task in tasks)
        new_id = max_id + 1
    else:
        new_id = 1
    
    # 设置任务ID
    task_data['id'] = new_id
    
    # 添加创建时间
    task_data['created_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 添加到任务列表
    tasks.append(task_data)
    save_schedule_tasks(tasks)
    
    # 如果任务是激活的，注册到调度器
    if task_data.get('active', True):
        register_task(task_data)
    
    return new_id

def update_task(task_id, task_data):
    """更新定时任务"""
    result = update_schedule_task(task_id, task_data)
    if result:
        # 清除并重新加载所有任务
        schedule.clear()
        tasks = get_schedule_tasks()
        for task in tasks:
            if task.get('active', True):
                register_task(task)
    return result

def delete_task(task_id):
    """删除定时任务"""
    tasks = get_schedule_tasks()
    
    # 查找并删除任务
    found = False
    for i, task in enumerate(tasks):
        if task.get('id') == task_id:
            del tasks[i]
            found = True
            break
    
    if found:
        save_schedule_tasks(tasks)
        
        # 清除并重新加载所有任务
        schedule.clear()
        for task in tasks:
            if task.get('active', True):
                register_task(task)
        
        return True
    
    return False

def get_task(task_id):
    """获取指定ID的任务"""
    tasks = get_schedule_tasks()
    
    for task in tasks:
        if task.get('id') == task_id:
            return task
    
    return None

def restart_scheduler():
    """重启调度器"""
    log_scheduler_event("正在重启调度器...", 'warning')
    
    # 停止当前调度器
    stop_scheduler_thread()
    
    # 等待线程完全停止
    if scheduler_thread and scheduler_thread.is_alive():
        scheduler_thread.join(timeout=5)
    
    # 重新初始化调度器
    initialize_scheduler()
    
    return get_scheduler_status()

# 程序启动时自动初始化调度器
# initialize_scheduler() 