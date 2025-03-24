import sys
import os
import traceback
from utils.helper import colored_print

def main():
    """主入口函数"""
    try:
        # 确保配置目录存在
        os.makedirs('chaoxing/configs', exist_ok=True)
        
        # 打印欢迎信息
        colored_print("超星学习通签到工具", "blue")
        colored_print("支持普通签到、拍照签到、手势签到、位置签到、二维码签到", "blue")
        
        # 显示选项
        print("\n请选择功能:")
        print("1. 单次签到")
        print("2. 监听签到")
        print("0. 退出")
        
        choice = input("\n请输入选项编号: ")
        
        if choice == "1":
            # 单次签到
            from sign import main as sign_main
            sign_main()
        elif choice == "2":
            # 监听签到
            from monitor import monitor_sign
            monitor_sign()
        elif choice == "0":
            # 退出
            colored_print("程序已退出", "blue")
            sys.exit(0)
        else:
            colored_print("无效选择，程序已退出", "red")
            sys.exit(1)
    except KeyboardInterrupt:
        colored_print("\n程序已被用户中断", "yellow")
        sys.exit(0)
    except Exception as e:
        colored_print(f"程序运行出错: {e}", "red")
        colored_print("详细错误信息:", "red")
        traceback.print_exc()
        colored_print("\n可能的解决方案:", "yellow")
        colored_print("1. 检查网络连接是否正常", "yellow")
        colored_print("2. 超星服务器可能暂时不可用，请稍后再试", "yellow")
        colored_print("3. 用户登录凭证可能已过期，请尝试重新登录", "yellow")
        colored_print("4. 如果存储文件损坏，尝试删除 chaoxing/configs/storage.json 文件后重试", "yellow")
        sys.exit(1)

if __name__ == "__main__":
    main() 