import re
import os
import json
import tempfile
import time

from configs.api import CHAT_GROUP, PANCHAOXING, PANLIST, PANUPLOAD, PPTSIGN
from utils.request import request, cookie_serialize

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
    
    # 使用统一的configs中的0.jpg
    if not object_id:
        object_id = upload_configs_photo(cookies)
        if not object_id:
            return "[拍照]签到失败：无法上传照片"
    
    url = f"{PPTSIGN['URL']}?activeId={active_id}&uid={cookies.get('_uid', '')}&clientip=&useragent=&latitude=-1&longitude=-1&appType=15&fid={fid}&objectId={object_id}&name={name}"
    result = request(
        url,
        {
            'headers': {
                'Cookie': cookie_serialize(cookies),
            },
        }
    )
    
    msg = '[拍照]签到成功' if result['data'] == 'success' else f"[拍照]{result['data']}"
    print(msg)
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
    result = request(
        url,
        {
            'headers': {
                'Cookie': cookie_serialize(cookies),
            },
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
    # 获取configs目录中的0.jpg文件路径
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    configs_photo_path = os.path.join(current_dir, 'configs', '0.jpg')
    
    if not os.path.exists(configs_photo_path):
        print('未找到configs目录中的0.jpg文件')
        return None
    
    # 获取token用于上传
    result = request(
        PANCHAOXING['URL'],
        {
            'headers': {
                'Cookie': cookie_serialize(cookies),
            },
        }
    )
    
    data = result['data']
    
    # 使用正则表达式提取token
    token_match = re.search(r'token\s*=\s*"([^"]+)"', data)
    
    if not token_match:
        print('获取上传token失败')
        return None
    
    token = token_match.group(1)
    
    # 读取图片文件
    with open(configs_photo_path, 'rb') as f:
        file_data = f.read()
    
    # 上传图片
    upload_result = upload_photo({'token': token, 'buffer': file_data, **cookies})
    
    try:
        result_json = json.loads(upload_result)
        if result_json.get('result') == 1:
            # 返回对象ID
            return result_json.get('objectId')
    except Exception as e:
        print(f"解析上传结果出错: {e}")
    
    print('上传照片失败，请检查网络或账号状态')
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
    
    # 创建临时文件
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
    temp_file.write(buffer)
    temp_file.close()
    
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
            
            # 发送请求
            response = requests.post(
                f"{PANUPLOAD['URL']}?_from=mobilelearn&_token={token}",
                files=files,
                data=data,
                headers={
                    'Cookie': cookie_serialize(cookies)
                }
            )
            
            return response.text
        finally:
            # 确保文件对象被关闭
            if file_obj:
                file_obj.close()
    finally:
        # 延迟一段时间再尝试删除临时文件
        try:
            time.sleep(0.5)  # 延迟半秒
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
        except Exception as e:
            print(f"删除临时文件出错，但不影响签到: {e}") 

def handle_photo_sign(params, activity, name):
    """处理拍照签到，包括用户交互"""
    try:
        from utils.helper import colored_print
    except:
        from utils.helper import colored_print
    import sys
    
    colored_print("访问 https://pan-yz.chaoxing.com 并在根目录上传你想要提交的照片，格式为jpg或png，命名为 0.jpg 或 0.png", "blue")
    input("已上传完毕? 按回车继续...")
    
    # 获取照片objectId
    object_id = get_object_id_from_cx_pan(params)
    if object_id is None:
        sys.exit(1)
    
    return photo_sign({
        **params, 
        'activeId': activity['activeId'], 
        'objectId': object_id, 
        'name': name,
        'fid': params.get('fid', '-1')
    }) 