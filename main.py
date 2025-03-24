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
        print("3. 指定用户签到")
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
        elif choice == "3":
            # 指定用户签到
            handle_specific_sign()
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

def handle_specific_sign():
    """处理指定用户签到功能"""
    from utils.file import get_json_object
    from sign_api import sign_by_index, sign_by_phone
    
    try:
        # 读取存储的用户
        storage = get_json_object('configs/storage.json')
        users = storage.get('users', [])
        
        if not users:
            colored_print("当前没有存储的用户，请先通过单次签到功能添加用户", "red")
            return
        
        # 显示用户列表
        colored_print("选择用户:", "blue")
        for i, user in enumerate(users):
            username = user.get('username', '未知用户')
            phone = user.get('phone', '未知手机号')
            print(f"{i}. {username} ({phone})")
        
        print("或直接输入手机号")
        
        # 获取用户选择
        user_input = input("\n请输入选项编号或手机号: ")
        
        result = None
        if user_input.isdigit() and 0 <= int(user_input) < len(users):
            # 使用索引
            result = sign_by_index(int(user_input))
        else:
            # 使用手机号
            result = sign_by_phone(user_input)
        
        # 显示结果
        if result['status']:
            colored_print(result['message'], "green")
        else:
            colored_print(result['message'], "red")
            
    except Exception as e:
        colored_print(f"指定用户签到出错: {e}", "red")
        traceback.print_exc()

if __name__ == "__main__":
    main() 