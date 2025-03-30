from configs.api import GESTURE_SIGN, PPTSIGN
from utils.request import request_manager
from utils.debug import is_debug_mode, debug_print
import json

def handle_gesture_sign(params, activity, name):
    """
    处理手势签到
    
    签到流程：
    1. 先验证手势码是否正确
    2. 执行实际签到
    3. 如果签到失败，尝试使用通用签到API
    """
    active_id = activity['activeId']
    sign_code = params.get('signCode', '')
    
    if is_debug_mode():
        debug_print(f"处理手势签到: 用户={name}, 手势码={sign_code}, 活动ID={active_id}", "blue")
    
    # 设置临时cookies
    cookies = {k: v for k, v in params.items() if k not in ['name', 'activeId', 'signCode']}
    if cookies:
        request_manager.set_cookies(cookies)
        if is_debug_mode():
            debug_print(f"设置临时cookies: {cookies}", "blue")
    
    # 第一步：验证手势码
    check_url = GESTURE_SIGN['CHECK_SIGN_CODE']['URL']
    
    if is_debug_mode():
        debug_print(f"验证手势码 - URL: {check_url}, 方法: POST, 数据: activeId={active_id}, signCode={sign_code}", "blue")
    
    check_result = request_manager.request(
        check_url, 
        {
            'scenario': 'activity',
            'method': 'POST',
            'debug': True
        },
        {
            "activeId": active_id,
            "signCode": sign_code
        }
    )
    
    if is_debug_mode():
        debug_print(f"验证手势码 - 状态码: {check_result.get('statusCode')}, 响应: {check_result.get('data')}", "blue")
    
    try:
        check_result_data = json.loads(check_result['data'])
        if check_result_data.get('result') != 1:
            error_msg = check_result_data.get('errorMsg', '未知错误')
            if is_debug_mode():
                debug_print(f"手势验证失败: {error_msg}", "red")
            return f"[手势]验证失败: {error_msg}"
    except json.JSONDecodeError:
        if is_debug_mode():
            debug_print(f"手势验证失败: 返回数据格式错误, 原始数据: {check_result.get('data')}", "red")
        return "[手势]验证失败: 返回数据格式错误"
    
    # 第二步：执行实际签到
    sign_url = f"{GESTURE_SIGN['SIGN_IN']['URL']}?activeId={active_id}&signCode={sign_code}&validate=&moreClassAttendEnc="
    
    if is_debug_mode():
        debug_print(f"执行签到 - URL: {sign_url}, 方法: GET", "blue")
        debug_print(f"当前cookies: {request_manager.get_cookies()}", "blue")
    
    try:
        # 使用正确的GET方法和URL参数
        sign_result = request_manager.request(
            sign_url,
            {
                'scenario': 'activity',
                'method': 'GET',
                'debug': True
            }
        )
        
        if is_debug_mode():
            debug_print(f"执行签到 - 状态码: {sign_result.get('statusCode')}, 响应: {sign_result.get('data')}", "blue")
        
        try:
            sign_result_data = json.loads(sign_result['data'])
            if sign_result_data.get('result') == 1:
                msg = f"[手势]签到成功：{name}"
                if is_debug_mode():
                    debug_print(f"手势签到结果: 成功", "green")
            else:
                error_msg = sign_result_data.get('errorMsg', '未知错误')
                msg = f"[手势]签到失败：{error_msg}"
                if is_debug_mode():
                    debug_print(f"手势签到结果: {error_msg}", "red")
        except json.JSONDecodeError:
            if is_debug_mode():
                debug_print(f"签到失败: 返回数据格式错误, 原始数据: {sign_result.get('data')}", "red")
            
            # 解析JSON失败，尝试使用通用签到API
            if is_debug_mode():
                debug_print(f"JSON解析失败，尝试使用通用签到API", "yellow")
            
            # 使用通用签到API尝试
            common_sign_url = f"{PPTSIGN['URL']}?activeId={active_id}&uid={cookies.get('_uid', '')}&clientip=&latitude=-1&longitude=-1&appType=15&fid={params.get('fid', '-1')}&name={name}&signCode={sign_code}"
            
            if is_debug_mode():
                debug_print(f"尝试通用签到 - URL: {common_sign_url}", "blue")
            
            sign_result = request_manager.request(
                common_sign_url,
                {
                    'scenario': 'activity',
                    'debug': True
                }
            )
            
            # 处理结果
            if sign_result['data'] == 'success':
                msg = f"[手势]签到成功：{name}"
                if is_debug_mode():
                    debug_print(f"通用API手势签到结果: 成功", "green")
            else:
                msg = f"[手势]签到失败：{sign_result['data']}"
                if is_debug_mode():
                    debug_print(f"通用API手势签到结果: {sign_result['data']}", "red")
    except Exception as e:
        if is_debug_mode():
            debug_print(f"签到请求异常: {str(e)}", "red")
        msg = f"[手势]签到失败：请求异常 - {str(e)}"
    
    print(msg)
    return msg 