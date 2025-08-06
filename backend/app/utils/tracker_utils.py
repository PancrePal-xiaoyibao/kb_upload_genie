"""
跟踪工具函数
提供tracker_id生成和管理功能
"""

import uuid
import hashlib
from datetime import datetime
from typing import Optional


def generate_tracker_id(prefix: str = "TRK") -> str:
    """
    生成唯一的跟踪ID
    
    Args:
        prefix: ID前缀，默认为"TRK"
        
    Returns:
        str: 格式化的跟踪ID
    """
    # 生成UUID4
    unique_id = str(uuid.uuid4())
    
    # 取UUID的前8位和后4位，用短横线连接
    short_id = f"{unique_id[:8]}-{unique_id[-4:]}"
    
    # 添加时间戳的后4位
    timestamp = str(int(datetime.now().timestamp()))[-4:]
    
    # 组合最终的tracker_id
    tracker_id = f"{prefix}-{short_id}-{timestamp}"
    
    return tracker_id.upper()


def generate_simple_tracker_id() -> str:
    """
    生成简单的跟踪ID（纯数字+字母组合）
    
    Returns:
        str: 12位的跟踪ID
    """
    # 生成UUID并取MD5哈希
    unique_id = str(uuid.uuid4())
    hash_obj = hashlib.md5(unique_id.encode())
    hash_hex = hash_obj.hexdigest()
    
    # 取前12位并转为大写
    return hash_hex[:12].upper()


def validate_tracker_id(tracker_id: str) -> bool:
    """
    验证跟踪ID格式是否有效
    
    Args:
        tracker_id: 要验证的跟踪ID
        
    Returns:
        bool: 是否有效
    """
    if not tracker_id:
        return False
    
    # 检查长度（应该在8-36字符之间）
    if len(tracker_id) < 8 or len(tracker_id) > 36:
        return False
    
    # 检查是否包含有效字符（字母、数字、短横线）
    valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-')
    if not all(c in valid_chars for c in tracker_id.upper()):
        return False
    
    return True


def format_tracker_display(tracker_id: str) -> str:
    """
    格式化跟踪ID用于显示
    
    Args:
        tracker_id: 跟踪ID
        
    Returns:
        str: 格式化后的显示文本
    """
    if not tracker_id:
        return "无"
    
    # 如果ID很长，显示前6位...后4位
    if len(tracker_id) > 12:
        return f"{tracker_id[:6]}...{tracker_id[-4:]}"
    
    return tracker_id


def extract_timestamp_from_tracker(tracker_id: str) -> Optional[datetime]:
    """
    从跟踪ID中提取时间戳信息（如果可能）
    
    Args:
        tracker_id: 跟踪ID
        
    Returns:
        Optional[datetime]: 提取的时间戳，如果无法提取则返回None
    """
    try:
        # 尝试从TRK格式的ID中提取时间戳
        if tracker_id.startswith('TRK-') and len(tracker_id.split('-')) >= 3:
            timestamp_part = tracker_id.split('-')[-1]
            if timestamp_part.isdigit() and len(timestamp_part) == 4:
                # 这是时间戳的后4位，无法准确还原完整时间
                return None
        
        return None
    except Exception:
        return None


def is_expired_tracker(created_at: datetime, days: int = 30) -> bool:
    """
    检查跟踪ID是否已过期
    
    Args:
        created_at: 创建时间
        days: 过期天数，默认30天
        
    Returns:
        bool: 是否已过期
    """
    if not created_at:
        return True
    
    from datetime import timedelta
    expiry_date = created_at + timedelta(days=days)
    return datetime.utcnow() > expiry_date


def get_tracker_age_description(created_at: datetime) -> str:
    """
    获取跟踪ID的年龄描述
    
    Args:
        created_at: 创建时间
        
    Returns:
        str: 年龄描述
    """
    if not created_at:
        return "未知"
    
    now = datetime.utcnow()
    diff = now - created_at
    
    if diff.days > 0:
        return f"{diff.days}天前"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours}小时前"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes}分钟前"
    else:
        return "刚刚"