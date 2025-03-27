import json
import time
import threading
import schedule
import datetime
from dateutil import parser

from utils.file import get_schedule_tasks, save_schedule_tasks, update_schedule_task
from utils.helper import colored_print
from utils.debug import is_debug_mode, debug_print
from sign_api import sign_by_phone, sign_by_index

# 全局线程对象，用于控制定时任务执行
scheduler_thread = None
stop_scheduler = False

def initialize_scheduler():
    """初始化定时任务调度器"""
    global scheduler_thread, stop_scheduler
    
    # 重置停止标志
    stop_scheduler = False
    
    # 如果已有线程在运行，则不再创建新线程
    if scheduler_thread and scheduler_thread.is_alive():
        return
    
    # 清除已有的任务
    schedule.clear()
    
    # 加载所有任务
    tasks = get_schedule_tasks()
    for task in tasks:
        if task.get('active', True):
            register_task(task)
    
    # 创建并启动线程
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    if is_debug_mode():
        debug_print("定时任务调度器已启动", "green")
    
    colored_print("定时任务调度器已启动", "green")

def run_scheduler():
    """运行定时任务调度器的后台线程"""
    global stop_scheduler
    
    while not stop_scheduler:
        schedule.run_pending()
        time.sleep(1)
    
    if is_debug_mode():
        debug_print("定时任务调度器已停止", "yellow")

def stop_scheduler_thread():
    """停止定时任务调度器"""
    global stop_scheduler
    stop_scheduler = True

def register_task(task):
    """注册一个定时任务到调度器"""
    task_id = task.get('id')
    task_type = task.get('type')
    
    if task_type == 'daily':
        # 每日固定时间执行
        time_str = task.get('time')
        if time_str:
            job = schedule.every().day.at(time_str).do(execute_task, task_id=task_id)
            if is_debug_mode():
                debug_print(f"已注册每日任务，ID: {task_id}, 时间: {time_str}", "blue")
    
    elif task_type == 'weekly':
        # 每周固定时间执行
        time_str = task.get('time')
        days = task.get('days', [])
        
        if time_str and days:
            for day in days:
                if day == 0:  # 周一
                    job = schedule.every().monday.at(time_str).do(execute_task, task_id=task_id)
                elif day == 1:  # 周二
                    job = schedule.every().tuesday.at(time_str).do(execute_task, task_id=task_id)
                elif day == 2:  # 周三
                    job = schedule.every().wednesday.at(time_str).do(execute_task, task_id=task_id)
                elif day == 3:  # 周四
                    job = schedule.every().thursday.at(time_str).do(execute_task, task_id=task_id)
                elif day == 4:  # 周五
                    job = schedule.every().friday.at(time_str).do(execute_task, task_id=task_id)
                elif day == 5:  # 周六
                    job = schedule.every().saturday.at(time_str).do(execute_task, task_id=task_id)
                elif day == 6:  # 周日
                    job = schedule.every().sunday.at(time_str).do(execute_task, task_id=task_id)
            
            if is_debug_mode():
                days_str = ", ".join(["周一", "周二", "周三", "周四", "周五", "周六", "周日"][d] for d in days)
                debug_print(f"已注册每周任务，ID: {task_id}, 时间: {time_str}, 日期: {days_str}", "blue")
    
    elif task_type == 'interval':
        # 间隔执行任务
        interval = task.get('interval', 3600)  # 默认1小时
        unit = task.get('unit', 'seconds')
        
        if unit == 'minutes':
            job = schedule.every(interval).minutes.do(execute_task, task_id=task_id)
        elif unit == 'hours':
            job = schedule.every(interval).hours.do(execute_task, task_id=task_id)
        else:  # seconds
            job = schedule.every(interval).seconds.do(execute_task, task_id=task_id)
        
        if is_debug_mode():
            debug_print(f"已注册间隔任务，ID: {task_id}, 间隔: {interval} {unit}", "blue")

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
        if is_debug_mode():
            debug_print(f"找不到ID为 {task_id} 的任务", "red")
        return
    
    # 检查任务是否激活
    if not task.get('active', True):
        if is_debug_mode():
            debug_print(f"任务 {task_id} 已禁用，跳过执行", "yellow")
        return
    
    # 获取任务信息
    task_name = task.get('name', f'任务{task_id}')
    user_type = task.get('user_type', 'phone')
    user_ids = task.get('user_ids', [])
    
    # 兼容旧版本，如果没有user_ids但有user_id，则转换为列表
    if not user_ids and 'user_id' in task:
        user_ids = [task['user_id']]
    
    # 如果没有用户ID，则记录错误并返回
    if not user_ids:
        if is_debug_mode():
            debug_print(f"任务 {task_name} 没有指定用户ID", "red")
        
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
    
    if is_debug_mode():
        debug_print(f"开始执行任务 {task_name} (ID: {task_id})", "blue")
    
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
            
            if is_debug_mode():
                status_str = "成功" if result.get('status', False) else "失败"
                debug_print(f"用户 {user_id} 执行{status_str}: {result.get('message', '未知结果')}", 
                           "green" if result.get('status', False) else "red")
        
        except Exception as e:
            # 处理单个用户的异常，不影响其他用户
            all_results.append({
                'user_id': user_id,
                'status': False,
                'message': f"执行出错: {str(e)}"
            })
            failed_count += 1
            
            if is_debug_mode():
                debug_print(f"用户 {user_id} 执行出错: {str(e)}", "red")
    
    # 计算总体结果
    total_count = len(user_ids)
    overall_status = success_count > 0
    summary_message = f"总计 {total_count} 个用户，成功 {success_count}，失败 {failed_count}"
    
    # 更新任务的最后执行时间和结果
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    last_run = {
        'time': now,
        'status': overall_status,
        'message': summary_message,
        'details': all_results
    }
    
    task['last_run'] = last_run
    update_schedule_task(task_id, task)
    
    if is_debug_mode():
        debug_print(f"任务 {task_name} 执行完成: {summary_message}", 
                  "green" if overall_status else "yellow")
    
    return {
        'status': overall_status,
        'message': summary_message,
        'results': all_results
    }

def create_task(task_data):
    """创建一个新的定时任务"""
    from utils.file import add_schedule_task
    
    # 添加默认字段
    if 'active' not in task_data:
        task_data['active'] = True
    
    # 添加创建时间
    task_data['created_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 保存到文件
    success = add_schedule_task(task_data)
    
    if success and task_data.get('active', True):
        # 清除现有调度并重新初始化
        schedule.clear()
        initialize_scheduler()
    
    return success

def update_task(task_id, task_data):
    """更新定时任务"""
    success = update_schedule_task(task_id, task_data)
    
    if success:
        # 清除现有调度并重新初始化
        schedule.clear()
        initialize_scheduler()
    
    return success

def delete_task(task_id):
    """删除定时任务"""
    from utils.file import delete_schedule_task
    
    success = delete_schedule_task(task_id)
    
    if success:
        # 清除现有调度并重新初始化
        schedule.clear()
        initialize_scheduler()
    
    return success

def get_task(task_id):
    """获取指定ID的任务"""
    tasks = get_schedule_tasks()
    for task in tasks:
        if task.get('id') == task_id:
            return task
    return None

# 程序启动时自动初始化调度器
# initialize_scheduler() 