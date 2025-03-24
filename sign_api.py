import json
import sys
import traceback

from functions.activity import get_ppt_active_info, pre_sign, traverse_course_activity, handle_activity_sign
from functions.user import get_courses
from utils.file import get_json_object
from utils.helper import colored_print

def sign_by_index(user_index=0):
    """
    根据用户索引进行签到
    
    Args:
        user_index: 用户在storage.json中的索引，默认为0
        
    Returns:
        dict: 签到结果，包含状态和消息
    """
    try:
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
        params = {**user['params']}
        params['phone'] = user['phone']
        
        # 调用签到功能
        return execute_sign(params, user.get('monitor', {}), user.get('username', '未知用户'))
    
    except Exception as e:
        error_message = f'签到过程出错: {e}'
        traceback.print_exc()
        return {
            'status': False,
            'message': error_message
        }

def sign_by_phone(phone):
    """
    根据手机号进行签到
    
    Args:
        phone: 用户手机号
        
    Returns:
        dict: 签到结果，包含状态和消息
    """
    try:
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
        params = {**user['params']}
        params['phone'] = user['phone']
        
        # 调用签到功能
        return execute_sign(params, user.get('monitor', {}), user.get('username', '未知用户'))
    
    except Exception as e:
        error_message = f'签到过程出错: {e}'
        traceback.print_exc()
        return {
            'status': False,
            'message': error_message
        }

def execute_sign(params, configs, name):
    """
    执行签到流程
    
    Args:
        params: 用户参数
        configs: 配置信息
        name: 用户名
        
    Returns:
        dict: 签到结果，包含状态和消息
    """
    try:
        # 获取所有课程
        courses = get_courses(params['_uid'], params['_d'], params['vc3'])
        if isinstance(courses, str):
            return {
                'status': False,
                'message': f'获取课程失败: {courses}'
            }
        
        # 获取进行中的签到活动
        activity = traverse_course_activity({'courses': courses, **params})
        if isinstance(activity, str):
            return {
                'status': False,
                'message': f'获取签到活动失败: {activity}'
            }
        
        # 处理签到，根据签到类型自动选择处理方式
        result, updated_configs = handle_activity_sign(params, activity, configs, name)
        
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