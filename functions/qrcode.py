from configs.api import PPTSIGN
from utils.request import request, cookie_serialize

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
    cookies = {k: v for k, v in args.items() if k not in ['enc', 'name', 'fid', 'activeId', 'lat', 'lon', 'address', 'altitude']}
    
    location_info = {
        "result": "1",
        "address": address,
        "latitude": lat,
        "longitude": lon,
        "altitude": altitude
    }
    
    import json
    location_json = json.dumps(location_info, ensure_ascii=False)
    
    url = f"{PPTSIGN['URL']}?enc={enc}&name={name}&activeId={active_id}&uid={cookies.get('_uid', '')}&clientip=&location={location_json}&latitude=-1&longitude=-1&fid={fid}&appType=15"
    
    # 对URL进行编码
    import urllib.parse
    encoded_url = urllib.parse.quote(url, safe=':/?&=')
    
    result = request(
        encoded_url,
        {
            'headers': {
                'Cookie': cookie_serialize(cookies),
            },
        }
    )
    
    msg = '[二维码]签到成功' if result['data'] == 'success' else f"[二维码]{result['data']}"
    print(msg)
    return msg 

def handle_qrcode_sign(params, activity, configs, name):
    """处理二维码签到，包括用户交互"""
    enc = input("enc(微信或其他识别二维码，可得enc参数): ")
    
    default_lng_lat = f"{configs.get('monitor', {}).get('lon', '113.516288')},{configs.get('monitor', {}).get('lat', '34.817038')}"
    default_address = configs.get('monitor', {}).get('address', '北京市海淀区双清路清华大学')
    
    lnglat = input(f"经纬度 [{default_lng_lat}]: ") or default_lng_lat
    address = input(f"详细地址 [{default_address}]: ") or default_address
    altitude = input("海拔 [100]: ") or "100"
    
    lat = lnglat.split(',')[1]
    lon = lnglat.split(',')[0]
    
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