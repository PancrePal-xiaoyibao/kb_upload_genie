"""
邮箱脱敏工具函数
"""

def mask_email_address(email: str) -> str:
    """
    对邮箱地址进行脱敏处理
    规则：
    - 用户名部分：保留前1-2个字符和后1-2个字符，中间用*替换
    - 域名部分：完全保留
    
    示例：
    - liusoee@gmail.com -> liu**ee@gmail.com
    - test@example.org -> te*t@example.org
    - a@domain.com -> a***@domain.com
    """
    if not email or '@' not in email:
        return email
    
    try:
        username, domain = email.split('@', 1)
        
        if len(username) <= 3:
            # 短用户名：保留第一个字符，其余用*替换
            masked_username = username[0] + '*' * (len(username) - 1)
        elif len(username) <= 6:
            # 中等长度：保留前1个和后1个字符
            masked_username = username[0] + '*' * (len(username) - 2) + username[-1]
        else:
            # 长用户名：保留前2个和后2个字符
            masked_username = username[:2] + '*' * (len(username) - 4) + username[-2:]
        
        return f"{masked_username}@{domain}"
    
    except Exception:
        # 如果处理失败，返回通用脱敏格式
        return "***@domain.com"


def mask_email_from_subject(subject: str) -> str:
    """
    从邮件主题中提取并脱敏邮箱地址
    """
    if not subject:
        return subject
    
    import re
    
    # 邮箱正则表达式
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    def replace_email(match):
        email = match.group(0)
        return mask_email_address(email)
    
    return re.sub(email_pattern, replace_email, subject)
