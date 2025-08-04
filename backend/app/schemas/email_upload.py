"""
邮件上传相关的Pydantic模型
用于API请求和响应的数据验证
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from app.models.email_upload import EmailUploadStatus


class EmailUploadResponse(BaseModel):
    """邮件上传响应模型"""
    id: str = Field(..., description="上传记录ID")
    original_filename: str = Field(..., description="原始文件名")
    file_size: int = Field(..., description="文件大小（字节）")
    file_type: str = Field(..., description="文件类型")
    email_subject: Optional[str] = Field(None, description="邮件主题")
    email_body: Optional[str] = Field(None, description="邮件正文")
    status: EmailUploadStatus = Field(..., description="处理状态")
    received_at: datetime = Field(..., description="接收时间")
    processed_at: Optional[datetime] = Field(None, description="处理时间")
    reviewer_id: Optional[str] = Field(None, description="审核员ID")
    review_comment: Optional[str] = Field(None, description="审核备注")
    extra_metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")

    class Config:
        from_attributes = True


class EmailUploadListResponse(BaseModel):
    """邮件上传列表响应模型"""
    items: List[EmailUploadResponse] = Field(..., description="上传记录列表")
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")


class EmailUploadStatsResponse(BaseModel):
    """邮件上传统计响应模型"""
    total_uploads: int = Field(..., description="总上传数")
    status_stats: Dict[str, int] = Field(..., description="按状态统计")
    total_size: int = Field(..., description="总文件大小")
    daily_stats: List[Dict[str, Any]] = Field(..., description="每日统计")
    period_days: int = Field(..., description="统计周期天数")


class EmailUploadCreateRequest(BaseModel):
    """邮件上传创建请求模型"""
    sender_email_hash: str = Field(..., description="发送者邮箱哈希")
    original_filename: str = Field(..., description="原始文件名")
    file_size: int = Field(..., description="文件大小")
    file_type: str = Field(..., description="文件类型")
    stored_filename: str = Field(..., description="存储文件名")
    email_subject: Optional[str] = Field(None, description="邮件主题")
    email_body: Optional[str] = Field(None, description="邮件正文")
    extra_metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")


class EmailUploadUpdateRequest(BaseModel):
    """邮件上传更新请求模型"""
    status: EmailUploadStatus = Field(..., description="新状态")
    review_comment: Optional[str] = Field(None, description="审核备注")


class EmailConfigResponse(BaseModel):
    """邮件配置响应模型"""
    email_upload_enabled: bool = Field(..., description="邮件上传是否启用")
    max_attachment_size: int = Field(..., description="最大附件大小")
    max_attachment_count: int = Field(..., description="最大附件数量")
    allowed_extensions: List[str] = Field(..., description="允许的文件扩展名")
    hourly_limit: int = Field(..., description="每小时限制")
    daily_limit: int = Field(..., description="每日限制")
    domain_whitelist_enabled: bool = Field(..., description="域名白名单是否启用")
    allowed_domains: List[str] = Field(..., description="允许的域名列表")


class EmailDomainRuleResponse(BaseModel):
    """邮件域名规则响应模型"""
    id: int = Field(..., description="规则ID")
    domain: str = Field(..., description="域名")
    is_allowed: bool = Field(..., description="是否允许")
    description: Optional[str] = Field(None, description="描述")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class EmailDomainRuleCreateRequest(BaseModel):
    """邮件域名规则创建请求模型"""
    domain: str = Field(..., description="域名")
    is_allowed: bool = Field(True, description="是否允许")
    description: Optional[str] = Field(None, description="描述")


class EmailDomainRuleListResponse(BaseModel):
    """邮件域名规则列表响应模型"""
    rules: List[EmailDomainRuleResponse] = Field(..., description="规则列表")
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    total_pages: int = Field(..., description="总页数")


# 为了兼容性，添加别名
DomainRuleResponse = EmailDomainRuleResponse
DomainRuleCreateRequest = EmailDomainRuleCreateRequest
DomainRuleListResponse = EmailDomainRuleListResponse


class EmailHealthResponse(BaseModel):
    """邮件系统健康检查响应模型"""
    status: str = Field(..., description="系统状态")
    timestamp: datetime = Field(..., description="检查时间")
    services: Dict[str, str] = Field(..., description="各服务状态")
    config: Dict[str, Any] = Field(..., description="配置信息")
    stats: Dict[str, Any] = Field(..., description="统计信息")


class EmailNotificationRequest(BaseModel):
    """邮件通知请求模型"""
    recipient_email: str = Field(..., description="收件人邮箱")
    subject: str = Field(..., description="邮件主题")
    body: str = Field(..., description="邮件正文")
    is_html: bool = Field(False, description="是否为HTML格式")


class EmailNotificationResponse(BaseModel):
    """邮件通知响应模型"""
    success: bool = Field(..., description="发送是否成功")
    message: str = Field(..., description="响应消息")
    notification_id: Optional[str] = Field(None, description="通知ID")


class EmailRateLimitResponse(BaseModel):
    """邮件频率限制响应模型"""
    email_hash: str = Field(..., description="邮箱哈希")
    allowed: bool = Field(..., description="是否允许")
    hourly_count: int = Field(..., description="小时计数")
    daily_count: int = Field(..., description="日计数")
    hourly_limit: int = Field(..., description="小时限制")
    daily_limit: int = Field(..., description="日限制")
    reset_time: Optional[datetime] = Field(None, description="重置时间")


class RateLimitStatsResponse(BaseModel):
    """频率限制统计响应模型"""
    total_rate_limits: int = Field(..., description="总频率限制数")
    active_limits: int = Field(..., description="活跃限制数")
    expired_limits: int = Field(..., description="过期限制数")
    hourly_stats: Dict[str, int] = Field(..., description="小时统计")
    daily_stats: Dict[str, int] = Field(..., description="日统计")
    top_limited_domains: List[Dict[str, Any]] = Field(..., description="限制最多的域名")
    period_days: int = Field(..., description="统计周期天数")


class EmailSystemStatsResponse(BaseModel):
    """邮件系统统计响应模型"""
    total_emails_processed: int = Field(..., description="总处理邮件数")
    total_attachments_saved: int = Field(..., description="总保存附件数")
    total_storage_used: int = Field(..., description="总存储使用量")
    active_rate_limits: int = Field(..., description="活跃频率限制数")
    blocked_domains: int = Field(..., description="被阻止域名数")
    allowed_domains: int = Field(..., description="允许域名数")
    last_email_check: Optional[datetime] = Field(None, description="最后邮件检查时间")
    system_uptime: float = Field(..., description="系统运行时间（秒）")


class EmailAttachmentResponse(BaseModel):
    """邮件附件响应模型"""
    filename: str = Field(..., description="文件名")
    size: int = Field(..., description="文件大小")
    mime_type: str = Field(..., description="MIME类型")
    file_hash: str = Field(..., description="文件哈希")
    upload_time: datetime = Field(..., description="上传时间")
    status: str = Field(..., description="文件状态")


class EmailBatchUploadResponse(BaseModel):
    """邮件批量上传响应模型"""
    total_files: int = Field(..., description="总文件数")
    successful_uploads: int = Field(..., description="成功上传数")
    failed_uploads: int = Field(..., description="失败上传数")
    upload_results: List[Dict[str, Any]] = Field(..., description="上传结果详情")
    processing_time: float = Field(..., description="处理时间（秒）")


class EmailValidationResponse(BaseModel):
    """邮件验证响应模型"""
    is_valid: bool = Field(..., description="是否有效")
    email_address: Optional[str] = Field(None, description="邮箱地址（脱敏）")
    domain: Optional[str] = Field(None, description="域名")
    domain_allowed: bool = Field(..., description="域名是否允许")
    rate_limit_status: Dict[str, Any] = Field(..., description="频率限制状态")
    validation_errors: List[str] = Field(default_factory=list, description="验证错误列表")