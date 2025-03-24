import json
import sys
import time
import getpass

from .functions.activity import get_ppt_active_info, pre_sign, traverse_course_activity, get_sign_type
from .functions.general import general_sign
from .functions.location import location_sign
from .functions.photo import photo_sign, get_object_id_from_cx_pan
from .functions.qrcode import qrcode_sign
from .functions.user import get_account_info, get_courses, get_local_users, user_login
from .utils.file import get_json_object, store_user
from .utils.helper import colored_print, delay

def monitor_sign():
    """监听签到主函数"""
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
            store_user(phone, {'phone': phone, 'params': result})
        
        params = {**result, 'phone': phone}
        
        # 初始化监控配置
        configs['monitor'] = {
            'delay': 0,
            'presetAddress': []
        }
        
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
    else:
        # 使用本地储存的参数
        json_object = get_json_object('configs/storage.json')['users'][user_item]
        params = {**json_object['params']}
        params['phone'] = json_object['phone']
        configs['monitor'] = json_object.get('monitor', {
            'delay': 0,
            'presetAddress': []
        })
    
    # 获取用户名
    name = get_account_info(params)
    colored_print(f"你好，{name}", "blue")
    
    # 开始监控
    colored_print(f"开始监控签到，延迟 {configs['monitor'].get('delay', 0)} 秒", "blue")
    colored_print("按 Ctrl+C 退出监控", "blue")
    
    try:
        while True:
            try:
                # 获取所有课程
                courses = get_courses(params['_uid'], params['_d'], params['vc3'])
                if isinstance(courses, str):
                    delay(60)
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
                
                # 处理签到
                other_id = activity['otherId']
                
                if other_id == 2:
                    # 二维码签到，无法自动处理
                    colored_print("发现二维码签到，无法自动处理", "red")
                
                elif other_id == 4:
                    # 位置签到
                    colored_print("发现位置签到，尝试使用预设位置", "blue")
                    
                    # 使用预设位置
                    preset_address = configs['monitor'].get('presetAddress', [])
                    if not preset_address:
                        colored_print("没有预设位置，使用默认位置", "red")
                        address_item = {
                            'lon': '113.516288',
                            'lat': '34.817038',
                            'address': '北京市海淀区双清路清华大学'
                        }
                    else:
                        # 使用第一个预设位置
                        address_item = preset_address[0]
                    
                    # 执行位置签到
                    result = location_sign({
                        **params, 
                        **address_item, 
                        'activeId': activity['activeId'], 
                        'name': name,
                        'fid': params.get('fid', '-1')
                    })
                    
                    if '[位置]签到成功' in result:
                        delay(10)
                    else:
                        # 签到失败，尝试其他位置
                        for i in range(1, len(preset_address)):
                            colored_print(f"尝试使用备用位置 {i}", "blue")
                            result = location_sign({
                                **params, 
                                **preset_address[i], 
                                'activeId': activity['activeId'], 
                                'name': name,
                                'fid': params.get('fid', '-1')
                            })
                            if '[位置]签到成功' in result:
                                break
                
                elif other_id == 3:
                    # 手势签到
                    colored_print("发现手势签到", "blue")
                    result = general_sign({
                        **params, 
                        'activeId': activity['activeId'], 
                        'name': name,
                        'fid': params.get('fid', '-1')
                    })
                
                
                elif other_id == 5:
                    # 签到码签到
                    colored_print("发现签到码签到", "blue")
                    result = general_sign({
                        **params, 
                        'activeId': activity['activeId'], 
                        'name': name,
                        'fid': params.get('fid', '-1')
                    })
                    
                
                elif other_id == 0:
                    # 获取签到详情
                    photo = get_ppt_active_info(activity['activeId'], **params)
                    
                    if photo.get('ifphoto') == 1:
                        # 拍照签到，无法自动处理
                        colored_print("发现拍照签到，无法自动处理", "red")
                    else:
                        # 普通签到
                        colored_print("发现普通签到", "blue")
                        result = general_sign({
                            **params, 
                            'activeId': activity['activeId'], 
                            'name': name,
                            'fid': params.get('fid', '-1')
                        })
                        
                
                # 记录签到信息
                phone = params.get('phone')
                if phone:
                    params_copy = params.copy()
                    params_copy.pop('phone', None)
                    store_user(phone, {'phone': phone, 'params': params_copy, **configs})
            
            except KeyboardInterrupt:
                raise
            except Exception as e:
                colored_print(f"发生错误: {e}", "red")
            
    
    except KeyboardInterrupt:
        colored_print("监控已停止", "blue")
        
        # 保存最新配置
        phone = params.get('phone')
        if phone:
            params_copy = params.copy()
            params_copy.pop('phone', None)
            store_user(phone, {'phone': phone, 'params': params_copy, **configs})

if __name__ == "__main__":
    monitor_sign()