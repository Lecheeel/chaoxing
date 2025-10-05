import os
import json
import time
import threading
import datetime
import logging
import traceback
from typing import List, Dict, Any, Optional, Union

from utils.file import get_json_object, save_json_object, get_stored_user
from utils.helper import colored_print, delay
from utils.debug import is_debug_mode, debug_print
from functions.sign import sign_by_phone
from functions.activity import traverse_course_activity, get_ppt_active_info, pre_sign
from functions.general import general_sign, handle_code_sign
from functions.gesture import handle_gesture_sign
from functions.location import location_sign
from functions.user import get_courses

# 全局变量，保存所有运行中的监听线程
monitor_threads = {}
stop_monitor_flag = {}
monitor_lock = threading.RLock()  # 用于线程安全操作

# 监听任务文件路径
MONITOR_TASKS_FILE = 'configs/monitor_tasks.json'


def ensure_monitor_file():
    """确保监听任务文件存在"""
    if not os.path.exists(MONITOR_TASKS_FILE):
        # 创建目录（如果不存在）
        os.makedirs(os.path.dirname(MONITOR_TASKS_FILE), exist_ok=True)
        
        # 创建初始文件
        save_json_object(MONITOR_TASKS_FILE, {"tasks": [], "next_id": 1})
        
        colored_print(f"已创建监听任务文件: {MONITOR_TASKS_FILE}", "green")


def setup_monitor_logging():
    """配置监听日志"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    logger = logging.getLogger('monitor')
    # 从环境变量获取日志级别
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # 防止重复添加处理器
    if not logger.handlers:
        # 文件处理器
        file_handler = logging.FileHandler('logs/monitor.log', encoding='utf-8')
        file_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(file_format)
        logger.addHandler(console_handler)
    
    return logger


# 获取监听日志记录器
monitor_logger = setup_monitor_logging()


def log_monitor_event(message, level='info'):
    """记录监听事件"""
    getattr(monitor_logger, level)(message)
    if is_debug_mode():
        debug_print(message, "blue" if level == 'info' else "red")
    colored_print(message, "cyan" if level == 'info' else "red")


def get_monitor_tasks() -> List[Dict[str, Any]]:
    """获取所有监听任务"""
    ensure_monitor_file()
    monitor_data = get_json_object(MONITOR_TASKS_FILE)
    return monitor_data.get('tasks', [])


def get_monitor_task(task_id: int) -> Optional[Dict[str, Any]]:
    """获取指定ID的监听任务"""
    tasks = get_monitor_tasks()
    for task in tasks:
        if task.get('id') == task_id:
            return task
    return None


def save_monitor_tasks(tasks: List[Dict[str, Any]]) -> bool:
    """保存监听任务列表"""
    ensure_monitor_file()
    try:
        monitor_data = get_json_object(MONITOR_TASKS_FILE)
        monitor_data['tasks'] = tasks
        save_json_object(MONITOR_TASKS_FILE, monitor_data)
        return True
    except Exception as e:
        log_monitor_event(f"保存监听任务失败: {str(e)}", 'error')
        return False


def get_next_task_id() -> int:
    """获取下一个可用的任务ID"""
    ensure_monitor_file()
    monitor_data = get_json_object(MONITOR_TASKS_FILE)
    next_id = monitor_data.get('next_id', 1)
    
    # 更新next_id
    monitor_data['next_id'] = next_id + 1
    save_json_object(MONITOR_TASKS_FILE, monitor_data)
    
    return next_id


def create_monitor_task(phone: str, course_ids: Optional[List[str]] = None, interval: int = 30, delay_range: Optional[List[int]] = None) -> int:
    """创建新的监听任务
    
    参数:
        phone: 用户手机号
        course_ids: 要监听的课程ID列表，如果为None或空列表则监听所有课程
        interval: 检查间隔（秒）
        delay_range: 发现签到后延迟时间范围[最小值,最大值]，单位为秒，如[30,120]表示延迟30-120秒，None表示不延迟
    """
    with monitor_lock:
        task_id = get_next_task_id()
        
        # 创建任务对象
        new_task = {
            'id': task_id,
            'phone': phone,
            'course_ids': course_ids if course_ids else [],  # 空列表表示监听所有课程
            'interval': interval,
            'active': True,
            'created_at': datetime.datetime.now().isoformat(),
            'last_check': None,
            'last_sign': None,
            'monitor_all': course_ids is None or len(course_ids) == 0,  # 标记是否监听所有课程
            'delay_range': delay_range  # 添加延迟时间范围
        }
        
        # 保存到任务列表
        tasks = get_monitor_tasks()
        tasks.append(new_task)
        save_monitor_tasks(tasks)
        
        # 启动监听线程
        start_monitor_thread(task_id)
        
        if new_task['monitor_all']:
            log_monitor_event(f"已创建监听任务 ID: {task_id}, 用户: {phone}, 监听所有课程")
        else:
            log_monitor_event(f"已创建监听任务 ID: {task_id}, 用户: {phone}, 课程数: {len(course_ids)}")
        
        # 如果设置了延迟，记录日志
        if delay_range:
            log_monitor_event(f"任务 ID: {task_id} 设置了延迟签到: {delay_range[0]}-{delay_range[1]}秒")
            
        return task_id


def update_monitor_task(task_id: int, phone: str, course_ids: Optional[List[str]] = None, interval: int = 30, active: bool = True, delay_range: Optional[List[int]] = None) -> bool:
    """更新监听任务"""
    with monitor_lock:
        tasks = get_monitor_tasks()
        updated = False
        
        for i, task in enumerate(tasks):
            if task.get('id') == task_id:
                # 先停止旧的监听线程
                stop_monitor_thread(task_id)
                
                # 更新任务
                tasks[i]['phone'] = phone
                tasks[i]['course_ids'] = course_ids if course_ids else []
                tasks[i]['interval'] = interval
                tasks[i]['active'] = active
                tasks[i]['updated_at'] = datetime.datetime.now().isoformat()
                tasks[i]['monitor_all'] = course_ids is None or len(course_ids) == 0
                
                # 更新延迟时间范围
                if delay_range is not None:
                    tasks[i]['delay_range'] = delay_range
                
                updated = True
                break
        
        if updated:
            # 保存更新
            save_monitor_tasks(tasks)
            
            # 如果任务是激活状态，启动监听线程
            if active:
                start_monitor_thread(task_id)
            
            log_monitor_event(f"已更新监听任务 ID: {task_id}, 状态: {'激活' if active else '停用'}")
            
            # 如果设置了延迟，记录日志
            if delay_range is not None:
                log_monitor_event(f"任务 ID: {task_id} 更新了延迟签到: {delay_range[0]}-{delay_range[1]}秒")
            
            return True
        else:
            log_monitor_event(f"更新失败，未找到任务 ID: {task_id}", 'error')
            return False


def delete_monitor_task(task_id: int) -> bool:
    """删除监听任务"""
    with monitor_lock:
        # 先停止监听线程
        stop_monitor_thread(task_id)
        
        tasks = get_monitor_tasks()
        initial_count = len(tasks)
        
        # 过滤掉要删除的任务
        tasks = [task for task in tasks if task.get('id') != task_id]
        
        if len(tasks) < initial_count:
            # 获取完整的monitor_data以便更新next_id
            monitor_data = get_json_object(MONITOR_TASKS_FILE)
            monitor_data['tasks'] = tasks
            
            # 如果删除后没有任务了，重置next_id为1
            if len(tasks) == 0:
                monitor_data['next_id'] = 1
                log_monitor_event(f"已删除所有任务，ID计数器已重置")
            
            # 保存更新后的数据
            save_json_object(MONITOR_TASKS_FILE, monitor_data)
            log_monitor_event(f"已删除监听任务 ID: {task_id}")
            return True
        else:
            log_monitor_event(f"删除失败，未找到任务 ID: {task_id}", 'error')
            return False


def toggle_monitor_task(task_id: int, active: bool) -> bool:
    """切换监听任务状态"""
    with monitor_lock:
        tasks = get_monitor_tasks()
        toggled = False
        
        for i, task in enumerate(tasks):
            if task.get('id') == task_id:
                # 如果状态没变，直接返回
                if task.get('active') == active:
                    return True
                
                # 更新状态
                tasks[i]['active'] = active
                tasks[i]['updated_at'] = datetime.datetime.now().isoformat()
                
                toggled = True
                break
        
        if toggled:
            # 保存更新
            save_monitor_tasks(tasks)
            
            # 根据新状态启动或停止线程
            if active:
                start_monitor_thread(task_id)
            else:
                stop_monitor_thread(task_id)
            
            log_monitor_event(f"已切换监听任务 ID: {task_id} 状态为: {'激活' if active else '停用'}")
            return True
        else:
            log_monitor_event(f"切换状态失败，未找到任务 ID: {task_id}", 'error')
            return False


def handle_sign_activity(user_info: Dict[str, Any], activity: Dict[str, Any], delay_seconds: int = 0) -> bool:
    """处理签到活动
    
    参数:
        user_info: 用户信息
        activity: 签到活动信息
        delay_seconds: 延迟签到的秒数
        
    返回:
        bool: 签到是否成功
    """
    try:
        phone = user_info.get('phone', '')
        params = user_info.get('params', {})
        name = params.get('name', '用户')
        
        # 如果设置了延迟，先等待指定时间
        if delay_seconds > 0:
            log_monitor_event(f"发现签到活动，将等待 {delay_seconds} 秒后进行签到")
            time.sleep(delay_seconds)
        
        # 合并参数
        sign_params = {**params, 'phone': phone}
        
        # 预签到
        pre_sign({**activity, **sign_params})
        
        # 根据签到类型处理
        other_id = activity.get('otherId')
        active_id = activity.get('activeId')
        
        if other_id == 2:
            # 二维码签到
            log_monitor_event(f"发现二维码签到，无法自动处理。用户: {phone}, 课程: {activity.get('courseId')}", 'info')
            return False
            
        elif other_id == 4:
            # 位置签到
            log_monitor_event(f"发现位置签到，尝试自动签到。用户: {phone}", 'info')
            
            # 获取用户位置信息
            location_info = user_info.get('monitor', {})
            
            # 预设位置列表
            preset_addresses = location_info.get('presetAddress', [])
            if not preset_addresses:
                # 如果没有预设位置列表，使用单个位置
                address_info = {
                    'lon': location_info.get('lon', '116.333585'),
                    'lat': location_info.get('lat', '40.008944'),
                    'address': location_info.get('address', '北京市海淀区双清路清华大学')
                }
                
                # 位置签到
                result = location_sign({
                    **sign_params,
                    **address_info,
                    'activeId': active_id,
                    'name': name,
                    'fid': params.get('fid', '-1')
                })
                
                success = '[位置]签到成功' in result
                log_monitor_event(f"位置签到结果: {result}", 'info' if success else 'error')
                return success
            else:
                # 如果有预设位置列表，尝试每个位置直到成功
                for i, address_item in enumerate(preset_addresses):
                    log_monitor_event(f"尝试位置 {i+1}/{len(preset_addresses)}: {address_item.get('address', '未知地址')}", 'info')
                    
                    result = location_sign({
                        **sign_params,
                        'lon': address_item.get('lon'),
                        'lat': address_item.get('lat'),
                        'address': address_item.get('address'),
                        'activeId': active_id,
                        'name': name,
                        'fid': params.get('fid', '-1')
                    })
                    
                    if '[位置]签到成功' in result:
                        log_monitor_event(f"位置签到成功", 'info')
                        return True
                    
                    # 避免请求过于频繁
                    time.sleep(1)
                
                log_monitor_event(f"所有预设位置均签到失败", 'error')
                return False
            
        elif other_id == 3:
            # 手势签到
            log_monitor_event(f"发现手势签到，尝试自动签到。用户: {phone}", 'info')
            
            # 预设常用手势模式
            gesture_patterns = {
                "L": "14789",
                "反L": "36987",
                "Z": "1235789",
                "反Z": "3215987",
                "2587": "2587",
                "2589": "2589",
                "8521": "8521",
                "8523": "8523"
            }
            
            # 自动尝试预设手势
            for pattern_name, pattern_code in gesture_patterns.items():
                log_monitor_event(f"尝试手势: '{pattern_name}' ({pattern_code})", 'info')
                
                result = handle_gesture_sign({
                    **sign_params, 
                    'signCode': pattern_code, 
                    'activeId': active_id
                }, activity, name)
                
                if "签到成功" in result:
                    log_monitor_event(f"手势签到成功! 图案: {pattern_name}", 'info')
                    return True
                
                # 防止请求过于频繁
                time.sleep(0.5)
                
            log_monitor_event(f"手势签到失败，所有预设手势均不匹配", 'error')
            return False
            
        elif other_id == 5:
            # 签到码签到 - 无法自动处理，需要手动输入签到码
            log_monitor_event(f"发现签到码签到，无法自动处理。用户: {phone}", 'info')
            return False
            
        elif other_id == 0:
            # 普通签到或拍照签到
            photo = get_ppt_active_info(active_id, **sign_params)
            
            if photo.get('ifphoto') == 1:
                # 拍照签到
                log_monitor_event(f"发现拍照签到，无法自动处理。用户: {phone}", 'info')
                return False
            else:
                # 普通签到
                log_monitor_event(f"发现普通签到，自动处理中。用户: {phone}", 'info')
                result = general_sign({
                    **sign_params,
                    'activeId': active_id,
                    'name': name,
                    'fid': params.get('fid', '-1')
                })
                
                success = '签到成功' in result
                log_monitor_event(f"普通签到结果: {result}", 'info' if success else 'error')
                return success
                
        return False
        
    except Exception as e:
        log_monitor_event(f"处理签到活动时出错: {str(e)}", 'error')
        log_monitor_event(traceback.format_exc(), 'error')
        return False


def check_for_sign_activity(phone: str, course_id: str) -> bool:
    """检查指定课程是否有签到活动
    
    参数:
        phone: 用户手机号
        course_id: 课程ID
        
    返回:
        bool: 是否有签到活动
    """
    try:
        # 获取用户信息
        user_info = get_stored_user(phone)
        if not user_info:
            log_monitor_event(f"未找到用户 {phone} 的信息", 'error')
            return False
            
        # 获取用户参数
        params = user_info.get('params', {})
        
        # 创建一个只包含指定课程的列表
        single_course = [{
            'courseId': course_id,
            'classId': course_id  # 假设classId与courseId相同，实际情况可能需要调整
        }]
        
        # 使用traverse_course_activity检查指定课程
        activity = traverse_course_activity({'courses': single_course, **params})
        
        # 如果返回的不是字符串，说明找到了签到活动
        return not isinstance(activity, str)
        
    except Exception as e:
        log_monitor_event(f"检查课程 {course_id} 签到活动时出错: {str(e)}", 'error')
        log_monitor_event(traceback.format_exc(), 'error')
        return False


def run_monitor_thread(task_id: int):
    """运行监听线程的主函数"""
    global stop_monitor_flag
    
    try:
        while not stop_monitor_flag.get(task_id, False):
            # 获取最新的任务信息
            task = get_monitor_task(task_id)
            if not task or not task.get('active', False):
                log_monitor_event(f"任务 {task_id} 已不再活跃，停止监听线程")
                break
            
            phone = task.get('phone')
            monitor_all = task.get('monitor_all', False)
            course_ids = task.get('course_ids', [])
            interval = task.get('interval', 30)
            delay_range = task.get('delay_range', None)
            
            # 获取用户信息
            user_info = get_stored_user(phone)
            if not user_info:
                log_monitor_event(f"未找到用户 {phone} 的信息，跳过检查", 'error')
                time.sleep(interval)
                continue
            
            params = user_info.get('params', {})
            
            # 更新最后检查时间
            update_last_check_time(task_id)
            
            try:
                if monitor_all:
                    # 监听所有课程
                    log_monitor_event(f"检查任务 ID: {task_id}, 用户: {phone}, 监听所有课程")
                    
                    # 获取所有课程
                    courses = get_courses(params.get('_uid'), params.get('_d'), params.get('vc3'))
                    if isinstance(courses, str):
                        log_monitor_event(f"获取课程列表失败: {courses}", 'error')
                        time.sleep(interval)
                        continue
                    
                    # 遍历课程查找签到活动
                    activity = traverse_course_activity({'courses': courses, **params})
                    if isinstance(activity, str):
                        # 没有找到签到活动
                        log_monitor_event(f"未发现签到活动", 'info')
                        time.sleep(interval)
                        continue
                    
                    # 发现签到活动，进行处理
                    log_monitor_event(f"发现签到活动! 用户: {phone}, 课程: {activity.get('courseId')}", 'info')
                    
                    # 计算延迟签到时间
                    delay_seconds = 0
                    if delay_range and len(delay_range) == 2:
                        min_delay, max_delay = delay_range
                        if min_delay == max_delay:
                            delay_seconds = min_delay
                        else:
                            import random
                            delay_seconds = random.randint(min_delay, max_delay)
                    
                    # 处理签到
                    success = handle_sign_activity(user_info, activity, delay_seconds)
                    
                    # 更新最后签到时间
                    if success:
                        update_last_sign_time(task_id)
                    
                else:
                    # 监听指定课程
                    log_monitor_event(f"检查任务 ID: {task_id}, 用户: {phone}, 课程数: {len(course_ids)}")
                    
                    # 检查每个课程
                    for course_id in course_ids:
                        if stop_monitor_flag.get(task_id, False):
                            break
                        
                        try:
                            # 检查是否有签到活动
                            has_activity = check_for_sign_activity(phone, course_id)
                            
                            if has_activity:
                                log_monitor_event(f"发现签到活动! 用户: {phone}, 课程: {course_id}", 'info')
                                
                                # 计算延迟签到时间
                                delay_seconds = 0
                                if delay_range and len(delay_range) == 2:
                                    min_delay, max_delay = delay_range
                                    if min_delay == max_delay:
                                        delay_seconds = min_delay
                                    else:
                                        import random
                                        delay_seconds = random.randint(min_delay, max_delay)
                                
                                # 如果设置了延迟，先等待
                                if delay_seconds > 0:
                                    log_monitor_event(f"将等待 {delay_seconds} 秒后进行签到")
                                    time.sleep(delay_seconds)
                                
                                # 执行签到
                                success = sign_by_phone(phone, {
                                    'course_id': course_id,
                                    'auto_position': True  # 自动使用用户已保存的位置
                                })
                                
                                if success:
                                    log_monitor_event(f"自动签到成功! 用户: {phone}, 课程: {course_id}", 'info')
                                    
                                    # 更新最后签到时间
                                    update_last_sign_time(task_id)
                                else:
                                    log_monitor_event(f"自动签到失败! 用户: {phone}, 课程: {course_id}", 'error')
                            
                        except Exception as e:
                            log_monitor_event(f"检查课程 {course_id} 时出错: {str(e)}", 'error')
            
            except Exception as e:
                log_monitor_event(f"监听任务执行时出错: {str(e)}", 'error')
                log_monitor_event(traceback.format_exc(), 'error')
            
            # 睡眠指定间隔
            for _ in range(interval):
                if stop_monitor_flag.get(task_id, False):
                    break
                time.sleep(1)
        
        log_monitor_event(f"监听线程 ID: {task_id} 已停止")
    except Exception as e:
        log_monitor_event(f"监听线程 ID: {task_id} 发生异常: {str(e)}", 'error')
        log_monitor_event(traceback.format_exc(), 'error')
    finally:
        # 确保线程结束时清理资源
        with monitor_lock:
            if task_id in monitor_threads and not stop_monitor_flag.get(task_id, False):
                stop_monitor_flag[task_id] = True
                if task_id in monitor_threads:
                    del monitor_threads[task_id]


def start_monitor_thread(task_id: int) -> bool:
    """启动监听线程"""
    with monitor_lock:
        task = get_monitor_task(task_id)
        if not task:
            log_monitor_event(f"启动监听线程失败，未找到任务 ID: {task_id}", 'error')
            return False
        
        if not task.get('active', False):
            log_monitor_event(f"任务 ID: {task_id} 未激活，不启动监听线程")
            return False
        
        # 如果已有线程在运行，先停止
        stop_monitor_thread(task_id)
        
        # 重置停止标志
        stop_monitor_flag[task_id] = False
        
        # 创建新线程
        thread = threading.Thread(
            target=run_monitor_thread,
            args=(task_id,),
            name=f"monitor-{task_id}"
        )
        thread.daemon = True
        thread.start()
        
        # 保存线程对象
        monitor_threads[task_id] = thread
        
        log_monitor_event(f"已启动监听线程 ID: {task_id}, 用户: {task.get('phone')}, 间隔: {task.get('interval')}秒")
        return True


def stop_monitor_thread(task_id: int) -> bool:
    """停止监听线程"""
    with monitor_lock:
        if task_id in monitor_threads:
            # 设置停止标志
            stop_monitor_flag[task_id] = True
            
            # 给线程一点时间停止
            thread = monitor_threads[task_id]
            if thread.is_alive():
                thread.join(0.5)  # 等待最多0.5秒
            
            # 从线程字典中移除
            del monitor_threads[task_id]
            log_monitor_event(f"已停止监听线程 ID: {task_id}")
            return True
        else:
            log_monitor_event(f"没有找到运行中的监听线程 ID: {task_id}")
            return False


def update_last_check_time(task_id: int) -> bool:
    """更新任务的最后检查时间"""
    tasks = get_monitor_tasks()
    updated = False
    
    for i, task in enumerate(tasks):
        if task.get('id') == task_id:
            tasks[i]['last_check'] = datetime.datetime.now().isoformat()
            updated = True
            break
    
    if updated:
        save_monitor_tasks(tasks)
        return True
    return False


def update_last_sign_time(task_id: int) -> bool:
    """更新任务的最后签到时间"""
    tasks = get_monitor_tasks()
    updated = False
    
    for i, task in enumerate(tasks):
        if task.get('id') == task_id:
            tasks[i]['last_sign'] = datetime.datetime.now().isoformat()
            updated = True
            break
    
    if updated:
        save_monitor_tasks(tasks)
        return True
    return False


def initialize_monitor():
    """初始化监听模块，启动所有激活的监听任务"""
    ensure_monitor_file()
    tasks = get_monitor_tasks()
    
    active_count = 0
    for task in tasks:
        if task.get('active', False):
            if start_monitor_thread(task.get('id')):
                active_count += 1
    
    log_monitor_event(f"监听模块初始化完成，已启动 {active_count} 个监听任务")
    return active_count


def stop_all_monitors():
    """停止所有监听任务"""
    with monitor_lock:
        task_ids = list(monitor_threads.keys())
        
        for task_id in task_ids:
            stop_monitor_thread(task_id)
        
        log_monitor_event(f"已停止所有监听任务，共 {len(task_ids)} 个")
        return len(task_ids)


# 在模块加载时自动初始化
# initialize_monitor() 