"""
调试工具模块 - 提供全局调试标志和相关调试功能
"""
from typing import Any, Dict, Optional
from .helper import colored_print

# 全局调试标志
DEBUG_MODE = False

def set_debug_mode(mode: bool) -> None:
    """
    设置全局调试模式
    
    Args:
        mode: True表示启用调试，False表示禁用调试
    """
    global DEBUG_MODE
    DEBUG_MODE = mode
    colored_print(f"调试模式已{'启用' if mode else '禁用'}", "blue")

def is_debug_mode() -> bool:
    """
    检查当前是否处于调试模式
    
    Returns:
        bool: 当前是否处于调试模式
    """
    return DEBUG_MODE

def debug_print(message: str, color: Optional[str] = None) -> None:
    """
    在调试模式下打印消息
    
    Args:
        message: 要打印的消息
        color: 可选的颜色
    """
    if DEBUG_MODE:
        colored_print(message, color)

def debug_print_request(url: str, method: str, headers: Dict[str, str], cookies: int) -> None:
    """
    在调试模式下打印请求信息
    
    Args:
        url: 请求URL
        method: 请求方法
        headers: 请求头
        cookies: Cookie数量
    """
    if DEBUG_MODE:
        colored_print("===== 请求信息 =====", "blue")
        colored_print(f"请求URL: {url}", "blue")
        colored_print(f"请求方法: {method}", "blue")
        colored_print(f"请求头: {headers}", "blue")
        colored_print(f"Cookie数量: {cookies}", "blue")
        colored_print("===================", "blue")

def debug_print_response(status_code: int, headers: Dict[str, str], data: Any = None) -> None:
    """
    在调试模式下打印响应信息
    
    Args:
        status_code: 响应状态码
        headers: 响应头
        data: 可选的响应数据
    """
    if DEBUG_MODE:
        colored_print("===== 响应信息 =====", "green")
        colored_print(f"状态码: {status_code}", "green")
        colored_print(f"响应头: {headers}", "green")
        if data and isinstance(data, str) and len(data) > 200:
            colored_print(f"响应数据(截断): {data}...", "green")
        elif data:
            colored_print(f"响应数据: {data}", "green")
        colored_print("===================", "green") 