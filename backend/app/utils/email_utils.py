"""
邮箱脱敏工具
用于在API响应时对邮箱地址进行脱敏处理
"""

import re


def mask_email(email: str) -> str:
    """
    对邮箱地址进行脱敏处理
    
    规则：
    - 用户名长度 <= 3: 显示第一个字符 + * + @domain
    - 用户名长度 4-6: 显示前2个字符 + ** + 后1个字符 + @domain  
    - 用户名长度 >= 7: 显示前3个字符 + ** + 后2个字符 + @domain
    
    示例：
    - a@gmail.com -> a*@gmail.com
    - abc@gmail.com -> a*c@gmail.com
    - liue@gmail.com -> li**e@gmail.com
    - liusoee@gmail.com -> liu**ee@gmail.com
    - verylongname@gmail.com -> ver**me@gmail.com
    """
    if not email or '@' not in email:
        return email
    
    try:
        username, domain = email.split('@', 1)
        username_len = len(username)
        
        if username_len <= 1:
            # 用户名太短，只显示*
            masked_username = '*'
        elif username_len <= 3:
            # 短用户名：显示第一个字符 + *
            masked_username = username[0] + '*'
        elif username_len <= 6:
            # 中等用户名：显示前2个 + ** + 后1个
            masked_username = username[:2] + '**' + username[-1:]
        else:
            # 长用户名：显示前3个 + ** + 后2个
            masked_username = username[:3] + '**' + username[-2:]
        
        return f"{masked_username}@{domain}"
    
    except Exception:
        # 如果处理失败，返回完全脱敏的邮箱
        return "***@***"


def is_valid_email(email: str) -> bool:
    """
    简单的邮箱格式验证
    """
    if not email:
        return False
    
    # 简单的邮箱正则验证
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


# 测试用例（仅在直接运行此文件时执行）
if __name__ == "__main__":
    test_emails = [
        "a@gmail.com",
        "ab@gmail.com", 
        "abc@gmail.com",
        "liue@gmail.com",
        "liusoee@gmail.com",
        "verylongname@gmail.com",
        "test.email+tag@example.com",
        "user123@company.co.uk"
    ]
    
    print("邮箱脱敏测试:")
    for email in test_emails:
        masked = mask_email(email)
        print(f"{email:25} -> {masked}")
