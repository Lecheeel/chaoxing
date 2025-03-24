import time

def delay(seconds):
    """
    延迟指定的秒数
    
    Args:
        seconds: 延迟的秒数
    """
    time.sleep(seconds)

def colored_print(text, color=None):
    """
    打印彩色文本
    
    Args:
        text: 要打印的文本
        color: 颜色，支持'red', 'green', 'blue'等
    """
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'blue': '\033[94m',
        'reset': '\033[0m'
    }
    
    if color and color in colors:
        print(f"{colors[color]}{text}{colors['reset']}")
    else:
        print(text) 