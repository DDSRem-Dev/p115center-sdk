__all__ = ["UploadInfo", "UploadInfoRes"]


from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UploadInfo(BaseModel):
    """
    上传文件信息
    """

    file_sha1: str = Field(..., description="文件 SHA1 哈希")
    first_sha1: str = Field(..., description="第一段 SHA1")
    second_auth: bool = Field(..., description="是否启用二次验证")
    second_sha1: Optional[str] = Field(None, description="二次 SHA1（二次验证时存在）")
    file_size: str = Field(..., description="文件大小")
    file_name: str = Field(..., description="文件名")
    time: int = Field(..., description="上传耗时")
    postime: datetime = Field(..., description="上传时间")


class UploadInfoRes(UploadInfo):
    """
    上传文件信息返回
    """

    id_: str = Field(..., alias="_id", description="用户 ID")
    owner_id: str = Field(..., description="用户 ID")
