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
        data = get_json_object('configs/storage.json')
        user['phone'] = phone
        
        # 查找是否已存在该用户
        found = False
        for i, stored_user in enumerate(data.get('users', [])):
            if stored_user.get('phone') == phone:
                # 保留现有字段，更新新字段
                data['users'][i].update(user)
                # 确保username字段存在
                if 'username' not in data['users'][i]:
                    data['users'][i]['username'] = "未知用户"
                found = True
                break
        
        if not found:
            # 未找到则添加
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
        
        # 写入文件
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_dir, 'configs/storage.json')
        
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        
        return data['users']
    except Exception as e:
        print(f"存储用户信息失败: {e}")
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