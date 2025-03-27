import re
import os
import json
import tempfile
import time

from configs.api import CHAT_GROUP, PANCHAOXING, PANLIST, PANUPLOAD, PPTSIGN
from utils.request import request, cookie_serialize, request_manager
from utils.debug import is_debug_mode, debug_print

def photo_sign(args):
    """
    拍照签到
    
    Args:
        args: 包含活动ID、对象ID、用户名和用户凭证的字典
    
    Returns:
        str: 签到结果消息
    """
    name = args.get('name', '')
    active_id = args.get('activeId', '')
    fid = args.get('fid', '')
    object_id = args.get('objectId', '')
    cookies = {k: v for k, v in args.items() if k not in ['name', 'activeId', 'fid', 'objectId']}
    
    if is_debug_mode():
        debug_print(f"执行拍照签到: activeId={active_id}, name={name}", "blue")
    
    # 使用统一的configs中的0.jpg
    if not object_id:
        if is_debug_mode():
            debug_print("未提供对象ID，尝试上传照片", "blue")
        object_id = upload_configs_photo(cookies)
        if not object_id:
            if is_debug_mode():
                debug_print("上传照片失败", "red")
            return "[拍照]签到失败：无法上传照片"
        if is_debug_mode():
            debug_print(f"照片上传成功，对象ID: {object_id}", "green")
    
    url = f"{PPTSIGN['URL']}?activeId={active_id}&uid={cookies.get('_uid', '')}&clientip=&useragent=&latitude=-1&longitude=-1&appType=15&fid={fid}&objectId={object_id}&name={name}"
    
    # 设置临时cookies
    if cookies:
        request_manager.set_cookies(cookies)
        
    result = request_manager.request(
        url,
        {
            'scenario': 'activity',
        }
    )
    
    msg = '[拍照]签到成功' if result['data'] == 'success' else f"[拍照]{result['data']}"
    print(msg)
    
    if is_debug_mode():
        debug_print(f"拍照签到结果: {result['data']}", "green" if result['data'] == 'success' else "red")
    
    return msg

def photo_sign_2(args):
    """
    拍照签到，无课程群聊版本
    
    Args:
        args: 包含活动ID、对象ID和用户凭证的字典
    
    Returns:
        str: 签到结果消息
    """
    active_id = args.get('activeId', '')
    object_id = args.get('objectId', '')
    cookies = {k: v for k, v in args.items() if k not in ['activeId', 'objectId']}
    
    # 使用统一的configs中的0.jpg
    if not object_id:
        object_id = upload_configs_photo(cookies)
        if not object_id:
            return "[拍照]签到失败：无法上传照片"
    
    url = f"{CHAT_GROUP['SIGN']['URL']}?activeId={active_id}&uid={cookies.get('_uid', '')}&clientip=&useragent=&latitude=-1&longitude=-1&fid=0&objectId={object_id}"
    
    # 设置临时cookies
    if cookies:
        request_manager.set_cookies(cookies)
        
    result = request_manager.request(
        url,
        {
            'scenario': 'activity',
        }
    )
    
    msg = '[拍照]签到成功' if result['data'] == 'success' else f"[拍照]{result['data']}"
    print(msg)
    return msg

def get_object_id_from_cx_pan(cookies):
    """
    从超星云盘获取图片对象ID（已弃用）
    
    Args:
        cookies: 用户凭证
    
    Returns:
        str: 对象ID，如果未找到则返回None
    """
    # 该函数已弃用，调用upload_configs_photo函数替代
    return upload_configs_photo(cookies)

def upload_configs_photo(cookies):
    """
    上传configs目录中的0.jpg到超星云盘
    
    Args:
        cookies: 用户凭证
    
    Returns:
        str: 对象ID，如果上传失败则返回None
    """
    if is_debug_mode():
        debug_print("开始上传照片", "blue")
    
    # 获取configs目录中的0.jpg文件路径
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    configs_photo_path = os.path.join(current_dir, 'configs', '0.jpg')
    
    if not os.path.exists(configs_photo_path):
        print('未找到configs目录中的0.jpg文件')
        if is_debug_mode():
            debug_print(f"未找到照片文件: {configs_photo_path}", "red")
        return None
    
    if is_debug_mode():
        debug_print(f"找到照片文件: {configs_photo_path}", "blue")
    
    # 设置临时cookies
    if cookies:
        request_manager.set_cookies(cookies)
    
    # 获取token用于上传
    if is_debug_mode():
        debug_print("获取上传Token", "blue")
        
    result = request_manager.request(
        PANCHAOXING['URL'],
        {
            'headers': {
                'Referer': 'https://i.chaoxing.com/',
            },
        }
    )
    
    data = result['data']
    
    # 使用正则表达式提取token
    token_match = re.search(r'token\s*=\s*"([^"]+)"', data)
    
    if not token_match:
        print('获取上传token失败')
        if is_debug_mode():
            debug_print("获取上传Token失败", "red")
        return None
    
    token = token_match.group(1)
    
    if is_debug_mode():
        debug_print(f"获取上传Token成功: {token[:10]}...", "green")
    
    # 读取图片文件
    with open(configs_photo_path, 'rb') as f:
        file_data = f.read()
    
    if is_debug_mode():
        debug_print(f"读取照片文件成功，大小: {len(file_data)} 字节", "blue")
    
    # 上传图片
    if is_debug_mode():
        debug_print("开始上传照片", "blue")
        
    upload_result = upload_photo({'token': token, 'buffer': file_data, **cookies})
    
    try:
        result_json = json.loads(upload_result)
        if result_json.get('result') == 1:
            # 返回对象ID
            object_id = result_json.get('objectId')
            if is_debug_mode():
                debug_print(f"照片上传成功，对象ID: {object_id}", "green")
            return object_id
    except Exception as e:
        print(f"解析上传结果出错: {e}")
        if is_debug_mode():
            debug_print(f"解析上传结果出错: {e}", "red")
    
    print('上传照片失败，请检查网络或账号状态')
    if is_debug_mode():
        debug_print("上传照片失败", "red")
    return None

def upload_photo(args):
    """
    上传照片到超星云盘
    
    Args:
        args: 包含图片数据、token和用户凭证的字典
    
    Returns:
        str: 上传结果
    """
    token = args.get('token', '')
    buffer = args.get('buffer', b'')
    cookies = {k: v for k, v in args.items() if k not in ['token', 'buffer']}
    
    if is_debug_mode():
        debug_print(f"准备上传照片，Token: {token[:10]}..., 数据大小: {len(buffer)} 字节", "blue")
    
    # 创建临时文件
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
    temp_file.write(buffer)
    temp_file.close()
    
    if is_debug_mode():
        debug_print(f"创建临时文件: {temp_file.name}", "blue")
    
    try:
        import requests
        
        # 准备表单数据
        file_obj = None
        response = None
        try:
            file_obj = open(temp_file.name, 'rb')
            files = {
                'file': ('1.png', file_obj, 'image/png')
            }
            data = {
                'puid': cookies.get('_uid', '')
            }
            
            if is_debug_mode():
                debug_print(f"上传请求信息: URL={PANUPLOAD['URL']}, PUID={data['puid']}", "blue")
            
            # 发送请求
            response = requests.post(
                f"{PANUPLOAD['URL']}?_from=mobilelearn&_token={token}",
                files=files,
                data=data,
                headers={
                    'Cookie': cookie_serialize(cookies)
                }
            )
            
            if is_debug_mode():
                debug_print(f"上传响应状态码: {response.status_code}", "blue")
            
            if response.status_code == 200:
                return response.text
            else:
                if is_debug_mode():
                    debug_print(f"上传失败，响应: {response.text}", "red")
                return json.dumps({'result': 0, 'msg': f"上传失败，状态码: {response.status_code}"})
        except Exception as e:
            if is_debug_mode():
                debug_print(f"上传过程发生异常: {e}", "red")
            return json.dumps({'result': 0, 'msg': f"上传异常: {str(e)}"})
        finally:
            if file_obj:
                file_obj.close()
    finally:
        # 删除临时文件
        try:
            os.remove(temp_file.name)
            if is_debug_mode():
                debug_print(f"删除临时文件: {temp_file.name}", "blue")
        except:
            pass
    
    return json.dumps({'result': 0, 'msg': '上传失败'})

def handle_photo_sign(params, activity, name):
    """处理拍照签到"""
    if is_debug_mode():
        debug_print(f"处理拍照签到: 活动ID={activity['activeId']}, 用户={name}", "blue")
    
    # 检查configs目录中是否有0.jpg
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    configs_dir = os.path.join(current_dir, 'configs')
    photo_path = os.path.join(configs_dir, '0.jpg')
    
    if not os.path.exists(photo_path):
        if is_debug_mode():
            debug_print(f"未找到签到照片: {photo_path}", "yellow")
        
        # 确保configs目录存在
        os.makedirs(configs_dir, exist_ok=True)
        
        print("未找到拍照签到照片，请将照片命名为0.jpg放置在configs目录中")
        print(f"照片路径: {photo_path}")
        exit(0)
    
    if is_debug_mode():
        debug_print(f"找到签到照片: {photo_path}", "green")
    
    return photo_sign({
        **params, 
        'activeId': activity['activeId'], 
        'name': name,
        'fid': params.get('fid', '-1')
    }) 