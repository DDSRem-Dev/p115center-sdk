__all__ = ["OfflineInfo", "OfflineInfoRes"]


from datetime import datetime

from pydantic import BaseModel, Field


class OfflineInfo(BaseModel):
    """
    离线下载信息
    """

    url: str = Field(..., description="离线下载链接")
    postime: datetime = Field(..., description="上传数据时间")


class OfflineInfoRes(OfflineInfo):
    """
    离线下载信息返回
    """

    id_: str = Field(..., alias="_id", description="用户 ID")
    owner_id: str = Field(..., description="用户 ID")
