__all__ = ["UserSpeedStatus"]


from typing import Literal, Optional

from pydantic import BaseModel, Field


class UserSpeedStatus(BaseModel):
    """
    单个用户速度状态的详细信息
    """

    status: Literal["fast", "slow", "undetermined"] = Field(
        ..., description="用户的速度状态"
    )
    user_average_speed_mbps: Optional[float] = Field(
        None, description="用于判断的用户平均速度 (MB/s)"
    )
    fastest_user_speed_mbps: Optional[float] = Field(
        None, description="所有用户内最快上传速度 (MB/s)"
    )
    records_used: int = Field(..., description="用于计算本次状态的记录数量")
    data_retrieval_method: Literal["standard_window", "extended_search", "no_data"] = (
        Field(..., description="数据获取方式")
    )
    median_benchmark_speed_mbps: Optional[float] = Field(
        None, description="当前全局的基准中位数速度 (MB/s)"
    )
