import re
import base64
import json
from Crypto.Cipher import DES
from Crypto.Util.Padding import pad
import requests

from configs.api import LOGIN, COURSELIST, ACCOUNTMANAGE, PANTOKEN, LOGIN_PAGE
from utils.request import request, cookie_serialize, get_session_cookies, clear_session, _session, request_manager
from utils.file import get_json_object
from utils.debug import is_debug_mode, debug_print

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
        if is_debug_mode():
            debug_print(f"开始用户登录流程，用户名: {uname}", "blue")
        
        # 清除之前的会话
        request_manager.clear_cookies()
        
        # 1. 先访问登录页面获取初始cookie
        print("正在获取登录页面...")
        init_result = request_manager.request(
            LOGIN_PAGE['URL'],
            {
                'method': LOGIN_PAGE['METHOD'],
                'scenario': 'login',
            }
        )
        
        if init_result['statusCode'] != 200:
            error_msg = "获取登录页面失败"
            print(error_msg)
            if is_debug_mode():
                debug_print(f"获取登录页面失败，状态码: {init_result['statusCode']}", "red")
            return {
                'success': False,
                'message': error_msg
            }
            
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
        
        # 构建登录表单
        formdata = f"uname={uname}&password={hex_str}&fid=-1&t=true&refer=https%253A%252F%252Fi.chaoxing.com&forbidotherlogin=0&validate="
        
        # 发送登录请求
        print("正在登录...")
        result = request_manager.request(
            LOGIN['URL'],
            {
                'method': LOGIN['METHOD'],
                'scenario': 'login',
                'headers': {
                    'Referer': LOGIN_PAGE['URL'],
                },
            },
            formdata
        )
        
        # 尝试解析JSON响应
        try:
            response_data = result['data']
            response_json = json.loads(response_data)
            
            if is_debug_mode():
                debug_print(f"登录响应状态: {response_json.get('status')}", "green")
                if 'msg' in response_json:
                    debug_print(f"登录响应消息: {response_json.get('msg')}", "green")
            
            if response_json.get('status'):
                # 如果响应中有重定向URL，跟随重定向获取完整cookie
                if 'url' in response_json.get('data', {}):
                    redirect_url = response_json['data']['url']
                    print(f"跟随登录重定向...")
                    if is_debug_mode():
                        debug_print(f"跟随重定向URL: {redirect_url}", "blue")
                    redirect_result = request_manager.request(redirect_url, {'method': 'GET'})
                
                # 获取session中的cookie
                session_cookies = request_manager.get_cookies()
                
                if is_debug_mode():
                    debug_print(f"获取到的Cookie: {session_cookies}", "green")
                
                # 检查必须的cookie是否存在
                required_cookies = ['_uid', '_d', 'vc3']
                missing_cookies = [c for c in required_cookies if c not in session_cookies]
                
                if missing_cookies:
                    # 尝试从JSON响应中补充缺失的cookie
                    data = response_json.get('data', {})
                    
                    if is_debug_mode():
                        debug_print(f"检测到缺失Cookie: {missing_cookies}，尝试从响应中补充", "blue")
                    
                    if '_uid' in missing_cookies and 'uid' in data:
                        session_cookies['_uid'] = str(data.get('uid'))
                    
                    if '_d' in missing_cookies and '_d' in data:
                        session_cookies['_d'] = data.get('_d')
                    
                    if 'vc3' in missing_cookies and 'vc3' in data:
                        session_cookies['vc3'] = data.get('vc3')
                    
                    # 设置新获取的认证cookie
                    request_manager.set_cookies(session_cookies)
                    
                    # 再次获取，包含新添加的
                    session_cookies = request_manager.get_cookies()
                    
                    if is_debug_mode():
                        debug_print(f"补充后的Cookie: {session_cookies}", "green")
                    
                    # 再次检查
                    missing_cookies = [c for c in required_cookies if c not in session_cookies]
                    
                    if missing_cookies:
                        error_msg = f"登录信息不完整，缺少以下cookie: {', '.join(missing_cookies)}"
                        if is_debug_mode():
                            debug_print(error_msg, "red")
                            debug_print("请检查账号密码是否正确，或尝试使用其他登录方式", "red")
                        return {
                            'success': False,
                            'message': error_msg
                        }
                
                print("登录成功")
                
                # 将认证信息保存到请求管理器
                # 注意：只有实际的cookie字段才设置为cookie
                auth_cookies = {**DEFAULT_PARAMS, **session_cookies}
                request_manager.set_auth_cookies(auth_cookies)
                
                if is_debug_mode():
                    debug_print("登录成功，已保存认证信息", "green")
                
                # 获取用户真实姓名和详细信息
                print("正在获取用户信息...")
                if is_debug_mode():
                    debug_print("开始获取用户详细信息", "blue")
                
                user_params = {**auth_cookies, 'phone': uname, 'password': password}
                real_name = get_account_info(user_params)
                
                if is_debug_mode():
                    debug_print(f"获取到用户真实姓名: {real_name}", "green")
                
                # 返回标准化的成功响应，包含详细的用户信息
                return {
                    'success': True,
                    'message': '登录成功',
                    'cookies': auth_cookies,
                    'user_info': {
                        'username': real_name if real_name != '未知用户' else session_cookies.get('uname', '未知用户'),
                        'real_name': real_name,
                        'uid': session_cookies.get('_uid'),
                        'phone': uname,
                    }
                }
            else:
                # 登录失败，可能是用户名密码错误
                error_msg = response_json.get('msg', '未知错误')
                print(f"登录失败: {error_msg}")
                if is_debug_mode():
                    debug_print(f"登录失败原因: {error_msg}", "red")
                return {
                    'success': False,
                    'message': error_msg
                }
                
        except json.JSONDecodeError:
            print("登录响应格式异常，正在检查登录状态...")
            if is_debug_mode():
                debug_print("登录响应解析JSON失败，尝试检查Cookie状态", "yellow")
            
            # 获取session中的cookie
            session_cookies = request_manager.get_cookies()
            
            # 检查必须的cookie是否存在
            required_cookies = ['_uid', '_d', 'vc3']
            missing_cookies = [c for c in required_cookies if c not in session_cookies]
            
            if missing_cookies:
                error_msg = f"登录信息不完整，缺少以下cookie: {', '.join(missing_cookies)}"
                print(error_msg)
                if is_debug_mode():
                    debug_print(f"登录失败，缺少必要Cookie: {missing_cookies}", "red")
                return {
                    'success': False,
                    'message': error_msg
                }
            
            print("登录成功")
            
            # 将认证信息保存到请求管理器
            # 注意：只有实际的cookie字段才设置为cookie
            auth_cookies = {**DEFAULT_PARAMS, **session_cookies}
            request_manager.set_auth_cookies(auth_cookies)
            
            if is_debug_mode():
                debug_print("登录成功，已保存认证信息", "green")
            
            # 获取用户真实姓名和详细信息
            print("正在获取用户信息...")
            if is_debug_mode():
                debug_print("开始获取用户详细信息", "blue")
            
            user_params = {**auth_cookies, 'phone': uname, 'password': password}
            real_name = get_account_info(user_params)
            
            if is_debug_mode():
                debug_print(f"获取到用户真实姓名: {real_name}", "green")
            
            return {
                'success': True,
                'message': '登录成功',
                'cookies': auth_cookies,
                'user_info': {
                    'username': real_name if real_name != '未知用户' else session_cookies.get('uname', '未知用户'),
                    'real_name': real_name,
                    'uid': session_cookies.get('_uid'),
                    'phone': uname,
                }
            }
            
    except Exception as e:
        error_msg = f"登录解析出错: {e}"
        print(error_msg)
        if is_debug_mode():
            debug_print(f"登录过程发生异常: {e}", "red")
        return {
            'success': False,
            'message': error_msg
        }

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
        if is_debug_mode():
            debug_print(f"开始获取课程列表，用户ID: {_uid}", "blue")
        
        # 确保登录信息设置到cookie中
        cookies = {
            '_uid': _uid,
            '_d': _d,
            'vc3': vc3
        }
        
        print("正在获取课程列表...")
        formdata = 'courseType=1&courseFolderId=0&courseFolderSize=0'
        result = request_manager.request(
            COURSELIST['URL'],
            {
                'gzip': False,  # 改为False，手动处理解压
                'method': COURSELIST['METHOD'],
                'cookies': cookies,  # 显式传递cookie
                'scenario': 'course',
                'headers': {
                    'Referer': 'https://mooc1-1.chaoxing.com/visit/interaction',
                }
            },
            formdata
        )
        
        if result['statusCode'] == 302:
            print('身份过期，请使用手动填写用户名密码的方式登录！')
            if is_debug_mode():
                debug_print("获取课程失败：请求被重定向(302)，身份可能已过期", "red")
            return 'AuthFailed'
        
        # 获取响应内容
        data = result['data']
        
        # 如果响应内容包含错误信息，可能是登录已过期
        if '请重新登录' in data or '登录超时' in data:
            print('登录信息已过期，请重新登录')
            if is_debug_mode():
                debug_print("获取课程失败：响应内容提示需要重新登录", "red")
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
        if is_debug_mode():
            debug_print(f"成功获取课程列表，共 {len(courses)} 门课程", "green")
            for i, course in enumerate(courses):
                debug_print(f"课程 {i+1}: courseId={course['courseId']}, classId={course['classId']}", "green")
        
        return courses
    except Exception as e:
        print(f"获取课程列表失败: {e}")
        if is_debug_mode():
            debug_print(f"获取课程列表过程发生异常: {e}", "red")
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
        if is_debug_mode():
            debug_print("开始获取用户账号信息", "blue")
            print("cookies:", cookies)
        
        # 检查cookies参数，确保它是字典类型且包含必要的值
        if not isinstance(cookies, dict):
            print("cookies不是字典类型")
            if is_debug_mode():
                debug_print("错误：cookies不是字典类型", "red")
            return "未知用户"
            
        if '_uid' not in cookies or '_d' not in cookies:
            print("cookies中缺少必要的参数")
            if is_debug_mode():
                debug_print("错误：cookies中缺少必要参数(_uid或_d)", "red")
            return "未知用户"
        
        # 预处理cookies，确保所有值都是字符串类型
        processed_cookies = {}
        for key, value in cookies.items():
            if isinstance(value, bool):
                processed_cookies[key] = "true" if value else "false"
            else:
                processed_cookies[key] = str(value)
        
        if is_debug_mode():
            debug_print(f"处理后的cookies: {processed_cookies}", "blue")
        
        # 使用request_manager发送请求
        result = request_manager.request(
            ACCOUNTMANAGE['URL'], 
            {
                'method': ACCOUNTMANAGE['METHOD'],
                'cookies': processed_cookies,  # 使用处理后的cookies
                'headers': {
                    'Referer': 'https://i.chaoxing.com/',
                }
            }
        )
        
        if result['statusCode'] != 200:
            print(f"获取用户信息失败，状态码: {result['statusCode']}")
            if is_debug_mode():
                debug_print(f"获取用户信息失败，状态码: {result['statusCode']}", "red")
            return "未知用户"
        
        # 获取响应数据
        data = result.get('data', '')
        
        # 处理不同类型的响应数据
        if isinstance(data, bytes):
            try:
                data = data.decode('utf-8')
            except UnicodeDecodeError:
                print("无法解码响应数据")
                if is_debug_mode():
                    debug_print("错误：无法解码响应数据(bytes)", "red")
                return "未知用户"
        else:
            if isinstance(data, bool):
                if is_debug_mode():
                    debug_print("错误：响应数据为布尔值", "red")
                return "未知用户"  # 布尔值无法提取用户名，直接返回
        
        # 确保data是字符串类型
        if not isinstance(data, str):
            try:
                data = str(data)
            except:
                if is_debug_mode():
                    debug_print(f"错误：无法将响应数据({type(data).__name__})转换为字符串", "red")
                return "未知用户"
                
        # 防止data是None或布尔值
        if data is None or isinstance(data, bool):
            if is_debug_mode():
                debug_print("错误：响应数据为None或布尔值", "red")
            return "未知用户"
        
        # 从HTML内容中提取用户名
        try:
            # 尝试提取用户名，参考TypeScript版本的实现
            end_of_messageName = data.find('messageName') + 20
            if end_of_messageName > 20:  # 确保找到了messageName
                name = data[end_of_messageName:data.find('"', end_of_messageName)]
                if name:
                    if is_debug_mode():
                        debug_print(f"成功提取到用户名: {name}", "green")
                    return name
            
            # 尝试其他可能的提取方式
            username_match = re.search(r'用户名：.*?>(.*?)<', data)
            if username_match:
                name = username_match.group(1)
                if is_debug_mode():
                    debug_print(f"通过备选方式提取到用户名: {name}", "green")
                return name
            
            # 如果都找不到，返回未知用户
            if is_debug_mode():
                debug_print("无法从响应中提取用户名", "yellow")
            return "未知用户"
        except Exception as e:
            print(f"解析用户名失败: {e}")
            if is_debug_mode():
                debug_print(f"解析用户名过程发生异常: {e}", "red")
            return "未知用户"
    except Exception as e:
        print(f"获取用户名出错: {e}")
        if is_debug_mode():
            debug_print(f"获取用户名过程发生异常: {e}", "red")
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
        # 使用request_manager发送请求
        result = request_manager.request(
            PANTOKEN['URL'], 
            {
                'method': 'GET',
                'cookies': cookies,  # 显式传递cookie
                'headers': {
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