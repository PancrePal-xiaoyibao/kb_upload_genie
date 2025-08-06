"""
上传跟踪相关的数据模式
定义跟踪查询相关的Pydantic模型，用于API请求和响应
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from app.models.article import ProcessingStatus, UploadMethod


class TrackerQueryRequest(BaseModel):
    """跟踪查询请求模式"""
    tracker_id: str = Field(..., min_length=1, max_length=36, description="跟踪ID")


class TrackerStatusResponse(BaseModel):
    """跟踪状态响应模式"""
    tracker_id: str = Field(..., description="跟踪ID")
    processing_status: ProcessingStatus = Field(..., description="处理状态")
    upload_method: Optional[UploadMethod] = Field(None, description="上传方法")
    title: Optional[str] = Field(None, description="文章标题")
    file_type: Optional[str] = Field(None, description="文件类型")
    file_size: Optional[int] = Field(None, description="文件大小(字节)")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    processed_at: Optional[datetime] = Field(None, description="处理完成时间")
    metadata: Optional[Dict[str, Any]] = Field(None, description="相关元数据")
    error_message: Optional[str] = Field(None, description="错误信息")
    
    class Config:
        from_attributes = True


class TrackerNotFoundResponse(BaseModel):
    """跟踪ID未找到响应模式"""
    success: bool = Field(default=False, description="操作是否成功")
    message: str = Field(default="跟踪ID未找到或已过期", description="错误消息")
    error_code: str = Field(default="TRACKER_NOT_FOUND", description="错误代码")


class TrackerErrorResponse(BaseModel):
    """跟踪查询错误响应模式"""
    success: bool = Field(default=False, description="操作是否成功")
    message: str = Field(..., description="错误消息")
    error_code: str = Field(..., description="错误代码")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")


class TrackerSuccessResponse(BaseModel):
    """跟踪查询成功响应模式"""
    success: bool = Field(default=True, description="操作是否成功")
    message: str = Field(default="查询成功", description="响应消息")
    data: TrackerStatusResponse = Field(..., description="跟踪状态数据")