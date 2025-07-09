import asyncio
import logging
from datetime import datetime
from typing import List

from langchain_core.tools import Tool

from .mcp_utils import MCPToolManager

logger = logging.getLogger(__name__)

def _get_current_time_impl(input_text: str = "") -> str:
    """获取当前时间的具体实现"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 使用Tool类直接创建，避免装饰器问题
get_current_time = Tool(
    name="get_current_time",
    description="获取当前时间",
    func=_get_current_time_impl
)

# MCP 工具管理器实例
mcp_manager = MCPToolManager()

def get_all_tools() -> List[Tool]:
    """获取所有可用的工具，包括本地工具和 MCP 工具
    
    Returns:
        包含所有工具的列表
    """
    # 本地工具
    local_tools = [get_current_time]
    
    # 获取已加载的 MCP 工具
    mcp_tools = mcp_manager.get_loaded_tools()
    
    # 合并所有工具
    all_tools = local_tools + mcp_tools
    logger.debug(f"总共提供 {len(all_tools)} 个工具 (本地: {len(local_tools)}, MCP: {len(mcp_tools)})")
    
    return all_tools

async def load_mcp_tools() -> List[Tool]:
    """异步加载 MCP 工具
    
    Returns:
        MCP 工具列表
    """
    try:
        mcp_tools = await mcp_manager.load_tools()
        logger.debug(f"成功加载 {len(mcp_tools)} 个 MCP 工具")
        return mcp_tools
    except Exception as e:
        logger.error(f"加载 MCP 工具失败: {e}")
        return []

def initialize_tools():
    """初始化所有工具（包括 MCP 工具）
    
    这个函数应该在应用启动时调用，以确保 MCP 工具被正确加载
    """
    try:
        # 在新的事件循环中运行异步函数
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        mcp_tools = loop.run_until_complete(load_mcp_tools())
        loop.close()
        
        logger.debug("工具初始化完成")
        return True
    except Exception as e:
        logger.error(f"工具初始化失败: {e}")
        return False

# 全局 MCP 管理器，用于在整个应用生命周期中维持连接
_global_mcp_manager = None

async def get_mcp_manager():
    """获取全局 MCP 管理器实例"""
    global _global_mcp_manager
    if _global_mcp_manager is None:
        _global_mcp_manager = MCPToolManager()
        await _global_mcp_manager.load_tools()
    return _global_mcp_manager

async def get_all_tools_async() -> List[Tool]:
    """异步获取所有可用的工具，确保 MCP 工具已加载
    
    Returns:
        包含所有工具的列表
    """
    # 本地工具
    local_tools = [get_current_time]
    
    try:
        # 获取 MCP 管理器并加载工具
        mcp_manager = await get_mcp_manager()
        mcp_tools = mcp_manager.get_loaded_tools()
        
        # 合并所有工具
        all_tools = local_tools + mcp_tools
        logger.debug(f"总共提供 {len(all_tools)} 个工具 (本地: {len(local_tools)}, MCP: {len(mcp_tools)})")
        
        return all_tools
    except Exception as e:
        logger.error(f"获取 MCP 工具失败: {e}")
        return local_tools

async def close_mcp_manager():
    """关闭全局 MCP 管理器"""
    global _global_mcp_manager
    if _global_mcp_manager:
        await _global_mcp_manager.close()
        _global_mcp_manager = None

