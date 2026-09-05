from typing import NotRequired, TypedDict

from app.entities.column_info import ColumnInfo


class DataAgentState(TypedDict):
    query: str # 用户输入的查询
    keywords: list[str] # 抽取的关键词
    retrieved_column_infos: list[ColumnInfo] # 检索到的字段信息
    error: NotRequired[str | None] # 校验SQL时出现的错误信息，无错时为 None

