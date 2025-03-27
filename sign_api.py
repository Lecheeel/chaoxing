import json
import sys
import traceback
import time

from functions.activity import get_ppt_active_info, pre_sign, traverse_course_activity, handle_activity_sign
from functions.user import get_account_info, get_courses, get_local_users, user_login
from utils.file import get_json_object, store_user
from utils.helper import colored_print
from utils.debug import is_debug_mode, debug_print
from utils.request import request_manager

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
        if is_debug_mode():
            debug_print(f"开始通过索引 {user_index} 进行签到", "blue")
            
        # 读取storage.json中的用户信息
        json_object = get_json_object('configs/storage.json')
        
        # 检查用户是否存在
        if 'users' not in json_object or len(json_object['users']) <= user_index:
            return {
                'status': False,
                'message': f'用户索引{user_index}不存在，请确认storage.json中有足够的用户'
            }
        
        # 获取用户信息
        user = json_object['users'][user_index]
        params = {}
        # 复制params内的cookie信息
        if 'params' in user and isinstance(user['params'], dict):
            params = {**user['params']}
        # 复制其他非cookie信息
        params['phone'] = user['phone']
        params['password'] = user.get('password', '')
        
        # 确保请求管理器有正确的认证cookie，只有params内的才会被设为cookie
        request_manager.set_auth_cookies({'params': params})
        
        if is_debug_mode():
            debug_print(f"成功获取用户信息: 手机号={params['phone']}", "green")
        
        # 调用签到功能
        return execute_sign(params, user.get('monitor', {}), user.get('username', '未知用户'), 
                           location_preset_item, location_address_info, location_random_offset)
    
    except Exception as e:
        error_message = f'签到过程出错: {e}'
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
        # 复制params内的cookie信息
        if 'params' in user and isinstance(user['params'], dict):
            params = {**user['params']}
        # 复制其他非cookie信息
        params['phone'] = user['phone']
        params['password'] = user.get('password', '')
        
        # 确保请求管理器有正确的认证cookie，只有params内的才会被设为cookie
        request_manager.set_auth_cookies({'params': params})
        
        if is_debug_mode():
            debug_print(f"成功获取用户信息: 手机号={params['phone']}", "green")
        
        # 调用签到功能
        return execute_sign(params, user.get('monitor', {}), user.get('username', '未知用户'),
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
        if is_debug_mode():
            debug_print("开始获取课程列表", "blue")
            if location_random_offset:
                debug_print("位置随机偏移功能已开启", "blue")
        
        # 确保请求管理器有正确的认证cookie
        request_manager.set_auth_cookies(params)
        
        # 获取所有课程
        courses = get_courses(params['_uid'], params['_d'], params['vc3'])
        if isinstance(courses, str):
            if is_debug_mode():
                debug_print(f"获取课程失败: {courses}", "red")
            return {
                'status': False,
                'message': f'获取课程失败: {courses}'
            }
        
        if is_debug_mode():
            debug_print(f"成功获取课程列表，共 {len(courses)} 门课程", "green")
            debug_print("开始查找进行中的签到活动", "blue")
        
        # 获取进行中的签到活动
        activity = traverse_course_activity({'courses': courses, **params})
        if isinstance(activity, str):
            if is_debug_mode():
                debug_print(f"未找到进行中的签到活动: {activity}", "yellow")
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
        
        return {
            'status': True,
            'message': '签到成功',
            'result': result,
            'activity': activity
        }
    except Exception as e:
        error_message = f'签到执行过程出错: {e}'
        traceback.print_exc()
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