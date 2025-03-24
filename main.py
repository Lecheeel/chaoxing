import sys
import os
import traceback
from utils.helper import colored_print

def main():
    try:
        # 确保配置目录存在
        os.makedirs('chaoxing/configs', exist_ok=True)
        
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
        sys.exit(1)

if __name__ == "__main__":
    main() 