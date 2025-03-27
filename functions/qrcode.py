from configs.api import PPTSIGN
from utils.request import request, cookie_serialize, request_manager
from utils.debug import is_debug_mode, debug_print

def qrcode_sign(args):
    """
    二维码签到
    
    Args:
        args: 包含活动ID、enc、位置信息和用户凭证的字典
    
    Returns:
        str: 签到结果消息
    """
    enc = args.get('enc', '')
    name = args.get('name', '')
    fid = args.get('fid', '')
    active_id = args.get('activeId', '')
    lat = args.get('lat', '')
    lon = args.get('lon', '')
    address = args.get('address', '')
    altitude = args.get('altitude', '0')
    
    # 从args中提取cookie相关参数，排除非cookie字段
    cookie_exclude_fields = ['enc', 'name', 'phone', 'password', 'username', 'activeId', 'lat', 'lon', 'address', 'altitude', 'monitor']
    
    # 如果args有params字段，则使用params内的作为cookie
    if 'params' in args and isinstance(args['params'], dict):
        cookies = args['params']
    else:
        # 否则过滤出cookie相关字段
        cookies = {k: v for k, v in args.items() if k not in cookie_exclude_fields}
    
    if is_debug_mode():
        debug_print(f"执行二维码签到: activeId={active_id}, name={name}", "blue")
        debug_print(f"二维码参数: enc={enc}", "blue")
        debug_print(f"位置信息: 地址={address}, 经度={lon}, 纬度={lat}, 海拔={altitude}", "blue")
    
    location_info = {
        "result": "1",
        "address": address,
        "latitude": lat,
        "longitude": lon,
        "altitude": altitude
    }
    
    import json
    location_json = json.dumps(location_info, ensure_ascii=False)
    
    if is_debug_mode():
        debug_print(f"位置JSON: {location_json}", "blue")
    
    url = f"{PPTSIGN['URL']}?enc={enc}&name={name}&activeId={active_id}&uid={cookies.get('_uid', '')}&clientip=&location={location_json}&latitude=-1&longitude=-1&fid={fid}&appType=15"
    
    # 对URL进行编码
    import urllib.parse
    encoded_url = urllib.parse.quote(url, safe=':/?&=')
    
    if is_debug_mode():
        debug_print(f"编码后的URL: {encoded_url}", "blue")
    
    # 设置临时cookies，确保只有cookie字段被传递
    if cookies:
        request_manager.set_cookies(cookies)
    
    result = request_manager.request(
        encoded_url,
        {
            'scenario': 'activity',
        }
    )
    
    msg = '[二维码]签到成功' if result['data'] == 'success' else f"[二维码]{result['data']}"
    print(msg)
    
    if is_debug_mode():
        debug_print(f"二维码签到结果: {result['data']}", "green" if result['data'] == 'success' else "red")
    
    return msg

def handle_qrcode_sign(params, activity, configs, name):
    """处理二维码签到，包括用户交互"""
    if is_debug_mode():
        debug_print(f"处理二维码签到: 活动ID={activity['activeId']}, 用户={name}", "blue")
    
    enc = input("enc(微信或其他识别二维码，可得enc参数): ")
    
    if is_debug_mode():
        debug_print(f"用户输入enc参数: {enc}", "blue")
    
    default_lng_lat = f"{configs.get('monitor', {}).get('lon', '113.516288')},{configs.get('monitor', {}).get('lat', '34.817038')}"
    default_address = configs.get('monitor', {}).get('address', '北京市海淀区双清路清华大学')
    
    if is_debug_mode():
        debug_print(f"默认位置参数: 经纬度={default_lng_lat}, 地址={default_address}", "blue")
    
    lnglat = input(f"经纬度 [{default_lng_lat}]: ") or default_lng_lat
    address = input(f"详细地址 [{default_address}]: ") or default_address
    altitude = input("海拔 [100]: ") or "100"
    
    lat = lnglat.split(',')[1]
    lon = lnglat.split(',')[0]
    
    if is_debug_mode():
        debug_print(f"用户输入位置参数: 经度={lon}, 纬度={lat}, 地址={address}, 海拔={altitude}", "blue")
    
    return qrcode_sign({
        **params, 
        'activeId': activity['activeId'], 
        'enc': enc, 
        'lat': lat, 
        'lon': lon, 
        'address': address, 
        'name': name, 
        'altitude': altitude,
        'fid': params.get('fid', '-1')
    }) 