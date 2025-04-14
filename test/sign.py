import json
import sys
import time
import getpass

from functions.activity import get_ppt_active_info, pre_sign, traverse_course_activity, handle_activity_sign
from functions.user import get_account_info, get_courses, get_local_users, user_login
from functions.location import preset_address_choices
from utils.file import get_json_object, store_user
from utils.helper import colored_print
from utils.debug import is_debug_mode, debug_print
from utils.request import request_manager

def main():
    """主函数，处理单次签到"""
    if is_debug_mode():
        debug_print("开始执行单次签到流程", "blue")
    
    params = {}
    configs = {}
    
    # 用户选择
    local_users = get_local_users()
    
    if is_debug_mode():
        debug_print(f"找到 {len(local_users)-1} 个本地存储的用户", "blue")
    
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
        if is_debug_mode():
            debug_print(f"用户选择选项: {choice}, 对应值: {user_item}", "blue")
    except (ValueError, IndexError):
        colored_print("无效选择，退出程序", "red")
        if is_debug_mode():
            debug_print("用户输入了无效选择", "red")
        sys.exit(1)
    
    # 使用新用户登录
    if user_item == -1:
        if is_debug_mode():
            debug_print("用户选择了手动登录", "blue")
        
        phone = input("手机号: ")
        password = getpass.getpass("密码: ")
        
        if is_debug_mode():
            debug_print(f"用户输入手机号: {phone}", "blue")
        
        # 登录获取各参数
        result = user_login(phone, password)
        if isinstance(result, str):
            if is_debug_mode():
                debug_print(f"登录失败: {result}", "red")
            sys.exit(1)
        else:
            if is_debug_mode():
                debug_print("登录成功，正在获取用户信息", "green")
            
            # 获取用户真实姓名
            user_params = {**result, 'phone': phone}
            user_name = get_account_info(user_params)
            
            # 创建用户对象，包含电话号码和密码
            user_data = {
                'phone': phone, 
                'password': password,
                # 'active': True,
                'params': result
            }
            
            # 保存用户名
            if user_name and user_name != "未知用户":
                user_data['username'] = user_name
                colored_print(f"你好，{user_name}", "blue")
                if is_debug_mode():
                    debug_print(f"成功获取用户名: {user_name}", "green")
            else:
                if is_debug_mode():
                    debug_print("未能获取有效的用户名", "yellow")
            
            # 询问用户是否添加位置信息
            colored_print("是否添加位置信息用于位置签到？(y/n): ", "blue")
            add_location = input().lower()
            if add_location == 'y':
                colored_print("请输入位置信息，格式为：经度,纬度/地址", "blue")
                colored_print("例如：116.333585,40.008944/北京市海淀区双清路清华大学", "blue")
                location_info = input("位置信息: ")
                
                import re
                match = re.match(r'([\d.]*),([\d.]*)\/(\S*)', location_info)
                if match:
                    lon = match.group(1)
                    lat = match.group(2)
                    address = match.group(3)
                    
                    # 添加预设地址
                    if 'monitor' not in user_data:
                        user_data['monitor'] = {}
                    if 'presetAddress' not in user_data['monitor']:
                        user_data['monitor']['presetAddress'] = []
                    
                    user_data['monitor']['presetAddress'].append({
                        'lon': lon,
                        'lat': lat,
                        'address': address
                    })
                    
                    colored_print("位置信息添加成功！", "green")
                    if is_debug_mode():
                        debug_print(f"已添加位置信息: 经度={lon}, 纬度={lat}, 地址={address}", "green")
                else:
                    colored_print("位置信息格式错误，将使用默认位置", "red")
                    if is_debug_mode():
                        debug_print("位置信息格式错误", "red")
            
            store_user(phone, user_data)
            if is_debug_mode():
                debug_print(f"用户信息已保存到本地", "green")
        
        params = {**result, 'phone': phone}
        
        # 同步配置信息
        if 'monitor' in user_data:
            configs['monitor'] = user_data['monitor']
    else:
        # 使用本地储存的参数
        if is_debug_mode():
            debug_print(f"使用本地存储的用户信息，索引: {user_item}", "blue")
        
        json_object = get_json_object('configs/storage.json')['users'][user_item]
        # 从storage.json中分离params和其他信息
        params = {}
        # 复制params内的cookie信息
        if 'params' in json_object and isinstance(json_object['params'], dict):
            params = {**json_object['params']}
        # 复制其他非cookie信息
        params['phone'] = json_object['phone']
        # 也保存密码，便于后续可能需要的重新登录
        params['password'] = json_object.get('password', '')
        configs['monitor'] = {**json_object.get('monitor', {})}
        
        # 检查是否有预设位置信息
        if not configs.get('monitor') or not configs['monitor'].get('presetAddress'):
            colored_print("未检测到预设位置信息，是否添加？(y/n): ", "blue")
            add_location = input().lower()
            if add_location == 'y':
                colored_print("请输入位置信息，格式为：经度,纬度/地址", "blue")
                colored_print("例如：116.333585,40.008944/北京市海淀区双清路清华大学", "blue")
                location_info = input("位置信息: ")
                
                import re
                match = re.match(r'([\d.]*),([\d.]*)\/(\S*)', location_info)
                if match:
                    lon = match.group(1)
                    lat = match.group(2)
                    address = match.group(3)
                    
                    # 添加预设地址
                    if 'monitor' not in configs:
                        configs['monitor'] = {}
                    if 'presetAddress' not in configs['monitor']:
                        configs['monitor']['presetAddress'] = []
                    
                    configs['monitor']['presetAddress'].append({
                        'lon': lon,
                        'lat': lat,
                        'address': address
                    })
                    
                    colored_print("位置信息添加成功！", "green")
                    if is_debug_mode():
                        debug_print(f"已添加位置信息: 经度={lon}, 纬度={lat}, 地址={address}", "green")
                    
                    # 保存到本地
                    json_object['monitor'] = configs['monitor']
                    store_user(params['phone'], json_object)
                    if is_debug_mode():
                        debug_print("用户信息已更新并保存", "green")
                else:
                    colored_print("位置信息格式错误，将使用默认位置", "red")
                    if is_debug_mode():
                        debug_print("位置信息格式错误", "red")
        
        if is_debug_mode():
            debug_print(f"读取用户信息成功: 手机号={params['phone']}", "green")
            debug_print(f"用户配置项数量: {len(configs['monitor'])}", "blue")
        
        # 设置认证相关的cookie，只有params内的才会被设为cookie
        request_manager.set_auth_cookies(params)
    
    # 获取用户名
    name = get_account_info(params)
    # 如果前面没有打印过欢迎信息，则在这里打印
    if 'user_name' not in locals() or name != user_name:
        colored_print(f"你好，{name}", "blue")
    
    if is_debug_mode():
        debug_print("开始获取课程列表", "blue")
    
    # 获取所有课程
    courses = get_courses(params['_uid'], params['_d'], params['vc3'])
    if isinstance(courses, str):
        if is_debug_mode():
            debug_print(f"获取课程失败: {courses}", "red")
        sys.exit(1)
    
    if is_debug_mode():
        debug_print(f"成功获取课程列表，共 {len(courses)} 门课程", "green")
        debug_print("开始查找进行中的签到活动", "blue")
    
    # 获取进行中的签到活动
    activity = traverse_course_activity({'courses': courses, **params})
    if isinstance(activity, str):
        if is_debug_mode():
            debug_print(f"未找到进行中的签到活动: {activity}", "yellow")
        sys.exit(1)
    
    if is_debug_mode():
        debug_print(f"找到签到活动: ID={activity['activeId']}, 类型={activity['otherId']}", "green")
        debug_print("开始进行签到", "blue")
    
    # 处理签到，根据签到类型自动选择处理方式
    result, updated_configs = handle_activity_sign(params, activity, configs, name)
    
    if is_debug_mode():
        debug_print(f"签到结果: {result}", "green")
        debug_print("开始保存用户信息", "blue")
    
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
        
        if is_debug_mode():
            debug_print("用户信息已更新并保存", "green")
            debug_print("单次签到流程完成", "green")

if __name__ == "__main__":
    main() 