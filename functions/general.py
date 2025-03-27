from configs.api import CHAT_GROUP, PPTSIGN
from utils.request import request, cookie_serialize, request_manager
from utils.debug import is_debug_mode, debug_print

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
    
    if is_debug_mode():
        debug_print(f"执行通用签到: activeId={active_id}, name={name}", "blue")
    
    # 设置临时cookies
    if cookies:
        request_manager.set_cookies(cookies)
    
    url = f"{PPTSIGN['URL']}?activeId={active_id}&uid={cookies.get('_uid', '')}&clientip=&latitude=-1&longitude=-1&appType=15&fid={fid}&name={name}"
    result = request_manager.request(
        url, 
        {
            'scenario': 'activity',
        }
    )
    
    msg = '[通用]签到成功' if result['data'] == 'success' else f"[通用]{result['data']}"
    print(msg)
    
    if is_debug_mode():
        debug_print(f"通用签到结果: {result['data']}", "green" if result['data'] == 'success' else "red")
    
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
    
    if is_debug_mode():
        debug_print(f"执行群聊签到: activeId={active_id}", "blue")
    
    # 设置临时cookies
    if cookies:
        request_manager.set_cookies(cookies)
    
    url = f"{CHAT_GROUP['SIGN']['URL']}?activeId={active_id}&uid={cookies.get('_uid', '')}&clientip="
    result = request_manager.request(
        url,
        {
            'scenario': 'activity',
        }
    )
    
    msg = '[通用]签到成功' if result['data'] == 'success' else f"[通用]{result['data']}"
    print(msg)
    
    if is_debug_mode():
        debug_print(f"群聊签到结果: {result['data']}", "green" if result['data'] == 'success' else "red")
    
    return msg

def handle_general_sign(params, activity, name):
    """处理一般签到"""
    if is_debug_mode():
        debug_print(f"处理一般签到: 用户={name}", "blue")
    return general_sign({
        **params, 
        'activeId': activity['activeId'], 
        'name': name,
        'fid': params.get('fid', '-1')
    })

def handle_gesture_sign(params, activity, name):
    """处理手势签到"""
    if is_debug_mode():
        debug_print(f"处理手势签到: 用户={name}", "blue")
    return handle_general_sign(params, activity, name)

def handle_code_sign(params, activity, name):
    """处理签到码签到"""
    if is_debug_mode():
        debug_print(f"处理签到码签到: 用户={name}", "blue")
    return handle_general_sign(params, activity, name) 