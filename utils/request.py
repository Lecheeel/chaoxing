import requests
import gzip
import time
import http.cookiejar
from io import BytesIO
import uuid
import json
from typing import Dict, Any, Optional, Union, List
from .debug import is_debug_mode, debug_print_request, debug_print_response
from .file import save_user_cookies, get_user_cookies, get_stored_user

# 头信息常量
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# 特定场景的头信息
LOGIN_HEADERS = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'X-Requested-With': 'XMLHttpRequest',
    'Origin': 'https://passport2.chaoxing.com',
}

COURSE_HEADERS = {
    'Accept': 'text/html, */*; q=0.01',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8;',
    'Origin': 'https://mooc1-1.chaoxing.com',
}

ACTIVITY_HEADERS = {
    'Referer': 'https://mobilelearn.chaoxing.com/',
}

PHOTO_HEADERS = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Origin': 'https://mobilelearn.chaoxing.com',
}

# 认证Cookie字段白名单
AUTH_COOKIE_FIELDS = ['fid', 'uf', '_d', '_uid', 'UID', 'vc3', 'tuid', 'lv', 'vc', 'sso_puid', 'source']

class RequestManager:
    """
    统一管理Web请求的类，处理cookie和请求头等参数
    """
    def __init__(self):
        # 创建自定义CookieJar，允许有多个同名的cookie
        self.cookies = http.cookiejar.CookieJar()
        self.session = requests.Session()
        self.session.cookies = self.cookies
        
        # 默认请求头
        self.default_headers = DEFAULT_HEADERS.copy()
        
        # 请求ID，用于跟踪和调试
        self.request_id = str(uuid.uuid4())[:8]
        
        # 保存用户认证信息
        self.auth_info = {}
        
        # 当前用户的电话号码（用于多用户管理）
        self.current_user_phone = None
    
    def set_default_headers(self, headers: Dict[str, str]) -> None:
        """
        设置默认请求头
        
        Args:
            headers: 要设置的请求头字典
        """
        self.default_headers.update(headers)
    
    def get_headers_for_scenario(self, scenario: str, extra_headers: Dict[str, str] = None) -> Dict[str, str]:
        """
        根据不同场景获取预设的headers
        
        Args:
            scenario: 场景名称，如'login', 'course', 'activity', 'photo'等
            extra_headers: 额外添加的headers
            
        Returns:
            Dict: 包含相应场景headers的字典
        """
        headers = self.default_headers.copy()
        
        if scenario == 'login':
            headers.update(LOGIN_HEADERS)
        elif scenario == 'course':
            headers.update(COURSE_HEADERS)
        elif scenario == 'activity':
            headers.update(ACTIVITY_HEADERS)
        elif scenario == 'photo':
            headers.update(PHOTO_HEADERS)
        
        # 添加额外的headers
        if extra_headers:
            headers.update(extra_headers)
            
        return headers
    
    def set_current_user(self, phone: str) -> bool:
        """
        设置当前的用户，并加载其存储的cookie
        
        Args:
            phone: 用户手机号
            
        Returns:
            bool: 是否成功设置用户
        """
        try:
            user_data = get_stored_user(phone)
            if not user_data:
                print(f"未找到用户: {phone}")
                return False
            
            # 设置当前用户
            self.current_user_phone = phone
            
            # 清除现有cookie
            self.clear_cookies()
            
            # 如果用户有存储的cookies，加载它们
            if 'cookies' in user_data:
                self.set_cookies(user_data['cookies'])
            
            # 如果用户有认证信息，加载它
            if 'auth_info' in user_data:
                self.auth_info = user_data['auth_info']
            
            return True
        except Exception as e:
            print(f"设置当前用户失败: {e}")
            return False
    
    def get_current_user(self) -> str:
        """
        获取当前用户手机号
        
        Returns:
            str: 当前用户手机号
        """
        return self.current_user_phone
    
    def set_auth_cookies(self, auth_data: Dict[str, str]) -> None:
        """
        设置认证相关的cookie
        
        Args:
            auth_data: 包含认证信息的字典
        """
        self.auth_info = auth_data.copy()
        
        # 使用白名单方式，只包含确定是cookie的字段
        
        # 如果auth_data中有params字段，则使用params中的内容作为cookie
        if 'params' in auth_data and isinstance(auth_data['params'], dict):
            auth_cookies = auth_data['params']
        else:
            # 使用白名单，只保留应作为cookie的字段
            auth_cookies = {k: v for k, v in auth_data.items() if k in AUTH_COOKIE_FIELDS}
        
        # 设置常用的认证cookie
        self.set_cookies(auth_cookies)
        
        # 如果已设置当前用户，保存cookie到本地存储
        if self.current_user_phone:
            self.save_cookies_to_storage()
    
    def save_cookies_to_storage(self) -> bool:
        """
        将当前会话的cookie保存到本地存储
        
        Returns:
            bool: 是否成功保存
        """
        if not self.current_user_phone:
            print("未设置当前用户，无法保存cookie")
            return False
        
        cookies = self.get_cookies()
        return save_user_cookies(self.current_user_phone, cookies, self.auth_info)
    
    def load_cookies_from_storage(self, phone: str) -> bool:
        """
        从本地存储加载指定用户的cookie
        
        Args:
            phone: 用户手机号
            
        Returns:
            bool: 是否成功加载
        """
        cookies = get_user_cookies(phone)
        if not cookies:
            return False
        
        # 清除现有cookie
        self.clear_cookies()
        
        # 设置加载的cookie
        self.set_cookies(cookies)
        return True
    
    def set_cookies(self, cookies: Dict[str, str], domain: str = None) -> None:
        """
        设置cookie
        
        Args:
            cookies: 要设置的cookie字典
            domain: cookie的域名，如果不提供则从下一个请求中提取
        """
        self._domain_for_cookies = domain
        
        for name, value in cookies.items():
            # 确保cookie值是字符串类型
            if isinstance(value, bool):
                value = "true" if value else "false"
            elif value is not None:
                value = str(value)
                # 确保cookie值可以用Latin-1编码
                try:
                    value.encode('latin-1')
                except UnicodeEncodeError:
                    # 如果包含非ASCII字符，进行URL编码
                    import urllib.parse
                    value = urllib.parse.quote(value)
            
            if domain:
                cookie = requests.cookies.create_cookie(name=name, value=value, domain=domain)
                self.session.cookies.set_cookie(cookie)
            else:
                # 如果没有提供域名，保存到临时存储中，在下次请求时设置
                self._pending_cookies = getattr(self, '_pending_cookies', {})
                self._pending_cookies[name] = value
    
    def _apply_pending_cookies(self, url: str) -> None:
        """
        应用待处理的cookie到请求中
        
        Args:
            url: 请求的URL
        """
        if hasattr(self, '_pending_cookies') and self._pending_cookies:
            try:
                domain = url.split('/')[2]
                for name, value in self._pending_cookies.items():
                    # 确保cookie值可以用Latin-1编码
                    if isinstance(value, str):
                        try:
                            value.encode('latin-1')
                        except UnicodeEncodeError:
                            # 如果包含非ASCII字符，进行URL编码
                            import urllib.parse
                            value = urllib.parse.quote(value)
                    
                    cookie = requests.cookies.create_cookie(name=name, value=value, domain=domain)
                    self.session.cookies.set_cookie(cookie)
                self._pending_cookies = {}
            except Exception as e:
                print(f"设置cookie时出错: {e}")
    
    def get_cookies(self) -> Dict[str, str]:
        """
        获取当前会话中的所有cookie
        
        Returns:
            Dict: 包含cookie信息的字典
        """
        cookies_dict = {}
        for cookie in self.session.cookies:
            cookies_dict[cookie.name] = cookie.value
        return cookies_dict
    
    def get_cookie_string(self) -> str:
        """
        获取格式化的cookie字符串，用于请求头
        
        Returns:
            str: 格式化的cookie字符串
        """
        cookies = self.get_cookies()
        return '; '.join([f"{name}={value}" for name, value in cookies.items()])
    
    def get_auth_cookie_string(self) -> str:
        """
        获取格式化的认证cookie字符串
        
        Returns:
            str: 格式化的认证cookie字符串
        """
        cookies = self.get_cookies()
        return f"fid={cookies.get('fid', '')}; uf={cookies.get('uf', '')}; _d={cookies.get('_d', '')}; UID={cookies.get('_uid', '') or cookies.get('UID', '')}; vc3={cookies.get('vc3', '')};"
    
    def clear_cookies(self) -> None:
        """
        清除会话中的所有cookie
        """
        self.session.cookies.clear()
        if hasattr(self, '_pending_cookies'):
            self._pending_cookies = {}
    
    def request(self, url: str, options: Dict[str, Any] = None, payload: Any = None, 
                max_retries: int = 3, timeout: int = 10) -> Dict[str, Any]:
        """
        发送HTTP请求
        
        Args:
            url: 接口地址
            options: 请求配置选项
            payload: 请求数据（用于POST请求）
            max_retries: 最大重试次数
            timeout: 请求超时时间(秒)
        
        Returns:
            Dict: 包含响应数据、头信息和状态码的字典
        """
        if options is None:
            options = {}
        
        # 设置默认值
        method = options.get('method', 'GET')
        
        # 如果options中包含scenario，使用预设的headers
        scenario = options.get('scenario')
        if scenario:
            headers = self.get_headers_for_scenario(scenario, options.get('headers'))
        else:
            # 否则使用默认headers加options中的headers
            headers = self.default_headers.copy()
            headers.update(options.get('headers', {}))
        
        # 确保所有头信息都是可以用ASCII编码的字符串
        for key in list(headers.keys()):
            if headers[key] and isinstance(headers[key], str):
                # 对非ASCII字符进行处理，防止Latin-1编码错误
                try:
                    headers[key].encode('latin-1')
                except UnicodeEncodeError:
                    # 如果包含非ASCII字符，进行URL编码
                    import urllib.parse
                    headers[key] = urllib.parse.quote(headers[key])
        
        # 应用临时cookie
        self._apply_pending_cookies(url)
        
        # 添加新的cookie头
        if 'cookies' in options:
            self.set_cookies(options['cookies'])
        
        # 输出调试信息
        if is_debug_mode() or options.get('debug'):
            debug_print_request(url, method, headers, len(self.session.cookies))
        
        # 重试机制
        for retry in range(max_retries):
            try:
                response = None
                if method.upper() == 'GET':
                    response = self.session.get(url, headers=headers, timeout=timeout)
                elif method.upper() == 'POST':
                    response = self.session.post(url, headers=headers, data=payload, timeout=timeout)
                
                # 检查响应状态
                response.raise_for_status()
                
                # 处理gzip压缩
                if options.get('gzip') and 'gzip' in response.headers.get('Content-Encoding', ''):
                    try:
                        buf = BytesIO(response.content)
                        with gzip.GzipFile(fileobj=buf) as f:
                            data = f.read().decode('utf-8')
                    except gzip.BadGzipFile:
                        # 服务器返回的不是有效的gzip数据，直接使用原始内容
                        print("警告: 服务器返回的不是有效的gzip数据，使用未压缩内容")
                        data = response.text
                else:
                    data = response.text
                
                # 调试输出响应信息
                if is_debug_mode() or options.get('debug'):
                    debug_print_response(response.status_code, dict(response.headers), data)
                
                # 请求成功后，如果有当前用户，自动保存cookie
                if self.current_user_phone:
                    self.save_cookies_to_storage()
                
                return {
                    'data': data,
                    'headers': dict(response.headers),
                    'statusCode': response.status_code,
                    'cookies': self.get_cookies()
                }
            except requests.exceptions.Timeout:
                if retry < max_retries - 1:
                    print(f"请求超时，正在进行第{retry + 2}次尝试...")
                    time.sleep(1)  # 延迟1秒后重试
                    continue
                print(f"请求超时: {url}")
                return {'data': 'timeout', 'headers': {}, 'statusCode': 408, 'cookies': self.get_cookies()}
            except requests.exceptions.ConnectionError:
                if retry < max_retries - 1:
                    print(f"连接错误，正在进行第{retry + 2}次尝试...")
                    time.sleep(2)  # 延迟2秒后重试
                    continue
                print(f"连接错误: {url}")
                return {'data': 'connection_error', 'headers': {}, 'statusCode': 503, 'cookies': self.get_cookies()}
            except requests.exceptions.RequestException as e:
                if retry < max_retries - 1:
                    print(f"请求异常，正在进行第{retry + 2}次尝试...")
                    time.sleep(1)  # 延迟1秒后重试
                    continue
                print(f"请求异常: {e}")
                return {'data': str(e), 'headers': {}, 'statusCode': 500, 'cookies': self.get_cookies()}

# 创建全局请求管理器实例
request_manager = RequestManager()

# 兼容性函数，用于向后兼容
def request(url, options=None, payload=None, max_retries=3, timeout=10):
    """
    向后兼容的请求函数
    """
    return request_manager.request(url, options, payload, max_retries, timeout)

def cookie_serialize(cookies):
    """
    向后兼容的cookie序列化函数，只序列化实际的cookie字段
    """
    # 确保传入的是字典
    if not isinstance(cookies, dict):
        return ""
    
    # 如果有params字段且是字典，使用它
    if 'params' in cookies and isinstance(cookies['params'], dict):
        real_cookies = cookies['params']
    else:
        # 使用白名单，只保留应作为cookie的字段
        real_cookies = {k: v for k, v in cookies.items() if k in AUTH_COOKIE_FIELDS}
    
    # 构建cookie字符串
    return f"fid={real_cookies.get('fid', '')}; uf={real_cookies.get('uf', '')}; _d={real_cookies.get('_d', '')}; UID={real_cookies.get('_uid', '') or real_cookies.get('UID', '')}; vc3={real_cookies.get('vc3', '')};"

def get_session_cookies():
    """
    向后兼容的获取会话cookie函数
    """
    return request_manager.get_cookies()

def clear_session():
    """
    向后兼容的清除会话函数
    """
    request_manager.clear_cookies()

def set_current_user(phone):
    """
    设置当前用户
    
    Args:
        phone: 用户手机号
        
    Returns:
        bool: 是否成功设置用户
    """
    return request_manager.set_current_user(phone)

def get_current_user():
    """
    获取当前用户手机号
    
    Returns:
        str: 当前用户手机号
    """
    return request_manager.get_current_user()

def save_current_cookies():
    """
    保存当前会话的cookie到本地存储
    
    Returns:
        bool: 是否成功保存
    """
    return request_manager.save_cookies_to_storage()

def load_user_cookies(phone):
    """
    从本地存储加载指定用户的cookie
    
    Args:
        phone: 用户手机号
        
    Returns:
        bool: 是否成功加载
    """
    return request_manager.load_cookies_from_storage(phone)

# 向后兼容，保留旧变量名
_session = request_manager.session 