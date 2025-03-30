import time
import getpass

from functions.activity import get_ppt_active_info, pre_sign, traverse_course_activity
from functions.general import general_sign, handle_code_sign
from functions.gesture import handle_gesture_sign
from functions.location import location_sign
from functions.user import get_account_info, get_courses, get_local_users, user_login
from utils.file import get_json_object, store_user
from utils.helper import colored_print, delay

def monitor_sign():
    """监听签到主函数"""
    params = {}
    configs = {}
    
    try:
        # 获取用户列表
        local_users = get_local_users()
        
        # 打印用户选项
        colored_print("选择用户:", "blue")
        for i, user in enumerate(local_users):
            if user['value'] == -1:
                colored_print(f"{i+1}. {user['title']}", "blue")
            else:
                print(f"{i+1}. {user['title']}")
        
        # 选择用户
        choice = input("选项编号: ")
        try:
            user_item = local_users[int(choice) - 1]['value']
        except (ValueError, IndexError):
            colored_print("无效选择，退出程序", "red")
            return
        
        # 处理用户选择
        if user_item == -1:
            # 新用户登录
            params, configs = handle_new_user_login()
            if not params:
                return
        else:
            # 使用已有账号
            json_object = get_json_object('configs/storage.json')['users'][user_item]
            params = {**json_object['params'], 'phone': json_object['phone']}
            configs['monitor'] = json_object.get('monitor', {
                'delay': 0,
                'presetAddress': []
            })
        
        # 获取用户名并开始监听
        name = get_account_info(params)
        print(params)
        colored_print(f"你好，{name}", "blue")
        colored_print(f"开始监听签到，延迟 {configs['monitor'].get('delay', 0)} 秒", "blue")
        colored_print("按 Ctrl+C 退出监听", "blue")
        
        # 主监听循环
        start_monitoring(params, configs, name)
            
    except KeyboardInterrupt:
        colored_print("监听已停止", "blue")
        
        # 保存最新配置
        save_user_config(params, configs)

def handle_new_user_login():
    """处理新用户登录流程"""
    phone = input("手机号: ")
    password = getpass.getpass("密码: ")
    
    # 登录获取各参数
    result = user_login(phone, password)
    if isinstance(result, str):
        colored_print(f"登录失败: {result}", "red")
        return None, None
    
    # 保存用户信息
    params = {**result, 'phone': phone}
    store_user(phone, {'phone': phone, 'params': result})
    
    # 初始化监听配置
    configs = {'monitor': {'delay': 0, 'presetAddress': []}}
    
    # 设置位置信息
    colored_print("[获取经纬度]https://api.map.baidu.com/lbsapi/getpoint/index.html", "blue")
    lon_lat_address = input("位置参数预设（经纬度/地址）[116.333585,40.008944/北京市海淀区双清路清华大学]: ") or "116.333585,40.008944/北京市海淀区双清路清华大学"
    
    import re
    match = re.match(r'([\d.]*),([\d.]*)\/(\S*)', lon_lat_address)
    if match:
        configs['monitor']['lon'] = match.group(1)
        configs['monitor']['lat'] = match.group(2)
        configs['monitor']['address'] = match.group(3)
        
        # 添加到预设地址
        configs['monitor']['presetAddress'].append({
            'lon': match.group(1),
            'lat': match.group(2),
            'address': match.group(3)
        })
    else:
        colored_print("地址格式错误，使用默认值", "red")
        configs['monitor']['lon'] = '113.516288'
        configs['monitor']['lat'] = '34.817038'
        configs['monitor']['address'] = '北京市海淀区双清路清华大学'
        
        # 添加到预设地址
        configs['monitor']['presetAddress'].append({
            'lon': '113.516288',
            'lat': '34.817038',
            'address': '北京市海淀区双清路清华大学'
        })
    
    # 设置延迟时间
    delay_time = input("签到延迟时间(秒) [0]: ") or "0"
    try:
        configs['monitor']['delay'] = int(delay_time)
    except ValueError:
        colored_print("延迟时间格式错误，使用默认值0", "red")
        configs['monitor']['delay'] = 0
        
    return params, configs

def start_monitoring(params, configs, name):
    """开始监听签到"""
    while True:
        try:
            # 获取所有课程
            courses = get_courses(params['_uid'], params['_d'], params['vc3'])
            if isinstance(courses, str):
                delay(10)
                continue
            
            # 获取进行中的签到活动
            activity = traverse_course_activity({'courses': courses, **params})
            if isinstance(activity, str):
                delay(10)
                continue
            
            # 发现签到活动，延迟指定时间
            if configs['monitor'].get('delay', 0) > 0:
                colored_print(f"发现签到活动，将在 {configs['monitor']['delay']} 秒后签到", "blue")
                delay(configs['monitor']['delay'])
            
            # 预签到
            pre_sign({**activity, **params})
            
            # 根据签到类型处理签到
            other_id = activity['otherId']
            
            if other_id == 2:
                # 二维码签到
                colored_print("发现二维码签到，需要手动处理", "yellow")
            
            elif other_id == 4:
                # 位置签到
                colored_print("发现位置签到，尝试使用预设位置", "blue")
                
                # 获取预设位置
                preset_address = configs['monitor'].get('presetAddress', [])
                if not preset_address:
                    colored_print("没有预设位置，使用默认位置", "red")
                    address_item = {
                        'lon': '113.516288',
                        'lat': '34.817038',
                        'address': '北京市海淀区双清路清华大学'
                    }
                    # 尝试单个位置签到
                    result = location_sign({
                        **params, 
                        **address_item, 
                        'activeId': activity['activeId'], 
                        'name': name,
                        'fid': params.get('fid', '-1')
                    })
                else:
                    # 逐个尝试预设位置
                    for i, address_item in enumerate(preset_address):
                        colored_print(f"尝试位置 {i+1}: {address_item['address']}", "blue")
                        result = location_sign({
                            **params, 
                            **address_item, 
                            'activeId': activity['activeId'], 
                            'name': name,
                            'fid': params.get('fid', '-1')
                        })
                        if '[位置]签到成功' in result:
                            break
                        time.sleep(1)  # 避免请求过于频繁
            
            elif other_id == 3:
                # 手势签到
                colored_print("发现手势签到", "blue")
                
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
                success = False
                
                for pattern_name, pattern_code in gesture_patterns.items():
                    colored_print(f"尝试手势: '{pattern_name}' ({pattern_code})", "blue")
                    
                    # 准备签到参数
                    sign_params = {**params, 'signCode': pattern_code, 'activeId': activity['activeId']}
                    
                    # 执行手势签到
                    result = handle_gesture_sign(sign_params, activity, name)
                    
                    # 判断是否签到成功
                    if "签到成功" in result:
                        colored_print(f"手势签到成功! 图案: {pattern_name}", "green")
                        success = True
                        break
                    
                    # 防止请求过于频繁
                    time.sleep(0.5)
                
                # 预设手势失败时手动输入
                if not success:
                    colored_print("预设手势均失败，请手动输入", "yellow")
                    colored_print("提示：查看学习通APP中手势图案，输入对应数字，如：1342", "blue")
                    sign_code = input("手势签到码: ").strip()
                    
                    if sign_code:
                        result = handle_gesture_sign({**params, 'signCode': sign_code, 'activeId': activity['activeId']}, activity, name)
                        colored_print(f"手势签到结果: {result}", "blue")
                    else:
                        colored_print("未提供手势码，无法完成签到", "red")
            
            elif other_id == 5:
                # 签到码签到
                colored_print("发现签到码签到", "blue")
                colored_print("提示：请输入老师公布的签到码（通常为4-6位数字）", "blue")
                sign_code = input("签到码: ").strip()
                
                if sign_code:
                    # 执行签到码签到
                    result = handle_code_sign({**params, 'signCode': sign_code}, activity, name)
                    colored_print(f"签到结果: {result}", "blue")
                else:
                    colored_print("未提供签到码，无法完成签到", "red")
            
            elif other_id == 0:
                # 获取签到详情
                photo = get_ppt_active_info(activity['activeId'], **params)
                
                if photo.get('ifphoto') == 1:
                    # 拍照签到
                    colored_print("发现拍照签到，需要手动处理", "yellow")
                else:
                    # 普通签到
                    colored_print("发现普通签到，自动处理中", "blue")
                    result = general_sign({
                        **params, 
                        'activeId': activity['activeId'], 
                        'name': name,
                        'fid': params.get('fid', '-1')
                    })
                    colored_print(f"签到结果: {result}", "blue")
            
            # 记录签到信息和更新用户配置
            save_user_config(params, configs)
            
            # 继续监听
            colored_print("继续监听中...", "blue")
            delay(1)
            
        except KeyboardInterrupt:
            raise
        except Exception as e:
            colored_print(f"发生错误: {e}", "red")
            delay(1)

def save_user_config(params, configs):
    """保存用户配置"""
    phone = params.get('phone')
    if phone:
        params_copy = params.copy()
        params_copy.pop('phone', None)
        store_user(phone, {'phone': phone, 'params': params_copy, **configs})

if __name__ == "__main__":
    monitor_sign()