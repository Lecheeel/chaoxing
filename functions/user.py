import re
import base64
import json
from Crypto.Cipher import DES
from Crypto.Util.Padding import pad
import requests

from configs.api import LOGIN, COURSELIST, ACCOUNTMANAGE, PANTOKEN, LOGIN_PAGE
from utils.request import request, cookie_serialize, get_session_cookies, clear_session, _session
from utils.file import get_json_object

# 默认参数
DEFAULT_PARAMS = {
    'fid': '-1',
    'pid': '-1',
    'refer': 'http%3A%2F%2Fi.chaoxing.com',
    '_blank': '1',
    't': True,
    'vc3': '',
    '_uid': '',
    '_d': '',
    'uf': '',
    'lv': '',
}

def user_login(uname, password):
    """
    用户登录
    
    Args:
        uname: 用户名/手机号
        password: 密码
    
    Returns:
        dict/str: 登录成功返回用户信息，失败返回错误信息
    """
    try:
        # 清除之前的会话
        clear_session()
        
        # 1. 先访问登录页面获取初始cookie
        print("正在获取登录页面...")
        init_result = request(
            LOGIN_PAGE['URL'],
            {
                'method': LOGIN_PAGE['METHOD'],
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'Accept-Language': 'zh-CN,zh;q=0.9',
                }
            }
        )
        
        if init_result['statusCode'] != 200:
            print("获取登录页面失败")
            return 'AuthFailed'
            
        # 密码加密 - 模拟原始CryptoJS实现
        key = b'u2oh6Vu^HWe40fj'
        # 截取前8个字节作为DES密钥
        des_key = key[:8]
        cipher = DES.new(des_key, DES.MODE_ECB)
        # 对齐数据
        padded_data = pad(password.encode(), 8)
        encrypted_bytes = cipher.encrypt(padded_data)
        # 转换为十六进制字符串
        hex_str = encrypted_bytes.hex()
        print("password:", hex_str)
        
        # 构建登录表单
        formdata = f"uname={uname}&password={hex_str}&fid=-1&t=true&refer=https%253A%252F%252Fi.chaoxing.com&forbidotherlogin=0&validate="
        
        # 发送登录请求
        print("正在登录...")
        result = request(
            LOGIN['URL'],
            {
                'method': LOGIN['METHOD'],
                'headers': {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Origin': 'https://passport2.chaoxing.com',
                    'Referer': LOGIN_PAGE['URL'],
                },
            },
            formdata
        )
        
        # 尝试解析JSON响应
        try:
            response_data = result['data']
            response_json = json.loads(response_data)
            
            if response_json.get('status'):
                # 如果响应中有重定向URL，跟随重定向获取完整cookie
                if 'url' in response_json.get('data', {}):
                    redirect_url = response_json['data']['url']
                    print(f"跟随登录重定向...")
                    redirect_result = request(redirect_url, {'method': 'GET'})
                
                # 获取session中的cookie
                session_cookies = get_session_cookies()
                
                # 检查必须的cookie是否存在
                required_cookies = ['_uid', '_d', 'vc3']
                missing_cookies = [c for c in required_cookies if c not in session_cookies]
                
                if missing_cookies:
                    # 尝试从JSON响应中补充缺失的cookie
                    data = response_json.get('data', {})
                    
                    if '_uid' in missing_cookies and 'uid' in data:
                        session_cookies['_uid'] = str(data.get('uid'))
                    
                    if '_d' in missing_cookies and '_d' in data:
                        session_cookies['_d'] = data.get('_d')
                    
                    if 'vc3' in missing_cookies and 'vc3' in data:
                        session_cookies['vc3'] = data.get('vc3')
                    
                    # 再次检查
                    missing_cookies = [c for c in required_cookies if c not in session_cookies]
                    
                    if missing_cookies:
                        print(f"登录信息不完整，缺少以下cookie: {', '.join(missing_cookies)}")
                        print("请检查账号密码是否正确，或尝试使用其他登录方式")
                        return 'AuthFailed'
                
                print("登录成功")
                login_result = {**DEFAULT_PARAMS, **session_cookies}
                return login_result
            else:
                # 登录失败，可能是用户名密码错误
                print(f"登录失败: {response_json.get('msg', '未知错误')}")
                return 'AuthFailed'
                
        except json.JSONDecodeError:
            print("登录响应格式异常，正在检查登录状态...")
            
            # 获取session中的cookie
            session_cookies = get_session_cookies()
            
            # 检查必须的cookie是否存在
            required_cookies = ['_uid', '_d', 'vc3']
            missing_cookies = [c for c in required_cookies if c not in session_cookies]
            
            if missing_cookies:
                print(f"登录信息不完整，缺少以下cookie: {', '.join(missing_cookies)}")
                return 'AuthFailed'
            
            print("登录成功")
            login_result = {**DEFAULT_PARAMS, **session_cookies}
            return login_result
            
    except Exception as e:
        print(f"登录解析出错: {e}")
    
    print("登录失败")
    return 'AuthFailed'

def get_courses(_uid, _d, vc3):
    """
    获取所有课程
    
    Args:
        _uid: 用户ID
        _d: 用户凭证
        vc3: 验证码
    
    Returns:
        list/str: 课程列表或错误信息
    """
    try:
        # 确保登录信息设置到cookie中
        cookies = {
            '_uid': _uid,
            '_d': _d,
            'vc3': vc3
        }
        
        print("正在获取课程列表...")
        formdata = 'courseType=1&courseFolderId=0&courseFolderSize=0'
        result = request(
            COURSELIST['URL'],
            {
                'gzip': False,  # 改为False，手动处理解压
                'method': COURSELIST['METHOD'],
                'cookies': cookies,  # 显式传递cookie
                'headers': {
                    'Accept': 'text/html, */*; q=0.01',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8;',
                    'Referer': 'https://mooc1-1.chaoxing.com/visit/interaction',
                    'Origin': 'https://mooc1-1.chaoxing.com'
                },
            },
            formdata
        )
        
        if result['statusCode'] == 302:
            print('身份过期，请使用手动填写用户名密码的方式登录！')
            return 'AuthFailed'
        
        # 获取响应内容
        data = result['data']
        
        # 如果响应内容包含错误信息，可能是登录已过期
        if '请重新登录' in data or '登录超时' in data:
            print('登录信息已过期，请重新登录')
            return 'AuthFailed'
        
        # 从HTML页面内容解析出所有courseId和classId
        courses = []
        
        # 使用正则表达式匹配课程ID和班级ID
        pattern = r'course_(\d+)_(\d+)'
        matches = re.finditer(pattern, data)
        
        for match in matches:
            courses.append({
                'courseId': match.group(1),
                'classId': match.group(2),
            })
        
        if not courses:
            print('无课程可查')
            return 'NoCourse'
        
        print(f"找到 {len(courses)} 门课程")
        return courses
    except Exception as e:
        print(f"获取课程列表失败: {e}")
        return 'GetCoursesFailed'

def get_account_info(cookies):
    """
    获取用户名
    
    Args:
        cookies: 用户凭证
    
    Returns:
        str: 用户名
    """
    try:
        print("正在获取用户信息...")
        print("cookies:", cookies)
        
        # 检查cookies参数，确保它是字典类型且包含必要的值
        if not isinstance(cookies, dict):
            print("cookies不是字典类型")
            return "未知用户"
            
        if '_uid' not in cookies or '_d' not in cookies:
            print("cookies中缺少必要的参数")
            return "未知用户"
        
        # 预处理cookies，确保所有值都是字符串类型
        processed_cookies = {}
        for key, value in cookies.items():
            if isinstance(value, bool):
                processed_cookies[key] = "true" if value else "false"
            else:
                processed_cookies[key] = str(value)
        
        # 使用request函数发送请求，它会自动使用_session并管理cookie
        result = request(
            ACCOUNTMANAGE['URL'], 
            {
                'method': ACCOUNTMANAGE['METHOD'],
                'cookies': processed_cookies,  # 使用处理后的cookies
                'headers': {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Referer': 'https://i.chaoxing.com/',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                },
            }
        )
        print("请求完成")
        print("结果状态码:", result['statusCode'])
        
        if result['statusCode'] != 200:
            print(f"获取用户信息失败，状态码: {result['statusCode']}")
            return "未知用户"
        
        # 获取响应数据
        data = result.get('data', '')
        
        # 处理不同类型的响应数据
        if isinstance(data, bytes):
            try:
                print("返回原始数据(bytes)：", data.decode('utf-8'))
                data = data.decode('utf-8')
            except UnicodeDecodeError:
                print("无法解码响应数据")
                return "未知用户"
        else:
            print(f"返回原始数据({type(data).__name__})：", data)
            if isinstance(data, bool):
                return "未知用户"  # 布尔值无法提取用户名，直接返回
        
        print("响应头:", result.get('headers', {}))
        
        # 确保data是字符串类型
        if not isinstance(data, str):
            try:
                data = str(data)
            except:
                return "未知用户"
                
        # 防止data是None或布尔值
        if data is None or isinstance(data, bool):
            return "未知用户"
        
        # 输出session cookies用于调试
        print(f"当前session cookies: {get_session_cookies()}")
        
        # 从HTML内容中提取用户名
        try:
            # 尝试提取用户名，参考TypeScript版本的实现
            end_of_messageName = data.find('messageName') + 20
            if end_of_messageName > 20:  # 确保找到了messageName
                name = data[end_of_messageName:data.find('"', end_of_messageName)]
                if name:
                    return name
            
            # 尝试其他可能的提取方式
            username_match = re.search(r'用户名：.*?>(.*?)<', data)
            if username_match:
                return username_match.group(1)
            
            # 如果都找不到，返回未知用户
            return "未知用户"
        except Exception as e:
            print(f"解析用户名失败: {e}")
            return "未知用户"
    except Exception as e:
        print(f"获取用户名出错: {e}")
        return "未知用户"

def get_pan_token(cookies):
    """
    获取用户鉴权token
    
    Args:
        cookies: 用户凭证
    
    Returns:
        str: 鉴权token
    """
    try:
        # 使用request函数发送请求，自动使用session管理cookie
        result = request(
            PANTOKEN['URL'], 
            {
                'method': 'GET',
                'cookies': cookies,  # 显式传递cookie
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Referer': 'https://i.chaoxing.com/'
                }
            }
        )
        
        # 验证返回的数据类型
        if result['statusCode'] != 200:
            print(f"获取用户鉴权token失败, 状态码: {result['statusCode']}")
            return ""
            
        data = result.get('data')
        if data is None:
            print("获取用户鉴权token失败: 无数据返回")
            return ""
            
        if not isinstance(data, str):
            print(f"获取用户鉴权token返回了非字符串数据: {type(data)}")
            try:
                data = str(data)
            except:
                return ""
                
        return data
    except Exception as e:
        print(f"获取用户鉴权token出错: {e}")
        return ""

def get_local_users():
    """
    返回用户列表
    
    Returns:
        list: 用户列表
    """
    data = get_json_object('configs/storage.json')
    users = []
    
    for i, user in enumerate(data.get('users', [])):
        # 优先使用username，如果不存在则使用phone，最后使用默认名
        display_name = user.get('username', user.get('phone', f'用户{i+1}'))
        users.append({
            'title': display_name,
            'value': i,
        })
    
    users.append({'title': '手动登录', 'value': -1})
    return users 