# -*- coding: utf-8 -*-
"""
签到统计功能模块
"""

import json
import os
from datetime import datetime, timedelta

def get_stats_file_path():
    """获取统计文件路径"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, 'configs', 'daily_stats.json')

def load_daily_stats():
    """加载每日统计数据"""
    try:
        stats_file = get_stats_file_path()
        if os.path.exists(stats_file):
            with open(stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"加载统计数据失败: {e}")
        return {}

def save_daily_stats(stats_data):
    """保存每日统计数据"""
    try:
        stats_file = get_stats_file_path()
        os.makedirs(os.path.dirname(stats_file), exist_ok=True)
        
        # 只保留最近30天的数据
        today = datetime.now().date()
        cutoff_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        filtered_stats = {k: v for k, v in stats_data.items() if k >= cutoff_date}
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(filtered_stats, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存统计数据失败: {e}")
        return False

def record_sign_result(user_phone, username, success, message="", activity_info=None):
    """
    记录签到结果
    
    Args:
        user_phone: 用户手机号
        username: 用户名
        success: 是否成功
        message: 签到消息
        activity_info: 活动信息（可选）
    """
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 加载现有统计数据
        daily_stats = load_daily_stats()
        
        # 初始化今日数据
        if today not in daily_stats:
            daily_stats[today] = {
                'success': 0,
                'failed': 0,
                'last_sign_time': '暂无记录',
                'records': []
            }
        
        # 更新统计
        today_stats = daily_stats[today]
        if success:
            today_stats['success'] += 1
        else:
            today_stats['failed'] += 1
        
        today_stats['last_sign_time'] = current_time
        
        # 记录详细信息
        record = {
            'time': current_time,
            'user_phone': user_phone,
            'username': username,
            'success': success,
            'message': message
        }
        
        if activity_info:
            record['activity_info'] = activity_info
        
        # 限制每日记录数量（最多保留100条）
        if 'records' not in today_stats:
            today_stats['records'] = []
        
        today_stats['records'].append(record)
        if len(today_stats['records']) > 100:
            today_stats['records'] = today_stats['records'][-100:]
        
        # 保存更新后的数据
        save_daily_stats(daily_stats)
        
        print(f"✅ 统计记录已更新: {username} - {'成功' if success else '失败'}")
        return True
        
    except Exception as e:
        print(f"记录签到结果失败: {e}")
        return False

def get_today_stats():
    """获取今日签到统计"""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        daily_stats = load_daily_stats()
        
        if today in daily_stats:
            today_data = daily_stats[today]
            return {
                'success': today_data.get('success', 0),
                'failed': today_data.get('failed', 0),
                'last_sign_time': today_data.get('last_sign_time', '暂无记录')
            }
        else:
            return {
                'success': 0,
                'failed': 0,
                'last_sign_time': '暂无记录'
            }
    except Exception as e:
        print(f"获取今日统计失败: {e}")
        return {
            'success': 0,
            'failed': 0,
            'last_sign_time': '暂无记录'
        }

def get_recent_records(days=7):
    """获取最近几天的签到记录"""
    try:
        daily_stats = load_daily_stats()
        recent_records = []
        
        # 获取最近N天的日期
        today = datetime.now().date()
        for i in range(days):
            date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            if date in daily_stats and 'records' in daily_stats[date]:
                date_records = daily_stats[date]['records']
                for record in date_records:
                    record['date'] = date
                    recent_records.append(record)
        
        # 按时间倒序排列
        recent_records.sort(key=lambda x: x['time'], reverse=True)
        return recent_records
        
    except Exception as e:
        print(f"获取最近记录失败: {e}")
        return []

def get_stats_summary(days=30):
    """获取统计汇总"""
    try:
        daily_stats = load_daily_stats()
        total_success = 0
        total_failed = 0
        total_days = 0
        
        today = datetime.now().date()
        for i in range(days):
            date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            if date in daily_stats:
                day_data = daily_stats[date]
                total_success += day_data.get('success', 0)
                total_failed += day_data.get('failed', 0)
                if day_data.get('success', 0) > 0 or day_data.get('failed', 0) > 0:
                    total_days += 1
        
        return {
            'total_success': total_success,
            'total_failed': total_failed,
            'total_attempts': total_success + total_failed,
            'active_days': total_days,
            'success_rate': round(total_success / (total_success + total_failed) * 100, 1) if (total_success + total_failed) > 0 else 0
        }
        
    except Exception as e:
        print(f"获取统计汇总失败: {e}")
        return {
            'total_success': 0,
            'total_failed': 0,
            'total_attempts': 0,
            'active_days': 0,
            'success_rate': 0
        } 