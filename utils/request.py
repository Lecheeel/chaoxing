import requests
import gzip
import time
import http.cookiejar
from io import BytesIO

# 创建自定义CookieJar，允许有多个同名的cookie
class MultipleCookieJar(http.cookiejar.CookieJar):
    def set_cookie(self, cookie):
        # 这个方法会被每个新cookie调用
        # 我们不做重复检查，允许添加同名cookie
        http.cookiejar.CookieJar.set_cookie(self, cookie)

# 创建全局session对象
_session = requests.Session()
_session.cookies = MultipleCookieJar()

def request(url, options=None, payload=None, max_retries=3, timeout=10):
    """
    发送HTTP请求
    
    Args:
        url: 接口地址
        options: headers, method 参数配置
        payload: 当进行POST请求时传入数据
        max_retries: 最大重试次数
        timeout: 请求超时时间(秒)
    
    Returns:
        dict: 包含响应数据、头信息和状态码
    """
    if options is None:
        options = {}
    
    # 设置默认值
    method = options.get('method', 'GET')
    headers = options.get('headers', {})
    
    # 添加默认User-Agent
    if 'User-Agent' not in headers:
        headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    
    # 添加新的cookie头
    if 'cookies' in options:
        for name, value in options['cookies'].items():
            # 确保cookie值是字符串类型
            if isinstance(value, bool):
                value = "true" if value else "false"
            elif value is not None:
                value = str(value)
                
            try:
                domain = url.split('/')[2]
                cookie = requests.cookies.create_cookie(name=name, value=value, domain=domain)
                _session.cookies.set_cookie(cookie)
            except Exception as e:
                print(f"设置cookie '{name}'='{value}'时出错: {e}")
    
    # 输出调试信息
    if options.get('debug'):
        print(f"请求URL: {url}")
        print(f"请求方法: {method}")
        print(f"请求头: {headers}")
        print(f"Cookie数量: {len(_session.cookies)}")
    
    # 重试机制
    for retry in range(max_retries):
        try:
            response = None
            if method.upper() == 'GET':
                response = _session.get(url, headers=headers, timeout=timeout)
            elif method.upper() == 'POST':
                response = _session.post(url, headers=headers, data=payload, timeout=timeout)
            
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
            
            # 整理cookie
            cookies_dict = {}
            for cookie in _session.cookies:
                cookies_dict[cookie.name] = cookie.value
            
            return {
                'data': data,
                'headers': dict(response.headers),
                'statusCode': response.status_code,
                'cookies': cookies_dict
            }
        except requests.exceptions.Timeout:
            if retry < max_retries - 1:
                print(f"请求超时，正在进行第{retry + 2}次尝试...")
                time.sleep(1)  # 延迟1秒后重试
                continue
            print(f"请求超时: {url}")
            return {'data': 'timeout', 'headers': {}, 'statusCode': 408}
        except requests.exceptions.ConnectionError:
            if retry < max_retries - 1:
                print(f"连接错误，正在进行第{retry + 2}次尝试...")
                time.sleep(2)  # 延迟2秒后重试
                continue
            print(f"连接错误: {url}")
            return {'data': 'connection_error', 'headers': {}, 'statusCode': 503}
        except requests.exceptions.RequestException as e:
            if retry < max_retries - 1:
                print(f"请求异常，正在进行第{retry + 2}次尝试...")
                time.sleep(1)  # 延迟1秒后重试
                continue
            print(f"请求异常: {e}")
            return {'data': str(e), 'headers': {}, 'statusCode': 500}

def cookie_serialize(cookies):
    """
    序列化cookie为字符串
    
    Args:
        cookies: 包含cookie信息的字典
    
    Returns:
        str: 序列化后的cookie字符串
    """
    return f"fid={cookies.get('fid', '')}; uf={cookies.get('uf', '')}; _d={cookies.get('_d', '')}; UID={cookies.get('_uid', '') or cookies.get('UID', '')}; vc3={cookies.get('vc3', '')};" 

def get_session_cookies():
    """
    获取当前会话中的所有cookie
    
    Returns:
        dict: 包含cookie信息的字典
    """
    cookies_dict = {}
    for cookie in _session.cookies:
        cookies_dict[cookie.name] = cookie.value
    return cookies_dict

def clear_session():
    """
    清除会话中的所有cookie
    """
    global _session
    _session = requests.Session()
    _session.cookies = MultipleCookieJar() 