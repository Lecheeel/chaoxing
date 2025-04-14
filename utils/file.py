import json
import os

def get_json_object(file_url):
    """
    读取JSON文件内容
    
    Args:
        file_url: 文件路径
    
    Returns:
        dict: JSON对象
    """
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_dir, file_url)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 如果文件不存在，创建一个空的JSON结构
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({"users": []}, f)
            return {"users": []}
        
        # 尝试不同的编码方式打开文件
        for encoding in ['utf-8', 'latin1', 'gbk', 'cp1252']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return json.load(f)
            except UnicodeDecodeError:
                continue
            except json.JSONDecodeError:
                # 如果JSON解析失败，可能是文件损坏
                break
        
        # 如果所有编码都失败，重新创建文件
        print(f"无法读取文件 {file_path}，将创建新文件")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({"users": []}, f)
        return {"users": []}
    except Exception as e:
        print(f"读取文件出错: {e}")
        return {"users": []}

def store_user(phone, user):
    """
    储存用户凭证
    
    Args:
        phone: 手机号
        user: 用户信息
    
    Returns:
        list: 更新后的用户列表
    """
    try:
        print(f"开始存储用户信息: 手机号={phone}")
        
        # 读取当前存储的数据
        data = get_json_object('configs/storage.json')
        
        # 确保用户对象包含手机号
        user['phone'] = phone
        
        # 查找是否已存在该用户
        found = False
        for i, stored_user in enumerate(data.get('users', [])):
            if stored_user.get('phone') == phone:
                # 保存更新前的用户信息，用于调试
                old_user = data['users'][i].copy()
                print(f"找到已存在用户: 索引={i}, 手机号={phone}")
                
                # 保留现有字段，更新新字段
                data['users'][i].update(user)
                
                # 确保username字段存在
                if 'username' not in data['users'][i]:
                    data['users'][i]['username'] = "未知用户"
                found = True
                break
        
        if not found:
            # 未找到则添加
            print(f"用户不存在，将添加新用户: {phone}")
            if 'users' not in data:
                data['users'] = []
            
            # 为新用户分配ID
            new_id = 0
            if data['users']:
                existing_ids = [u.get('id', 0) for u in data['users']]
                new_id = max(existing_ids) + 1
            
            # 设置默认值
            if 'username' not in user:
                user['username'] = "未知用户"
            if 'active' not in user:
                user['active'] = True
            if 'id' not in user:
                user['id'] = new_id
            
            data['users'].append(user)
        
        # 验证users列表非空
        if not data.get('users'):
            print("警告: 更新后的用户列表为空，将使用默认结构")
            data = {"users": [user]}
        
        # 写入文件
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_dir, 'configs/storage.json')
        print(f"将保存数据到路径: {file_path}")
        
        # 安全写入（先写入临时文件，再重命名）
        temp_file = f"{file_path}.tmp"
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"已写入临时文件: {temp_file}")
        
        # 重命名为正式文件
        os.replace(temp_file, file_path)
        print(f"临时文件已重命名为: {file_path}")
        
        # 验证写入结果
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                verify_data = json.load(f)
                if verify_data.get('users'):
                    print(f"验证成功: 文件包含 {len(verify_data['users'])} 个用户")
                else:
                    print(f"警告: 验证发现用户列表为空")
        except Exception as ve:
            print(f"验证文件内容时出错: {ve}")
        
        print(f"用户信息保存成功，当前用户数量: {len(data.get('users', []))}")
        return data['users']
    except Exception as e:
        print(f"存储用户信息失败: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_stored_user(phone):
    """
    获取存储的用户信息
    
    Args:
        phone: 手机号
    
    Returns:
        dict: 用户信息，如果不存在则返回None
    """
    data = get_json_object('configs/storage.json')
    
    for user in data.get('users', []):
        if user.get('phone') == phone:
            return user.copy()
    
    return None

def save_user_cookies(phone, cookies, auth_info=None):
    """
    保存用户的cookies到storage.json
    
    Args:
        phone: 手机号
        cookies: 要保存的cookie字典
        auth_info: 认证信息(可选)
    
    Returns:
        bool: 是否保存成功
    """
    try:
        user = get_stored_user(phone)
        if not user:
            user = {"phone": phone, "username": "未知用户"}
        
        # 保存cookies
        user['cookies'] = cookies
        
        # 如果提供了认证信息，也保存
        if auth_info:
            user['auth_info'] = auth_info
        
        store_user(phone, user)
        return True
    except Exception as e:
        print(f"保存用户cookies失败: {e}")
        return False

def get_user_cookies(phone):
    """
    获取用户存储的cookies
    
    Args:
        phone: 手机号
    
    Returns:
        dict: 用户cookies，如果不存在则返回空字典
    """
    user = get_stored_user(phone)
    if user and 'cookies' in user:
        return user['cookies']
    return {}

def get_all_users():
    """
    获取所有存储的用户信息
    
    Returns:
        list: 所有用户信息的列表
    """
    data = get_json_object('configs/storage.json')
    return data.get('users', [])

def delete_user(phone):
    """
    删除指定手机号的用户
    
    Args:
        phone: 手机号
    
    Returns:
        bool: 是否删除成功
    """
    try:
        data = get_json_object('configs/storage.json')
        
        # 查找并移除用户
        for i, user in enumerate(data.get('users', [])):
            if user.get('phone') == phone:
                data['users'].pop(i)
                break
        
        # 写入文件
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_dir, 'configs/storage.json')
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"删除用户失败: {e}")
        return False

def save_json_object(file_url, data):
    """
    保存JSON对象到指定文件
    
    Args:
        file_url: 文件路径
        data: 要保存的JSON对象
    
    Returns:
        bool: 是否保存成功
    """
    try:
        print(f"尝试保存JSON数据到: {file_url}")
        
        # 确保路径是相对于项目根目录的
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_dir, file_url)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 安全写入（先写入临时文件，再重命名）
        temp_file = f"{file_path}.tmp"
        print(f"创建临时文件: {temp_file}")
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"数据已写入临时文件")
        
        print(f"准备将临时文件重命名为: {file_path}")
        # 重命名为正式文件
        os.replace(temp_file, file_path)
        
        print(f"文件保存成功: {file_path}")
        
        # 验证写入结果
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                verify_data = json.load(f)
            print(f"文件验证成功")
        except Exception as e:
            print(f"文件验证失败: {e}")
            return False
        
        return True
    except Exception as e:
        print(f"保存JSON对象到文件时出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_schedule_tasks():
    """获取所有定时签到任务"""
    tasks = []
    try:
        json_object = get_json_object('configs/schedule.json')
        if 'tasks' in json_object:
            tasks = json_object['tasks']
    except:
        # 如果文件不存在或格式不正确，返回空列表
        tasks = []
    
    return tasks

def save_schedule_tasks(tasks):
    """保存定时签到任务列表"""
    try:
        data = {'tasks': tasks}
        with open('configs/schedule.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"保存定时任务失败: {e}")
        return False

def add_schedule_task(task):
    """添加定时签到任务"""
    tasks = get_schedule_tasks()
    # 生成任务ID
    task_id = 1
    if tasks:
        task_id = max([t.get('id', 0) for t in tasks]) + 1
    
    task['id'] = task_id
    tasks.append(task)
    return save_schedule_tasks(tasks)

def update_schedule_task(task_id, task_data):
    """更新定时签到任务"""
    tasks = get_schedule_tasks()
    # 确保task_id是整数
    task_id = int(task_id)
    for i, task in enumerate(tasks):
        # 确保对比的task ID也是整数
        if int(task.get('id', 0)) == task_id:
            tasks[i].update(task_data)
            return save_schedule_tasks(tasks)
    return False

def delete_schedule_task(task_id):
    """删除定时签到任务"""
    tasks = get_schedule_tasks()
    tasks = [t for t in tasks if t.get('id') != task_id]
    return save_schedule_tasks(tasks) 