# backend/models/processed_jd.py
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from beanie import Document, PydanticObjectId # 移除 Indexed，因为我们将直接用 IndexModel
import pymongo # 导入 pymongo 以使用 ASCENDING 和 IndexModel
from pymongo import IndexModel # 明确导入 IndexModel
from pydantic import BaseModel, EmailStr, Field # Correct


class ProcessedJD(Document):
    jd_text: str
    keywords: List[str]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expire_at: Optional[datetime] = None

    class Settings:
        name = "processed_jds"
        indexes = [
            # TTL 索引: MongoDB 会在 expire_at 时间点自动删除文档
            # expireAfterSeconds=0 表示文档在 expire_at 指定的时间精确过期
            # 使用 pymongo.IndexModel 来定义索引
            IndexModel(
                keys=[("expire_at", pymongo.ASCENDING)], 
                name="expire_at_ttl_index", # 给索引起一个名字是个好习惯
                expireAfterSeconds=0
            )
            # 如果您还有其他普通字段索引，例如：
            # IndexModel(keys=[("keywords", pymongo.ASCENDING)], name="keywords_index")
        ]