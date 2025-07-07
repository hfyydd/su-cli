from datetime import datetime
from langchain_core.tools import Tool

def _get_current_time_impl(input_text: str = "") -> str:
    """获取当前时间的具体实现"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 使用Tool类直接创建，避免装饰器问题
get_current_time = Tool(
    name="get_current_time",
    description="获取当前时间",
    func=_get_current_time_impl
)