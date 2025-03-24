from configs.api import CHAT_GROUP, PPTSIGN
from utils.request import request, cookie_serialize
from utils.helper import delay, colored_print

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
        
        url = f"{PPTSIGN['URL']}?name={name}&address={address}&activeId={active_id}&uid={cookies.get('_uid', '')}&clientip=&latitude={lat}&longitude={lon}&fid={fid}&appType=15&ifTiJiao=1"
        result = request(
            url,
            {
                'headers': {
                    'Cookie': cookie_serialize(cookies),
                },
            }
        )
        
        msg = '[位置]签到成功' if result['data'] == 'success' else f"[位置]{result['data']}"
    else:
        # 多个位置尝试
        name = args.get('name', '')
        active_id = args.get('activeId', '')
        preset_address = args.get('presetAddress', [])
        fid = args.get('fid', '')
        cookies = {k: v for k, v in args.items() if k not in ['name', 'activeId', 'presetAddress', 'fid']}
        
        for address_item in preset_address:
            url = f"{PPTSIGN['URL']}?name={name}&address={address_item['address']}&activeId={active_id}&uid={cookies.get('_uid', '')}&clientip=&latitude={address_item['lat']}&longitude={address_item['lon']}&fid={fid}&appType=15&ifTiJiao=1"
            result = request(
                url,
                {
                    'headers': {
                        'Cookie': cookie_serialize(cookies),
                    },
                }
            )
            
            if result['data'] == 'success':
                msg = '[位置]签到成功'
                break
            else:
                msg = f"[位置]{result['data']}"
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
        
        formdata = f"address={address}&activeId={active_id}&uid={cookies.get('_uid', '')}&clientip=&useragent=&latitude={lat}&longitude={lon}&fid=&ifTiJiao=1"
        result = request(
            CHAT_GROUP['SIGN']['URL'],
            {
                'method': 'POST',
                'headers': {
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'Cookie': cookie_serialize(cookies),
                },
            },
            formdata
        )
        
        msg = '[位置]签到成功' if result['data'] == 'success' else f"[位置]{result['data']}"
    else:
        # 多个位置尝试
        active_id = args.get('activeId', '')
        preset_address = args.get('presetAddress', [])
        cookies = {k: v for k, v in args.items() if k not in ['activeId', 'presetAddress']}
        
        for address_item in preset_address:
            formdata = f"address={address_item['address']}&activeId={active_id}&uid={cookies.get('_uid', '')}&clientip=&useragent=&latitude={address_item['lat']}&longitude={address_item['lon']}&fid=&ifTiJiao=1"
            result = request(
                CHAT_GROUP['SIGN']['URL'],
                {
                    'method': 'POST',
                    'headers': {
                        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                        'Cookie': cookie_serialize(cookies),
                    },
                },
                formdata
            )
            
            if result['data'] == 'success':
                msg = '[位置]签到成功'
                break
            else:
                msg = f"[位置]{result['data']}"
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
            'title': f"{address['lon']},{address['lat']}/{address['address']}",
            'value': i,
        })
    
    choices.append({'title': '手动添加', 'value': -1})
    return choices

def handle_location_sign(params, activity, configs, name):
    """处理位置签到，包括用户交互"""
    import sys
    import re

    colored_print("[获取经纬度]https://api.map.baidu.com/lbsapi/getpoint/index.html", "blue")
    
    preset_address = configs.get('monitor', {}).get('presetAddress', [])
    
    # 打印预设地址列表
    choices = preset_address_choices(preset_address)
    colored_print("选择地址:", "blue")
    for i, choice in enumerate(choices):
        print(f"{i+1}. {choice['title']}")
    
    choice = input("请输入选项编号: ")
    try:
        preset_item = choices[int(choice) - 1]['value']
    except (ValueError, IndexError):
        colored_print("无效选择，退出程序", "red")
        sys.exit(1)
    
    if preset_item == -1:
        # 手动添加
        lon_lat_address = input("位置参数预设（经纬度/地址）[116.333585,40.008944/北京市海淀区双清路清华大学]: ") or "116.333585,40.008944/北京市海淀区双清路清华大学"
        
        match = re.match(r'([\d.]*),([\d.]*)\/(\S*)', lon_lat_address)
        if match:
            address_item = {
                'lon': match.group(1),
                'lat': match.group(2),
                'address': match.group(3)
            }
            
            # 添加到预设地址
            if not configs.get('monitor'):
                configs['monitor'] = {}
            if not configs['monitor'].get('presetAddress'):
                configs['monitor']['presetAddress'] = []
            
            configs['monitor']['presetAddress'].append(address_item)
        else:
            colored_print("地址格式错误，退出程序", "red")
            sys.exit(1)
    else:
        # 选取地址
        address_item = preset_address[preset_item]
    
    # 执行位置签到
    return location_sign({
        **params, 
        **address_item, 
        'activeId': activity['activeId'], 
        'name': name,
        'fid': params.get('fid', '-1')
    }), configs 