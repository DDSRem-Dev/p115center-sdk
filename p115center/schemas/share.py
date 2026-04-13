__all__ = [
    "MediaType",
    "ShareInfo",
    "ShareInfoRes",
    "ShareIterUploadInfo",
    "ShareIterDeleteRes",
    "ShareSnapInvalidEntry",
    "ShareSnapValidateRes",
]


from datetime import datetime
from enum import Enum
from typing import Literal, Optional, Union, Any, List, Dict

from pydantic import BaseModel, Field


class MediaType(Enum):
    """
    媒体类型
    """

    MOVIE = "电影"
    TV = "电视剧"
    COLLECTION = "系列"
    UNKNOWN = "未知"


class ShareInfo(BaseModel):
    """
    分享信息
    """

    url: str = Field(..., description="分享链接")
    source: Optional[str] = Field(None, description="来源：themoviedb、douban、bangumi")
    type: Optional[MediaType] = Field(None, description="类型：电影、电视剧")
    title: Optional[str] = Field(None, description="媒体标题")
    en_title: Optional[str] = Field(None, description="英文标题")
    hk_title: Optional[str] = Field(None, description="香港标题")
    tw_title: Optional[str] = Field(None, description="台湾标题")
    sg_title: Optional[str] = Field(None, description="新加坡标题")
    year: Optional[str] = Field(None, description="年份")
    season: Optional[int] = Field(None, description="季")
    tmdb_id: Optional[int] = Field(None, description="TMDB ID")
    imdb_id: Optional[str] = Field(None, description="IMDB ID")
    tvdb_id: Optional[int] = Field(None, description="TVDB ID")
    douban_id: Optional[str] = Field(None, description="豆瓣 ID")
    bangumi_id: Optional[int] = Field(None, description="Bangumi ID")
    collection_id: Optional[int] = Field(None, description="合集 ID")
    postime: datetime = Field(..., description="上传数据时间")


class ShareInfoRes(ShareInfo):
    """
    分享信息返回
    """

    id_: str = Field(..., alias="_id", description="用户 ID")
    owner_id: str = Field(..., description="用户 ID")


class ShareIterUploadInfo(BaseModel):
    """
    115 分享文件(夹) iter 上传信息
    """

    status: str = Field(..., description="上传状态")
    file_id: str = Field(..., description="文件 ID")
    batch_id: str = Field(..., description="上传 Batch Id")


class ShareIterDeleteRes(BaseModel):
    """
    删除分享文件迭代数据成功响应
    """

    status: Literal["deleted"] = Field(..., description="删除状态")
    batch_id: str = Field(..., description="Batch Id")


class ShareSnapInvalidEntry(BaseModel):
    """
    单组校验失败时的条目
    """

    share_code: str = Field(..., description="分享码")
    receive_code: str = Field(..., description="提取码")
    error: Union[str, Dict[str, Any]] = Field(..., description="错误信息")


class ShareSnapValidateRes(BaseModel):
    """
    批量校验结果
    """

    valid_count: int = Field(..., description="校验通过的数量")
    invalid: List[ShareSnapInvalidEntry] = Field(..., description="校验失败的条目")
