from configs.api import CHAT_GROUP, PPTSIGN
from utils.request import request, cookie_serialize

def general_sign(args):
    """
    通用签到
    
    Args:
        args: 包含活动ID、用户名和用户凭证的字典
    
    Returns:
        str: 签到结果消息
    """
    name = args.get('name', '')
    active_id = args.get('activeId', '')
    fid = args.get('fid', '')
    cookies = {k: v for k, v in args.items() if k not in ['name', 'activeId', 'fid']}
    
    url = f"{PPTSIGN['URL']}?activeId={active_id}&uid={cookies.get('_uid', '')}&clientip=&latitude=-1&longitude=-1&appType=15&fid={fid}&name={name}"
    result = request(
        url, 
        {
            'headers': {
                'Cookie': cookie_serialize(cookies),
            },
        }
    )
    
    msg = '[通用]签到成功' if result['data'] == 'success' else f"[通用]{result['data']}"
    print(msg)
    return msg

def general_sign_2(args):
    """
    群聊签到方式，无课程
    
    Args:
        args: 包含活动ID和用户凭证的字典
    
    Returns:
        str: 签到结果消息
    """
    active_id = args.get('activeId', '')
    cookies = {k: v for k, v in args.items() if k != 'activeId'}
    
    url = f"{CHAT_GROUP['SIGN']['URL']}?activeId={active_id}&uid={cookies.get('_uid', '')}&clientip="
    result = request(
        url,
        {
            'headers': {
                'Cookie': cookie_serialize(cookies),
            },
        }
    )
    
    msg = '[通用]签到成功' if result['data'] == 'success' else f"[通用]{result['data']}"
    print(msg)
    return msg

def handle_general_sign(params, activity, name):
    """处理一般签到"""
    return general_sign({
        **params, 
        'activeId': activity['activeId'], 
        'name': name,
        'fid': params.get('fid', '-1')
    })

def handle_gesture_sign(params, activity, name):
    """处理手势签到"""
    return handle_general_sign(params, activity, name)

def handle_code_sign(params, activity, name):
    """处理签到码签到"""
    return handle_general_sign(params, activity, name) 