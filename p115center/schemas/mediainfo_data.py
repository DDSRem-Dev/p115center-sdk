__all__ = ["UploadMediaInfoData"]


from pydantic import BaseModel, Field


class UploadMediaInfoData(BaseModel):
    """
    上传媒体信息返回数据
    """

    inserted_count: int = Field(..., description="新插入的文档数量")
    modified_count: int = Field(..., description="已存在并被更新的文档数量")
    total_processed: int = Field(..., description="本次请求处理的总文件数")
