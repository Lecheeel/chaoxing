from configs.api import CHAT_GROUP, PPTSIGN
from utils.request import request, cookie_serialize, request_manager
from utils.helper import delay, colored_print
from utils.debug import is_debug_mode, debug_print
import random
import math

def location_sign(args):
    """
    位置签到
    
    Args:
        args: 包含活动ID、位置信息和用户凭证的字典
    
    Returns:
        str: 签到结果消息
    """
    msg = ''
    
    # 判断是单个位置还是多个位置
    if 'address' in args:
        # 单个位置直接签到
        name = args.get('name', '')
        address = args.get('address', '')
        active_id = args.get('activeId', '')
        lat = args.get('lat', '')
        lon = args.get('lon', '')
        fid = args.get('fid', '')
        cookies = {k: v for k, v in args.items() if k not in ['name', 'address', 'activeId', 'lat', 'lon', 'fid']}
        
        if is_debug_mode():
            debug_print(f"执行位置签到: activeId={active_id}, name={name}", "blue")
            debug_print(f"位置信息: 地址={address}, 经度={lon}, 纬度={lat}", "blue")
        
        # 设置临时cookies
        if cookies:
            request_manager.set_cookies(cookies)
            
        url = f"{PPTSIGN['URL']}?name={name}&address={address}&activeId={active_id}&uid={cookies.get('_uid', '')}&clientip=&latitude={lat}&longitude={lon}&fid={fid}&appType=15&ifTiJiao=1"
        result = request_manager.request(
            url,
            {
                'scenario': 'activity',
            }
        )
        
        # 检查是否在可签到范围内
        if result['data'] == 'success':
            msg = '[位置]签到成功'
        elif '不在可签到范围内' in result['data']:
            msg = '[位置]不在可签到范围内'
        else:
            msg = f"[位置]{result['data']}"
        
        if is_debug_mode():
            debug_print(f"位置签到结果: {result['data']}", "green" if result['data'] == 'success' else "red")
    else:
        # 多个位置尝试
        name = args.get('name', '')
        active_id = args.get('activeId', '')
        preset_address = args.get('presetAddress', [])
        fid = args.get('fid', '')
        cookies = {k: v for k, v in args.items() if k not in ['name', 'activeId', 'presetAddress', 'fid']}
        
        if is_debug_mode():
            debug_print(f"执行多位置尝试签到: activeId={active_id}, name={name}", "blue")
            debug_print(f"预设位置数量: {len(preset_address)}", "blue")
        
        # 设置临时cookies
        if cookies:
            request_manager.set_cookies(cookies)
            
        for i, address_item in enumerate(preset_address):
            if is_debug_mode():
                debug_print(f"尝试第{i+1}个位置: 地址={address_item['address']}, 经度={address_item['lon']}, 纬度={address_item['lat']}", "blue")
                
            url = f"{PPTSIGN['URL']}?name={name}&address={address_item['address']}&activeId={active_id}&uid={cookies.get('_uid', '')}&clientip=&latitude={address_item['lat']}&longitude={address_item['lon']}&fid={fid}&appType=15&ifTiJiao=1"
            result = request_manager.request(
                url,
                {
                    'scenario': 'activity',
                }
            )
            
            if result['data'] == 'success':
                msg = '[位置]签到成功'
                if is_debug_mode():
                    debug_print(f"位置签到成功，使用第{i+1}个位置", "green")
                break
            elif '不在可签到范围内' in result['data']:
                msg = '[位置]不在可签到范围内'
                if is_debug_mode():
                    debug_print(f"位置不在可签到范围内，尝试下一个位置", "yellow")
                delay(1)
            else:
                msg = f"[位置]{result['data']}"
                if is_debug_mode():
                    debug_print(f"位置签到失败: {result['data']}，尝试下一个位置", "yellow")
                delay(1)
    
    print(msg)
    return msg

def location_sign_2(args):
    """
    位置签到，无课程群聊版本
    
    Args:
        args: 包含活动ID、位置信息和用户凭证的字典
    
    Returns:
        str: 签到结果消息
    """
    msg = ''
    
    # 判断是单个位置还是多个位置
    if 'address' in args:
        # 单个位置直接签到
        address = args.get('address', '')
        active_id = args.get('activeId', '')
        lat = args.get('lat', '')
        lon = args.get('lon', '')
        cookies = {k: v for k, v in args.items() if k not in ['address', 'activeId', 'lat', 'lon']}
        
        if is_debug_mode():
            debug_print(f"执行群聊位置签到: activeId={active_id}", "blue")
            debug_print(f"位置信息: 地址={address}, 经度={lon}, 纬度={lat}", "blue")
        
        # 设置临时cookies
        if cookies:
            request_manager.set_cookies(cookies)
            
        formdata = f"address={address}&activeId={active_id}&uid={cookies.get('_uid', '')}&clientip=&useragent=&latitude={lat}&longitude={lon}&fid=&ifTiJiao=1"
        result = request_manager.request(
            CHAT_GROUP['SIGN']['URL'],
            {
                'method': 'POST',
                'scenario': 'activity',
                'headers': {
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                },
            },
            formdata
        )
        
        msg = '[位置]签到成功' if result['data'] == 'success' else f"[位置]{result['data']}"
        
        if is_debug_mode():
            debug_print(f"群聊位置签到结果: {result['data']}", "green" if result['data'] == 'success' else "red")
    else:
        # 多个位置尝试
        active_id = args.get('activeId', '')
        preset_address = args.get('presetAddress', [])
        cookies = {k: v for k, v in args.items() if k not in ['activeId', 'presetAddress']}
        
        if is_debug_mode():
            debug_print(f"执行群聊多位置尝试签到: activeId={active_id}", "blue")
            debug_print(f"预设位置数量: {len(preset_address)}", "blue")
        
        # 设置临时cookies
        if cookies:
            request_manager.set_cookies(cookies)
            
        for i, address_item in enumerate(preset_address):
            if is_debug_mode():
                debug_print(f"尝试第{i+1}个位置: 地址={address_item['address']}, 经度={address_item['lon']}, 纬度={address_item['lat']}", "blue")
                
            formdata = f"address={address_item['address']}&activeId={active_id}&uid={cookies.get('_uid', '')}&clientip=&useragent=&latitude={address_item['lat']}&longitude={address_item['lon']}&fid=&ifTiJiao=1"
            result = request_manager.request(
                CHAT_GROUP['SIGN']['URL'],
                {
                    'method': 'POST',
                    'scenario': 'activity',
                    'headers': {
                        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    },
                },
                formdata
            )
            
            if result['data'] == 'success':
                msg = '[位置]签到成功'
                if is_debug_mode():
                    debug_print(f"群聊位置签到成功，使用第{i+1}个位置", "green")
                break
            else:
                msg = f"[位置]{result['data']}"
                if is_debug_mode():
                    debug_print(f"群聊位置签到失败: {result['data']}，尝试下一个位置", "yellow")
                delay(1)
    
    print(msg)
    return msg

def preset_address_choices(preset_address=None):
    """
    生成预设地址选项
    
    Args:
        preset_address: 预设地址列表
    
    Returns:
        list: 地址选项列表
    """
    if preset_address is None:
        preset_address = []
    
    choices = []
    for i, address in enumerate(preset_address):
        choices.append({
            'title': f"{address['lat']},{address['lon']}/{address['address']}",
            'value': i,
        })
    
    choices.append({'title': '手动添加', 'value': -1})
    return choices

def random_offset_coordinates(lon, lat, max_distance=5):
    """
    为经纬度添加随机偏移
    
    Args:
        lon: 经度
        lat: 纬度
        max_distance: 最大偏移距离(米)
    
    Returns:
        tuple: (新经度, 新纬度)
    """
    # 转换为浮点数
    try:
        lon = float(lon)
        lat = float(lat)
    except ValueError:
        if is_debug_mode():
            debug_print("经纬度转换失败，使用原始值", "yellow")
        return lon, lat
    
    # 地球半径(米)
    earth_radius = 6378137.0
    
    # 随机距离(0-max_distance米)
    distance = random.uniform(0, max_distance)
    
    # 随机方向(0-360度)
    bearing = random.uniform(0, 2 * math.pi)
    
    # 纬度偏移距离转换为度
    lat_offset = distance / earth_radius * (180 / math.pi)
    
    # 经度偏移距离转换为度，考虑纬度因素
    lon_offset = distance / (earth_radius * math.cos(math.radians(lat))) * (180 / math.pi)
    
    # 根据方向计算经纬度偏移
    new_lat = lat + lat_offset * math.cos(bearing)
    new_lon = lon + lon_offset * math.sin(bearing)
    
    # 保持小数位数一致
    decimal_places_lat = len(str(lat).split('.')[-1]) if '.' in str(lat) else 6
    decimal_places_lon = len(str(lon).split('.')[-1]) if '.' in str(lon) else 6
    
    new_lat = round(new_lat, decimal_places_lat)
    new_lon = round(new_lon, decimal_places_lon)
    
    if is_debug_mode():
        debug_print(f"位置随机偏移: 原始({lon}, {lat}) -> 新({new_lon}, {new_lat}), 偏移约{distance:.2f}米", "blue")
    
    return str(new_lon), str(new_lat)

def handle_location_sign(params, activity, configs, name, preset_item=None, address_info=None, random_offset=True):
    """
    处理位置签到
    
    Args:
        params: 用户参数
        activity: 活动信息
        configs: 配置信息
        name: 用户名
        preset_item: 预设位置索引，None表示不使用预设
        address_info: 自定义位置信息，格式为"经度,纬度/地址"字符串，preset_item为None时使用
        random_offset: 是否随机偏移位置坐标(默认开启)
    
    Returns:
        tuple: (签到结果, 更新后的配置)
    """
    import re

    if is_debug_mode():
        debug_print(f"处理位置签到: 活动ID={activity['activeId']}, 用户={name}", "blue")
        if random_offset:
            debug_print("位置随机偏移功能已开启", "blue")
    
    # 获取用户的预设位置
    preset_address = configs.get('presetAddress', [])
    
    if is_debug_mode():
        debug_print(f"用户预设位置数量: {len(preset_address)}", "blue")
    
    # 首先检查用户是否有自己的预设位置
    if preset_address:
        # 用户有自己的预设位置，优先使用
        address_item = preset_address[0]  # 使用第一个预设位置
        
        if is_debug_mode():
            debug_print(f"使用用户自己的预设位置: 经度={address_item['lon']}, 纬度={address_item['lat']}, 地址={address_item['address']}", "blue")
        
        # 随机偏移坐标
        lon, lat = address_item['lon'], address_item['lat']
        if random_offset:
            lon, lat = random_offset_coordinates(lon, lat)
        
        result = location_sign({
            **params,
            'activeId': activity['activeId'],
            'name': name,
            'address': address_item['address'],
            'lat': lat,
            'lon': lon,
            'fid': params.get('fid', '-1')
        })
        return result, configs
    # 检查是否使用预设位置
    elif preset_item is not None and preset_item >= 0 and preset_item < len(preset_address):
        # 使用预设
        address_item = preset_address[preset_item]
        
        if is_debug_mode():
            debug_print(f"使用预设位置: 经度={address_item['lon']}, 纬度={address_item['lat']}, 地址={address_item['address']}", "blue")
        
        # 随机偏移坐标
        lon, lat = address_item['lon'], address_item['lat']
        if random_offset:
            lon, lat = random_offset_coordinates(lon, lat)
        
        result = location_sign({
            **params,
            'activeId': activity['activeId'],
            'name': name,
            'address': address_item['address'],
            'lat': lat,
            'lon': lon,
            'fid': params.get('fid', '-1')
        })
        return result, configs
    elif address_info:
        # 使用自定义位置
        if is_debug_mode():
            debug_print(f"使用自定义位置: {address_info}", "blue")
        
        match = re.match(r'([\d.]*),([\d.]*)\/(\S*)', address_info)
        if match:
            lat = match.group(1)
            lon = match.group(2)
            address = match.group(3)
            
            # 随机偏移坐标
            if random_offset:
                lon, lat = random_offset_coordinates(lon, lat)
            
            address_item = {
                'lon': lon,
                'lat': lat,
                'address': address
            }
            
            if is_debug_mode():
                debug_print(f"解析后的位置信息: 经度={address_item['lon']}, 纬度={address_item['lat']}, 地址={address_item['address']}", "green")
            
            # 添加到预设地址
            if 'presetAddress' not in configs:
                configs['presetAddress'] = []
            
            configs['presetAddress'].append(address_item)
            
            if is_debug_mode():
                debug_print("已将新位置添加到预设列表", "green")
            
            # 执行位置签到
            result = location_sign({
                **params,
                'activeId': activity['activeId'],
                'name': name,
                'address': address_item['address'],
                'lat': address_item['lat'],
                'lon': address_item['lon'],
                'fid': params.get('fid', '-1')
            })
            return result, configs
        else:
            if is_debug_mode():
                debug_print("位置参数格式错误，无法解析", "red")
            return "位置参数格式错误", configs
    else:
        # 没有指定位置信息
        if preset_address:
            # 有保存的预设位置，使用第一个
            if is_debug_mode():
                debug_print(f"使用第一个预设位置进行签到", "blue")
            
            address_item = preset_address[0]
            
            # 随机偏移坐标
            lon, lat = address_item['lon'], address_item['lat']
            if random_offset:
                lon, lat = random_offset_coordinates(lon, lat)
            
            if is_debug_mode():
                debug_print(f"位置信息: 经度={lon}, 纬度={lat}, 地址={address_item['address']}", "blue")
            
            result = location_sign({
                **params,
                'activeId': activity['activeId'],
                'name': name,
                'address': address_item['address'],
                'lat': lat,
                'lon': lon,
                'fid': params.get('fid', '-1')
            })
            return result, configs
        else:
            # 没有预设位置，使用默认位置
            if is_debug_mode():
                debug_print("没有预设位置，使用默认位置", "blue")
            
            # 默认位置
            default_lon = "116.333585"
            default_lat = "40.008944"
            default_address = "北京市海淀区双清路清华大学"
            
            # 随机偏移坐标
            lon, lat = default_lon, default_lat
            if random_offset:
                lon, lat = random_offset_coordinates(default_lon, default_lat)
            
            if is_debug_mode():
                debug_print(f"默认位置信息: 经度={lon}, 纬度={lat}, 地址={default_address}", "blue")
            
            result = location_sign({
                **params,
                'activeId': activity['activeId'],
                'name': name,
                'address': default_address,
                'lat': lat,
                'lon': lon,
                'fid': params.get('fid', '-1')
            })
            return result, configs
        
