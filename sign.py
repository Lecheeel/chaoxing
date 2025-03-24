import json
import sys
import time
import getpass

from functions.activity import get_ppt_active_info, pre_sign, traverse_course_activity, handle_activity_sign
from functions.general import general_sign
from functions.location import location_sign, preset_address_choices
from functions.photo import photo_sign, get_object_id_from_cx_pan
from functions.qrcode import qrcode_sign
from functions.user import get_account_info, get_courses, get_local_users, user_login
from utils.file import get_json_object, store_user
from utils.helper import colored_print

def main():
    """主函数，处理单次签到"""
    params = {}
    configs = {}
    
    # 用户选择
    local_users = get_local_users()
    
    # 打印用户列表
    colored_print("选择用户:", "blue")
    for i, user in enumerate(local_users):
        if user['value'] == -1:
            colored_print(f"{i+1}. {user['title']}", "blue")
        else:
            print(f"{i+1}. {user['title']}")
    
    choice = input("请输入选项编号: ")
    try:
        user_item = local_users[int(choice) - 1]['value']
    except (ValueError, IndexError):
        colored_print("无效选择，退出程序", "red")
        sys.exit(1)
    
    # 使用新用户登录
    if user_item == -1:
        phone = input("手机号: ")
        password = getpass.getpass("密码: ")
        
        # 登录获取各参数
        result = user_login(phone, password)
        if isinstance(result, str):
            sys.exit(1)
        else:
            # 创建用户对象，包含电话号码和密码
            user_data = {
                'phone': phone, 
                'password': password,
                # 'active': True,
                'params': result
            }
            store_user(phone, user_data)
        
        params = {**result, 'phone': phone}
    else:
        # 使用本地储存的参数
        json_object = get_json_object('configs/storage.json')['users'][user_item]
        params = {**json_object['params']}
        params['phone'] = json_object['phone']
        # 也保存密码，便于后续可能需要的重新登录
        params['password'] = json_object.get('password', '')
        configs['monitor'] = {**json_object.get('monitor', {})}
    
    # 获取用户名
    name = get_account_info(params)
    colored_print(f"你好，{name}", "blue")
    
    # 获取所有课程
    courses = get_courses(params['_uid'], params['_d'], params['vc3'])
    if isinstance(courses, str):
        sys.exit(1)
    
    # 获取进行中的签到活动
    activity = traverse_course_activity({'courses': courses, **params})
    if isinstance(activity, str):
        sys.exit(1)
    
    # 处理签到，根据签到类型自动选择处理方式
    result, updated_configs = handle_activity_sign(params, activity, configs, name)
    
    # 记录签到信息并更新用户名
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

if __name__ == "__main__":
    main() 