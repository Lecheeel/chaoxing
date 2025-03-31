import threading
import time
import json
import logging
import traceback
from datetime import datetime

# 导入项目的功能模块
from functions.activity import get_ppt_active_info, pre_sign, traverse_course_activity
from functions.general import general_sign
from functions.location import location_sign
from functions.photo import photo_sign, get_object_id_from_cx_pan
from functions.qrcode import qrcode_sign
from functions.user import get_account_info, get_courses
from utils.file import get_json_object, store_user
from utils.helper import colored_print
from utils.request import request_manager, request

# 监控线程字典，键为用户手机号，值为线程对象
monitor_threads = {}
# 监控状态字典，键为用户手机号，值为状态信息
monitor_status = {}

def get_monitor_status():
    """获取所有监控线程的状态"""
    status_list = []
    for phone, status in monitor_status.items():
        status_copy = status.copy()
        status_copy['phone'] = phone
        status_copy['is_running'] = phone in monitor_threads and monitor_threads[phone].is_alive()
        status_list.append(status_copy)
    return status_list

def get_user_monitor_status(phone):
    """获取指定用户的监控状态"""
    if phone in monitor_status:
        status = monitor_status[phone].copy()
        status['is_running'] = phone in monitor_threads and monitor_threads[phone].is_alive()
        return status
    return None

def stop_monitor(phone):
    """停止指定用户的监控线程"""
    if phone in monitor_threads:
        if phone in monitor_status:
            monitor_status[phone]['should_stop'] = True
        
        # 等待线程结束
        if monitor_threads[phone].is_alive():
            monitor_threads[phone].join(3)  # 最多等待3秒
        
        # 从字典中移除
        if not monitor_threads[phone].is_alive():
            monitor_threads.pop(phone, None)
            return True
    
    # 如果线程已经不存在但状态仍然存在，则清理状态
    if phone in monitor_status:
        if not (phone in monitor_threads and monitor_threads[phone].is_alive()):
            # 标记状态为已停止
            monitor_status[phone]['should_stop'] = True
            monitor_status[phone]['status'] = 'stopped'
            # 返回成功
            return True
    
    return False

def stop_all_monitors():
    """停止所有监控线程"""
    phones = list(monitor_threads.keys())
    results = []
    
    for phone in phones:
        result = stop_monitor(phone)
        results.append({
            'phone': phone,
            'stopped': result
        })
    
    return results

def monitor_sign_task(params, configs, name):
    """
    监控签到任务，在单独的线程中运行
    
    Args:
        params: 用户参数，包含认证信息
        configs: 监控配置
        name: 用户名
    """
    phone = params.get('phone')
    
    # 添加额外的参数检查
    if not phone:
        logging.error("[Monitor] monitor_sign_task函数缺少必要参数: phone")
        return
    
    if not params.get('_uid') or not params.get('_d') or not params.get('vc3'):
        logging.error(f"[Monitor] 用户 {name}({phone}) 缺少必要的认证参数")
        return
    
    # 初始化监控状态
    if phone not in monitor_status:
        monitor_status[phone] = {
            'username': name,
            'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'last_check_time': None,
            'last_sign_time': None,
            'sign_count': 0,
            'error_count': 0,
            'last_error': None,
            'should_stop': False,
            'status': 'running'
        }
    else:
        # 重置状态
        monitor_status[phone].update({
            'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'last_check_time': None,
            'last_sign_time': None,
            'sign_count': 0,
            'error_count': 0,
            'last_error': None,
            'should_stop': False,
            'status': 'running'
        })
    
    logging.info(f"[Monitor] 开始为用户 {name}({phone}) 监控签到")
    
    try:
        # 为了确保日志记录成功，单独处理此部分
        auth_info = f"_uid={params.get('_uid')}, _d={params.get('_d')}, vc3={params.get('vc3', '')[:20]}..."
        logging.info(f"[Monitor] 用户 {name}({phone}) 认证信息: {auth_info}")
        
        # 确保request_manager是可用的
        if not request_manager:
            logging.error(f"[Monitor] 用户 {name}({phone}) request_manager不可用")
            monitor_status[phone]['last_error'] = "request_manager不可用"
            monitor_status[phone]['error_count'] += 1
            monitor_status[phone]['status'] = 'stopped'
            return
        
        # 检查位置预设是否正确配置
        if not configs.get('monitor', {}).get('presetAddress'):
            logging.warning(f"[Monitor] 用户 {name}({phone}) 没有配置位置预设，将使用默认位置")
            if 'monitor' not in configs:
                configs['monitor'] = {}
            if 'presetAddress' not in configs['monitor']:
                configs['monitor']['presetAddress'] = [{
                    'lon': '113.516288',
                    'lat': '34.817038',
                    'address': '北京市海淀区双清路清华大学'
                }]
        
        # 设置认证信息
        try:
            logging.info(f"[Monitor] 用户 {name}({phone}) 正在初始化认证信息")
            request_manager.set_auth_cookies(params)
            logging.info(f"[Monitor] 用户 {name}({phone}) 认证信息设置成功")
        except Exception as e:
            logging.error(f"[Monitor] 用户 {name}({phone}) 设置认证信息时发生错误: {str(e)}", exc_info=True)
            monitor_status[phone]['last_error'] = f"设置认证信息失败: {str(e)}"
            monitor_status[phone]['error_count'] += 1
            monitor_status[phone]['status'] = 'stopped'
            return
        
        while not monitor_status[phone]['should_stop']:
            try:
                # 更新最后检查时间
                monitor_status[phone]['last_check_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 设置认证信息
                logging.info(f"[Monitor] 用户 {name}({phone}) 设置认证信息")
                request_manager.set_auth_cookies(params)
                
                # 获取所有课程
                logging.info(f"[Monitor] 用户 {name}({phone}) 正在获取课程")
                
                # 添加重试机制
                max_retries = 3
                retry_delay = 5
                for retry in range(max_retries):
                    try:
                        courses = get_courses(params['_uid'], params['_d'], params['vc3'])
                        if not isinstance(courses, str):
                            break
                        
                        error_msg = f"获取课程失败 (尝试 {retry+1}/{max_retries}): {courses}"
                        logging.error(f"[Monitor] 用户 {name}({phone}) {error_msg}")
                        
                        if retry < max_retries - 1:
                            # 重新设置认证信息后再重试
                            logging.info(f"[Monitor] 用户 {name}({phone}) 重新设置认证信息并等待 {retry_delay} 秒后重试")
                            request_manager.set_auth_cookies(params)
                            time.sleep(retry_delay)
                            retry_delay *= 2  # 指数退避
                    except Exception as e:
                        logging.error(f"[Monitor] 用户 {name}({phone}) 获取课程时发生异常 (尝试 {retry+1}/{max_retries}): {str(e)}")
                        if retry < max_retries - 1:
                            time.sleep(retry_delay)
                            retry_delay *= 2
                
                # 检查是否成功获取课程
                if isinstance(courses, str):
                    error_msg = f"获取课程失败，已达到最大重试次数: {courses}"
                    logging.error(f"[Monitor] 用户 {name}({phone}) {error_msg}")
                    monitor_status[phone]['last_error'] = error_msg
                    monitor_status[phone]['error_count'] += 1
                    time.sleep(60)  # 失败后等待60秒
                    continue
                
                logging.info(f"[Monitor] 用户 {name}({phone}) 获取到 {len(courses)} 门课程")
                
                # 获取进行中的签到活动
                logging.info(f"[Monitor] 用户 {name}({phone}) 正在检查签到活动")
                activity = traverse_course_activity({'courses': courses, **params})
                if isinstance(activity, str):
                    # 没有签到活动，不是错误
                    logging.info(f"[Monitor] 用户 {name}({phone}) 没有进行中的签到活动")
                    time.sleep(10)  # 等待10秒后再次检查
                    continue
                
                # 发现签到活动，延迟指定时间
                logging.info(f"[Monitor] 用户 {name}({phone}) 发现签到活动: {activity}")
                delay_seconds = configs.get('monitor', {}).get('delay', 0)
                if delay_seconds > 0:
                    logging.info(f"[Monitor] 用户 {name}({phone}) 发现签到活动，将在 {delay_seconds} 秒后签到")
                    time.sleep(delay_seconds)
                
                # 预签到
                logging.info(f"[Monitor] 用户 {name}({phone}) 正在进行预签到")
                pre_result = pre_sign({**activity, **params})
                logging.info(f"[Monitor] 用户 {name}({phone}) 预签到结果: {pre_result}")
                
                # 处理签到
                other_id = activity['otherId']
                sign_result = None
                
                if other_id == 2:
                    # 二维码签到，无法自动处理
                    logging.warning(f"[Monitor] 用户 {name}({phone}) 发现二维码签到，无法自动处理")
                    monitor_status[phone]['last_error'] = "发现二维码签到，无法自动处理"
                    monitor_status[phone]['error_count'] += 1
                
                elif other_id == 4:
                    # 位置签到
                    logging.info(f"[Monitor] 用户 {name}({phone}) 发现位置签到，尝试使用预设位置")
                    
                    # 使用预设位置
                    preset_address = configs.get('monitor', {}).get('presetAddress', [])
                    logging.info(f"[Monitor] 用户 {name}({phone}) 位置预设数量: {len(preset_address)}")
                    
                    if not preset_address:
                        logging.warning(f"[Monitor] 用户 {name}({phone}) 没有预设位置，使用默认位置")
                        address_item = {
                            'lon': '113.516288',
                            'lat': '34.817038',
                            'address': '北京市海淀区双清路清华大学'
                        }
                    else:
                        # 使用第一个预设位置
                        address_item = preset_address[0]
                        logging.info(f"[Monitor] 用户 {name}({phone}) 使用位置: {address_item}")
                    
                    # 执行位置签到
                    sign_result = location_sign({
                        **params, 
                        **address_item, 
                        'activeId': activity['activeId'], 
                        'name': name,
                        'fid': params.get('fid', '-1')
                    })
                    logging.info(f"[Monitor] 用户 {name}({phone}) 位置签到结果: {sign_result}")
                    
                    if '[位置]签到成功' in sign_result:
                        monitor_status[phone]['sign_count'] += 1
                        monitor_status[phone]['last_sign_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        time.sleep(10)  # 签到成功后等待10秒
                    else:
                        # 签到失败，尝试其他位置
                        success = False
                        for i in range(1, len(preset_address)):
                            logging.info(f"[Monitor] 用户 {name}({phone}) 尝试使用备用位置 {i}: {preset_address[i]}")
                            sign_result = location_sign({
                                **params, 
                                **preset_address[i], 
                                'activeId': activity['activeId'], 
                                'name': name,
                                'fid': params.get('fid', '-1')
                            })
                            logging.info(f"[Monitor] 用户 {name}({phone}) 备用位置签到结果: {sign_result}")
                            if '[位置]签到成功' in sign_result:
                                monitor_status[phone]['sign_count'] += 1
                                monitor_status[phone]['last_sign_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                success = True
                                break
                        
                        if not success:
                            monitor_status[phone]['last_error'] = f"位置签到失败: {sign_result}"
                            monitor_status[phone]['error_count'] += 1
                
                elif other_id == 3 or other_id == 5:
                    # 手势签到或签到码签到
                    sign_type = "手势" if other_id == 3 else "签到码"
                    logging.info(f"[Monitor] 用户 {name}({phone}) 发现{sign_type}签到")
                    sign_result = general_sign({
                        **params, 
                        'activeId': activity['activeId'], 
                        'name': name,
                        'fid': params.get('fid', '-1')
                    })
                    logging.info(f"[Monitor] 用户 {name}({phone}) {sign_type}签到结果: {sign_result}")
                    
                    if '签到成功' in sign_result:
                        monitor_status[phone]['sign_count'] += 1
                        monitor_status[phone]['last_sign_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        monitor_status[phone]['last_error'] = f"{sign_type}签到失败: {sign_result}"
                        monitor_status[phone]['error_count'] += 1
                
                elif other_id == 0:
                    # 获取签到详情
                    logging.info(f"[Monitor] 用户 {name}({phone}) 正在获取签到详情")
                    photo = get_ppt_active_info(activity['activeId'], **params)
                    logging.info(f"[Monitor] 用户 {name}({phone}) 签到详情: {photo}")
                    
                    if photo.get('ifphoto') == 1:
                        # 拍照签到，无法自动处理
                        logging.warning(f"[Monitor] 用户 {name}({phone}) 发现拍照签到，无法自动处理")
                        monitor_status[phone]['last_error'] = "发现拍照签到，无法自动处理"
                        monitor_status[phone]['error_count'] += 1
                    else:
                        # 普通签到
                        logging.info(f"[Monitor] 用户 {name}({phone}) 发现普通签到")
                        sign_result = general_sign({
                            **params, 
                            'activeId': activity['activeId'], 
                            'name': name,
                            'fid': params.get('fid', '-1')
                        })
                        logging.info(f"[Monitor] 用户 {name}({phone}) 普通签到结果: {sign_result}")
                        
                        if '签到成功' in sign_result:
                            monitor_status[phone]['sign_count'] += 1
                            monitor_status[phone]['last_sign_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            monitor_status[phone]['last_error'] = f"普通签到失败: {sign_result}"
                            monitor_status[phone]['error_count'] += 1
                
                # 记录签到信息
                params_copy = params.copy()
                password = params_copy.pop('password', None)
                phone_num = params_copy.pop('phone', None)
                
                if phone_num:
                    user_data = {
                        'phone': phone_num,
                        'params': params_copy,
                        'monitor': configs.get('monitor', {})
                    }
                    
                    # 保存用户名
                    if name and name != "未知用户":
                        user_data['username'] = name
                    
                    # 保存密码
                    if password:
                        user_data['password'] = password
                    
                    logging.info(f"[Monitor] 用户 {name}({phone}) 保存用户信息")
                    store_user(phone_num, user_data)
            
            except Exception as e:
                logging.error(f"[Monitor] 用户 {name}({phone}) 监控过程发生错误: {str(e)}", exc_info=True)
                monitor_status[phone]['last_error'] = f"监控过程发生错误: {str(e)}"
                monitor_status[phone]['error_count'] += 1
            
            # 默认等待10秒
            time.sleep(10)
    
    except Exception as e:
        logging.error(f"[Monitor] 用户 {name}({phone}) 监控线程发生致命错误: {str(e)}", exc_info=True)
        monitor_status[phone]['last_error'] = f"监控线程发生致命错误: {str(e)}"
        monitor_status[phone]['error_count'] += 1
    
    finally:
        # 更新状态为已停止
        if phone in monitor_status:
            monitor_status[phone]['status'] = 'stopped'
        
        logging.info(f"[Monitor] 用户 {name}({phone}) 监控线程已退出")

def start_monitor(phone, delay=0, location_preset_index=None):
    """
    为指定用户启动监控
    
    Args:
        phone: 用户手机号
        delay: 签到延迟时间（秒）
        location_preset_index: 位置签到使用的预设位置索引
        
    Returns:
        dict: 启动结果
    """
    try:
        # 检查是否已有监控线程在运行
        if phone in monitor_threads and monitor_threads[phone].is_alive():
            logging.info(f"[Monitor] 用户 {phone} 的监控已在运行中")
            return {
                'status': False,
                'message': f'用户 {phone} 的监控已在运行中'
            }
        
        # 获取用户信息
        json_object = get_json_object('configs/storage.json')
        user = None
        
        for u in json_object.get('users', []):
            if u.get('phone') == phone:
                user = u
                break
        
        if not user:
            logging.error(f"[Monitor] 未找到手机号为 {phone} 的用户")
            return {
                'status': False,
                'message': f'未找到手机号为 {phone} 的用户'
            }
        
        # 提取必要参数
        params = {}
        if 'params' in user and isinstance(user['params'], dict):
            params = {**user['params']}
        
        # 检查是否有必要的认证参数
        required_params = ['_uid', '_d', 'vc3']
        missing_params = [p for p in required_params if p not in params or not params[p]]
        
        if missing_params:
            logging.error(f"[Monitor] 用户 {phone} 缺少必要的认证参数: {', '.join(missing_params)}")
            return {
                'status': False,
                'message': f'用户 {phone} 缺少必要的认证参数: {", ".join(missing_params)}'
            }
        
        # 复制非cookie信息
        params['phone'] = user['phone']
        params['password'] = user.get('password', '')
        
        # 获取用户名
        name = user.get('username', '未知用户')
        if not name or name == '未知用户':
            # 尝试获取用户名
            try:
                logging.info(f"[Monitor] 尝试获取用户 {phone} 的用户名")
                name = get_account_info(params) or '未知用户'
                logging.info(f"[Monitor] 为用户 {phone} 获取到用户名: {name}")
            except Exception as e:
                logging.error(f"[Monitor] 获取用户 {phone} 的用户名时发生错误: {str(e)}", exc_info=True)
                name = '未知用户'
        
        # 处理监控配置
        configs = {'monitor': {}}
        
        # 如果用户已有monitor配置，复制它
        if 'monitor' in user:
            configs['monitor'] = user['monitor']
        
        # 确保presetAddress字段存在
        if 'presetAddress' not in configs['monitor']:
            configs['monitor']['presetAddress'] = []
        
        # 如果没有位置预设，添加默认位置
        if not configs['monitor']['presetAddress']:
            logging.info(f"[Monitor] 用户 {phone} 没有位置预设，添加默认位置")
            configs['monitor']['presetAddress'] = [{
                'lon': '113.516288',
                'lat': '34.817038',
                'address': '北京市海淀区双清路清华大学'
            }]
        
        # 设置签到延迟
        configs['monitor']['delay'] = delay
        
        # 处理位置签到的预设位置
        if location_preset_index is not None and 'presetAddress' in configs['monitor']:
            try:
                location_preset_index = int(location_preset_index)
                if 0 <= location_preset_index < len(configs['monitor']['presetAddress']):
                    # 将选定的预设位置设为第一个
                    preset = configs['monitor']['presetAddress'].pop(location_preset_index)
                    configs['monitor']['presetAddress'].insert(0, preset)
                    logging.info(f"[Monitor] 用户 {phone} 将位置预设 {location_preset_index} 设为首选位置: {preset}")
                else:
                    logging.warning(f"[Monitor] 用户 {phone} 位置预设索引 {location_preset_index} 超出范围")
            except (ValueError, TypeError) as e:
                logging.warning(f"[Monitor] 用户 {phone} 提供的位置预设索引无效: {location_preset_index}，错误: {str(e)}")
        
        # 启动监控线程
        logging.info(f"[Monitor] 正在为用户 {name}({phone}) 创建监控线程")
        thread = threading.Thread(
            target=monitor_sign_task,
            args=(params, configs, name),
            daemon=True
        )
        thread.start()
        
        # 记录线程
        monitor_threads[phone] = thread
        
        # 验证线程是否成功启动
        if thread.is_alive():
            logging.info(f"[Monitor] 用户 {name}({phone}) 的监控线程已成功启动")
        else:
            logging.error(f"[Monitor] 用户 {name}({phone}) 的监控线程启动后立即退出")
            return {
                'status': False,
                'message': f'监控线程启动失败，请检查系统日志'
            }
        
        return {
            'status': True,
            'message': f'已为用户 {name}({phone}) 启动监控',
            'detail': {
                'username': name,
                'delay': delay,
                'location_preset_index': location_preset_index
            }
        }
    except Exception as e:
        logging.error(f"[Monitor] 启动用户 {phone} 的监控时发生错误: {str(e)}", exc_info=True)
        return {
            'status': False,
            'message': f'启动监控时发生错误: {str(e)}'
        } 