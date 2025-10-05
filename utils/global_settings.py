#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import logging

logger = logging.getLogger('app')

def get_global_settings():
    """
    获取全局设置
    
    Returns:
        dict: 全局设置
    """
    settings_path = 'configs/global_settings.json'
    
    # 如果配置文件不存在，创建默认设置
    if not os.path.exists(settings_path):
        default_settings = {
            "panel": {
                "theme": "light",
                "language": "zh_CN"
            },
            "user": {
                "default_location_preset": -1,
                "default_active_status": True,
                "default_monitor_interval": 30,
                "default_sign_delay": {
                    "min": 0,
                    "max": 30
                }
            },
            "system": {
                "auto_update_cookie": True,
                "cookie_update_interval": 21
            }
        }
        
        # 确保目录存在
        if not os.path.exists('configs'):
            os.makedirs('configs')
            
        # 写入默认设置
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(default_settings, f, ensure_ascii=False, indent=2)
        
        return default_settings
    
    # 读取现有设置
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        return settings
    except Exception as e:
        logger.error(f"读取全局设置出错: {e}")
        return {}

def update_global_settings(new_settings):
    """
    更新全局设置
    
    Args:
        new_settings: 新的设置数据
        
    Returns:
        bool: 更新是否成功
    """
    try:
        # 获取当前设置
        current_settings = get_global_settings()
        
        # 合并新设置（深度合并）
        def deep_update(d, u):
            for k, v in u.items():
                if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                    deep_update(d[k], v)
                else:
                    d[k] = v
            return d
        
        # 更新设置
        updated_settings = deep_update(current_settings, new_settings)
        
        # 写入文件
        settings_path = 'configs/global_settings.json'
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(updated_settings, f, ensure_ascii=False, indent=2)
            
        logger.info("全局设置已更新")
        return True
    except Exception as e:
        logger.error(f"更新全局设置时出错: {e}")
        return False

def get_default_location_preset():
    """
    获取默认位置预设ID
    
    Returns:
        int: 默认位置预设ID
    """
    settings = get_global_settings()
    return settings.get('user', {}).get('default_location_preset', -1) 