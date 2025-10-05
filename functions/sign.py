import json
import sys
import traceback
import time
import logging
import os

from functions.activity import get_ppt_active_info, pre_sign, traverse_course_activity, handle_activity_sign
from functions.user import get_account_info, get_courses, get_local_users, user_login
from utils.file import get_json_object, store_user
from utils.helper import colored_print
from utils.debug import is_debug_mode, debug_print
from utils.request import request_manager

# 配置签到日志
def setup_sign_logging():
    """配置签到日志"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    logger = logging.getLogger('sign')
    # 从环境变量获取日志级别
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # 防止重复添加处理器
    if not logger.handlers:
        # 文件处理器
        file_handler = logging.FileHandler('logs/app.log', encoding='utf-8')
        file_format = logging.Formatter('%(asctime)s - %(levelname)s - [签到] %(message)s')
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    
    return logger

# 初始化签到日志记录器
sign_logger = setup_sign_logging()

def sign_by_index(user_index=0, location_preset_item=None, location_address_info=None, location_random_offset=True):
    """
    根据用户索引进行签到
    
    Args:
        user_index: 用户在storage.json中的索引，默认为0
        location_preset_item: 位置签到的预设位置索引，None表示自动选择
        location_address_info: 位置签到的自定义位置信息
        location_random_offset: 位置签到时是否随机偏移坐标，默认为True
        
    Returns:
        dict: 签到结果，包含状态和消息
    """
    try:
        sign_logger.info(f"开始通过索引 {user_index} 进行签到")
        if is_debug_mode():
            debug_print(f"开始通过索引 {user_index} 进行签到", "blue")
            
        # 读取storage.json中的用户信息
        json_object = get_json_object('configs/storage.json')
        
        # 检查用户是否存在
        if 'users' not in json_object or len(json_object['users']) <= user_index:
            error_msg = f'用户索引{user_index}不存在，请确认storage.json中有足够的用户'
            sign_logger.error(error_msg)
            return {
                'status': False,
                'message': error_msg
            }
        
        # 获取用户信息
        user = json_object['users'][user_index]
        params = {}
        
        # 优先从params字段获取认证信息（新版本）
        if 'params' in user and isinstance(user['params'], dict):
            params = {**user['params']}
        # 如果params不存在，则从cookies字段获取（旧版本兼容）
        elif 'cookies' in user and isinstance(user['cookies'], dict):
            params = {**user['cookies']}
        
        # 复制其他非cookie信息
        params['phone'] = user['phone']
        params['password'] = user.get('password', '')
        
        # 确保请求管理器有正确的认证cookie
        request_manager.set_auth_cookies(params)
        
        sign_logger.info(f"成功获取用户信息: 手机号={params['phone']}")
        if is_debug_mode():
            debug_print(f"成功获取用户信息: 手机号={params['phone']}", "green")
        
        # 调用签到功能
        result = execute_sign(params, user.get('monitor', {}), user.get('username', '未知用户'), 
                           location_preset_item, location_address_info, location_random_offset)
        
        # 记录签到结果
        if result.get('status'):
            sign_logger.info(f"签到成功: {result.get('message', '')}")
        else:
            sign_logger.error(f"签到失败: {result.get('message', '')}")
        
        return result
    
    except Exception as e:
        error_message = f'签到过程出错: {e}'
        sign_logger.error(error_message)
        traceback.print_exc()
        return {
            'status': False,
            'message': error_message
        }

def sign_by_phone(phone, location_preset_item=None, location_address_info=None, location_random_offset=True):
    """
    根据手机号进行签到
    
    Args:
        phone: 用户手机号
        location_preset_item: 位置签到的预设位置索引，None表示自动选择
        location_address_info: 位置签到的自定义位置信息
        location_random_offset: 位置签到时是否随机偏移坐标，默认为True
        
    Returns:
        dict: 签到结果，包含状态和消息
    """
    try:
        sign_logger.info(f"开始通过手机号 {phone} 进行签到")
        if is_debug_mode():
            debug_print(f"开始通过手机号 {phone} 进行签到", "blue")
            
        # 读取storage.json中的用户信息
        json_object = get_json_object('configs/storage.json')
        
        # 查找对应手机号的用户
        user = None
        for u in json_object.get('users', []):
            if u.get('phone') == phone:
                user = u
                break
        
        # 检查用户是否存在
        if not user:
            return {
                'status': False,
                'message': f'手机号为{phone}的用户不存在，请确认storage.json中有此用户'
            }
        
        # 获取用户信息
        params = {}
        
        # 优先从params字段获取认证信息（新版本）
        if 'params' in user and isinstance(user['params'], dict):
            params = {**user['params']}
        # 如果params不存在，则从cookies字段获取（旧版本兼容）
        elif 'cookies' in user and isinstance(user['cookies'], dict):
            params = {**user['cookies']}
        
        # 复制其他非cookie信息
        params['phone'] = user['phone']
        params['password'] = user.get('password', '')
        
        # 确保请求管理器有正确的认证cookie
        request_manager.set_auth_cookies(params)
        
        if is_debug_mode():
            debug_print(f"成功获取用户信息: 手机号={params['phone']}", "green")
        
        # 构建用户配置
        user_configs = {}
        
        # 检查用户是否有自己的预设位置
        has_presets = False
        
        # 检查直接存储在presetAddress中的位置
        if 'presetAddress' in user and user['presetAddress']:
            user_configs['presetAddress'] = user['presetAddress']
            has_presets = True
            if is_debug_mode():
                debug_print(f"用户有自己的预设位置(presetAddress), 将使用用户自己的位置信息", "blue")
                debug_print(f"用户预设位置: {user['presetAddress'][0]}", "blue")
        
        # 检查存储在monitor.presetAddress中的位置(旧版本)
        elif 'monitor' in user and 'presetAddress' in user['monitor'] and user['monitor']['presetAddress']:
            user_configs['presetAddress'] = user['monitor']['presetAddress']
            has_presets = True
            if is_debug_mode():
                debug_print(f"用户有自己的预设位置(monitor.presetAddress), 将使用用户自己的位置信息", "blue")
                debug_print(f"用户预设位置: {user['monitor']['presetAddress'][0]}", "blue")
        else:
            # 用户没有预设位置，使用其他monitor配置
            if 'monitor' in user:
                user_configs = user['monitor']
        
        # 调用签到功能
        return execute_sign(params, user_configs, user.get('username', '未知用户'), 
                           location_preset_item, location_address_info, location_random_offset)
    
    except Exception as e:
        error_message = f'签到过程出错: {e}'
        traceback.print_exc()
        return {
            'status': False,
            'message': error_message
        }

def sign_by_login(phone, password, location_preset_item=None, location_address_info=None, location_random_offset=True):
    """
    通过登录进行签到
    
    Args:
        phone: 用户手机号
        password: 用户密码
        location_preset_item: 位置签到的预设位置索引，None表示自动选择
        location_address_info: 位置签到的自定义位置信息
        location_random_offset: 位置签到时是否随机偏移坐标，默认为True
        
    Returns:
        dict: 签到结果，包含状态和消息
    """
    try:
        if is_debug_mode():
            debug_print(f"开始通过登录方式进行签到，手机号: {phone}", "blue")
            
        # 登录获取各参数
        result = user_login(phone, password)
        if isinstance(result, str):
            if is_debug_mode():
                debug_print(f"登录失败: {result}", "red")
            return {
                'status': False,
                'message': f'登录失败: {result}'
            }
        
        if is_debug_mode():
            debug_print("登录成功，正在获取用户信息", "green")
        
        # 获取用户真实姓名
        user_params = {**result, 'phone': phone, 'password': password}
        user_name = get_account_info(user_params)
        
        # 创建用户对象
        user_data = {
            'phone': phone, 
            'password': password,
            'params': result
        }
        
        # 保存用户名
        if user_name and user_name != "未知用户":
            user_data['username'] = user_name
            if is_debug_mode():
                debug_print(f"成功获取用户名: {user_name}", "green")
        else:
            if is_debug_mode():
                debug_print("未能获取有效的用户名", "yellow")
        
        # 保存用户信息
        store_user(phone, user_data)
        if is_debug_mode():
            debug_print(f"用户信息已保存到本地", "green")
        
        # 调用签到功能
        return execute_sign(user_params, {}, user_name, 
                           location_preset_item, location_address_info, location_random_offset)
    
    except Exception as e:
        error_message = f'登录签到过程出错: {e}'
        traceback.print_exc()
        return {
            'status': False,
            'message': error_message
        }

def execute_sign(params, configs, name, location_preset_item=None, location_address_info=None, location_random_offset=True):
    """
    执行签到流程
    
    Args:
        params: 用户参数
        configs: 配置信息
        name: 用户名
        location_preset_item: 位置签到的预设位置索引，None表示自动选择
        location_address_info: 位置签到的自定义位置信息
        location_random_offset: 位置签到时是否随机偏移坐标，默认为True
        
    Returns:
        dict: 签到结果，包含状态和消息
    """
    try:
        sign_logger.info(f"开始执行签到流程，用户: {name}")
        if is_debug_mode():
            debug_print("开始获取课程列表", "blue")
            if location_random_offset:
                debug_print("位置随机偏移功能已开启", "blue")
        
        # 如果指定了位置索引，从全局配置中获取位置信息
        if location_preset_item is not None:
            try:
                from utils.file import get_json_object
                global_config = get_json_object('configs/storage.json')
                locations = global_config.get('locations', [])
                
                if 0 <= location_preset_item < len(locations):
                    location = locations[location_preset_item]
                    # 将位置信息添加到配置中
                    if 'presetAddress' not in configs:
                        configs['presetAddress'] = []
                    
                    # 添加位置信息到预设位置列表
                    configs['presetAddress'].append({
                        'address': location.get('address', ''),
                        'lat': location.get('lat', ''),
                        'lon': location.get('lon', ''),
                        'name': location.get('name', '')
                    })
                    
                    if is_debug_mode():
                        debug_print(f"使用全局位置信息: {location.get('name', '')} - {location.get('address', '')}", "blue")
                else:
                    if is_debug_mode():
                        debug_print(f"位置索引 {location_preset_item} 无效，使用默认配置", "yellow")
            except Exception as e:
                if is_debug_mode():
                    debug_print(f"获取全局位置信息失败: {e}", "yellow")
        
        # 确保请求管理器有正确的认证cookie
        request_manager.set_auth_cookies(params)
        
        # 检查必要的认证参数
        required_params = ['_uid', '_d', 'vc3']
        missing_params = [param for param in required_params if param not in params]
        if missing_params:
            error_message = f"缺少必要的认证参数: {', '.join(missing_params)}"
            if is_debug_mode():
                debug_print(error_message, "red")
                debug_print(f"当前params包含的字段: {list(params.keys())}", "yellow")
            return {
                'status': False,
                'message': error_message
            }
        
        # 获取所有课程
        courses = get_courses(params['_uid'], params['_d'], params['vc3'])
        if isinstance(courses, str):
            error_msg = f'获取课程失败: {courses}'
            sign_logger.error(error_msg)
            if is_debug_mode():
                debug_print(f"获取课程失败: {courses}", "red")
            
            # 记录签到失败统计
            try:
                from utils.stats import record_sign_result
                phone = params.get('phone', '未知用户')
                record_sign_result(
                    user_phone=phone,
                    username=name,
                    success=False,
                    message=f'获取课程失败: {courses}'
                )
            except Exception as stats_e:
                if is_debug_mode():
                    debug_print(f"记录统计信息失败: {stats_e}", "yellow")
            
            return {
                'status': False,
                'message': error_msg
            }
        
        sign_logger.info(f"成功获取课程列表，共 {len(courses)} 门课程")
        if is_debug_mode():
            debug_print(f"成功获取课程列表，共 {len(courses)} 门课程", "green")
            debug_print("开始查找进行中的签到活动", "blue")
        
        # 获取进行中的签到活动
        activity = traverse_course_activity({'courses': courses, **params})
        if isinstance(activity, str):
            if is_debug_mode():
                debug_print(f"未找到进行中的签到活动: {activity}", "yellow")
            
            # 记录签到失败统计
            try:
                from utils.stats import record_sign_result
                phone = params.get('phone', '未知用户')
                # 针对NoActivity提供更友好的消息
                if activity == "NoActivity":
                    message = "未检测到有效签到活动"
                else:
                    message = f'获取签到活动失败: {activity}'
                
                record_sign_result(
                    user_phone=phone,
                    username=name,
                    success=False,
                    message=message
                )
            except Exception as stats_e:
                if is_debug_mode():
                    debug_print(f"记录统计信息失败: {stats_e}", "yellow")
            
            return {
                'status': False,
                'message': f'获取签到活动失败: {activity}'
            }
        
        if is_debug_mode():
            debug_print(f"找到签到活动: ID={activity['activeId']}, 类型={activity['otherId']}", "green")
            debug_print("开始进行签到", "blue")
        
        # 处理签到，根据签到类型自动选择处理方式
        result, updated_configs = handle_activity_sign(
            params, activity, configs, name, 
            location_preset_item, location_address_info, location_random_offset
        )
        
        if is_debug_mode():
            debug_print(f"签到结果: {result}", "green")
            debug_print("开始保存用户信息", "blue")
        
        # 检查签到结果
        if '[位置]不在可签到范围内' in result:
            # 记录签到失败统计
            try:
                from utils.stats import record_sign_result
                record_sign_result(
                    user_phone=phone,
                    username=name,
                    success=False,
                    message='位置不在可签到范围内',
                    activity_info={
                        'activity_id': activity.get('activeId'),
                        'activity_type': activity.get('otherId')
                    }
                )
            except Exception as stats_e:
                if is_debug_mode():
                    debug_print(f"记录统计信息失败: {stats_e}", "yellow")
            
            return {
                'status': False,
                'message': '签到失败',
                'result': result,
                'activity': activity
            }
        
        # 检查签到结果是否真正成功
        is_sign_success = '签到成功' in result or result == 'success' or '[通用]签到成功' in result or '[位置]签到成功' in result or '[拍照]签到成功' in result or '[手势]签到成功' in result or '[二维码]签到成功' in result or '[签到码]签到成功' in result
        
        # 记录签到信息并更新用户信息
        phone = params.pop('phone', None)
        password = params.pop('password', None)
        if phone:
            user_data = {
                'phone': phone,
                'params': params,
                **updated_configs
            }
            
            # 如果获取到了用户名，保存它
            if name and name != "未知用户":
                user_data['username'] = name
            
            # 如果有密码，保存它
            if password:
                user_data['password'] = password
                
            store_user(phone, user_data)
            
            if is_debug_mode():
                debug_print("用户信息已更新并保存", "green")
        
        # 根据签到结果记录统计
        try:
            from utils.stats import record_sign_result
            record_sign_result(
                user_phone=phone,
                username=name,
                success=is_sign_success,
                message=result,
                activity_info={
                    'activity_id': activity.get('activeId'),
                    'activity_type': activity.get('otherId')
                }
            )
        except Exception as stats_e:
            if is_debug_mode():
                debug_print(f"记录统计信息失败: {stats_e}", "yellow")
        
        if is_sign_success:
            sign_logger.info(f"签到成功: {result}")
            return {
                'status': True,
                'message': '签到成功',
                'result': result,
                'activity': activity
            }
        else:
            sign_logger.error(f"签到失败: {result}")
            return {
                'status': False,
                'message': '签到失败',
                'result': result,
                'activity': activity
            }
    except Exception as e:
        error_message = f'签到执行过程出错: {e}'
        traceback.print_exc()
        
        # 记录签到失败统计
        try:
            from utils.stats import record_sign_result
            phone = params.get('phone', '未知用户')
            record_sign_result(
                user_phone=phone,
                username=name,
                success=False,
                message=error_message
            )
        except Exception as stats_e:
            if is_debug_mode():
                debug_print(f"记录统计信息失败: {stats_e}", "yellow")
        
        return {
            'status': False,
            'message': error_message
        }


if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            # 默认使用第一个用户
            result = sign_by_index(0)
        else:
            # 获取用户信息
            json_object = get_json_object('configs/storage.json')
            user_arg = sys.argv[1]
            
            # 先尝试查找手机号
            phone_match = False
            for user in json_object.get('users', []):
                if user.get('phone') == user_arg:
                    phone_match = True
                    break
            
            if phone_match:
                # 如果找到匹配的手机号，使用手机号签到
                result = sign_by_phone(user_arg)
            elif user_arg.isdigit() and int(user_arg) < len(json_object.get('users', [])):
                # 如果是有效的索引号，使用索引签到
                result = sign_by_index(int(user_arg))
            else:
                # 否则当作手机号处理
                result = sign_by_phone(user_arg)
        
        if result['status']:
            colored_print(result['message'], "green")
        else:
            colored_print(result['message'], "red")
            
    except Exception as e:
        colored_print(f"程序运行出错: {e}", "red")
        colored_print("详细错误信息:", "red")
        traceback.print_exc()
        sys.exit(1) 