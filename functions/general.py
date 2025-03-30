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
    
    sign_code = params.get('signCode', '')
    active_id = activity.get('activeId', '')
    
    if not sign_code:
        if is_debug_mode():
            debug_print("手势签到失败: 没有提供手势码", "red")
        return "[手势]签到失败：未提供手势码"
    
    # 验证手势码
    cookies = {k: v for k, v in params.items() if k not in ['name', 'activeId']}
    
    # 设置临时cookies
    if cookies:
        request_manager.set_cookies(cookies)
    
    # 验证签到码
    check_url = f"https://mobilelearn.chaoxing.com/widget/sign/pcStuSignController/checkSignCode?activeId={active_id}&signCode={sign_code}"
    check_result = request_manager.request(
        check_url,
        {
            'scenario': 'activity',
        }
    )
    
    # 检查验证结果
    if check_result.get('result') != 1:
        error_msg = check_result.get('errorMsg', '手势码验证失败')
        if is_debug_mode():
            debug_print(f"手势签到失败: {error_msg}", "red")
        return f"[手势]{error_msg}"
    
    # 验证通过，执行签到
    sign_args = {
        **params,
        'activeId': active_id,
        'name': name,
        'fid': params.get('fid', '-1'),
        'signCode': sign_code
    }
    
    return general_sign(sign_args)

def handle_code_sign(params, activity, name):
    """处理签到码签到"""
    if is_debug_mode():
        debug_print(f"处理签到码签到: 用户={name}", "blue")
    
    sign_code = params.get('signCode', '')
    active_id = activity.get('activeId', '')
    
    if not sign_code:
        if is_debug_mode():
            debug_print("签到码签到失败: 没有提供签到码", "red")
        return "[签到码]签到失败：未提供签到码"
    
    # 验证签到码
    cookies = {k: v for k, v in params.items() if k not in ['name', 'activeId']}
    
    # 设置临时cookies
    if cookies:
        request_manager.set_cookies(cookies)
    
    # 验证签到码
    check_url = f"https://mobilelearn.chaoxing.com/widget/sign/pcStuSignController/checkSignCode?activeId={active_id}&signCode={sign_code}"
    check_result = request_manager.request(
        check_url,
        {
            'scenario': 'activity',
        }
    )
    
    # 检查验证结果
    if check_result.get('result') != 1:
        error_msg = check_result.get('errorMsg', '签到码验证失败')
        if is_debug_mode():
            debug_print(f"签到码签到失败: {error_msg}", "red")
        return f"[签到码]{error_msg}"
    
    # 验证通过，执行签到
    sign_args = {
        **params,
        'activeId': active_id,
        'name': name,
        'fid': params.get('fid', '-1'),
        'signCode': sign_code
    }
    
    return general_sign(sign_args) 