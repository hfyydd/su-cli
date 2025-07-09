"""MCP (Model Context Protocol) utilities for loading and managing external tools."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StdioConnection

logger = logging.getLogger(__name__)


class MCPToolManager:
    """管理 MCP 工具的类"""
    
    def __init__(self, config_path: str = "mcp_config.json"):
        """初始化 MCP 工具管理器
        
        Args:
            config_path: MCP 配置文件路径
        """
        self.config_path = config_path  # 保持为字符串
        self.config = self._load_config()
        self.loaded_tools = []
        self.client = None
    
    def _load_config(self) -> Dict[str, Any]:
        """加载 MCP 配置文件"""
        # 可能的配置文件路径列表
        possible_paths = [
            Path(self.config_path),  # 原始路径
            Path("agents/default") / self.config_path,  # 从根目录查找
            Path(__file__).parent.parent.parent / self.config_path,  # 相对于当前文件
        ]
        
        for config_path in possible_paths:
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        logger.debug(f"已加载 MCP 配置文件: {config_path}")
                        return config
                except Exception as e:
                    logger.error(f"加载 MCP 配置文件失败 ({config_path}): {e}")
                    continue
        
        logger.warning(f"在以下路径都未找到 MCP 配置文件: {[str(p) for p in possible_paths]}")
        return {"mcpServers": {}}
    
    def _convert_config_for_client(self) -> Dict[str, Any]:
        """转换配置格式为 MultiServerMCPClient 所需的格式"""
        mcp_servers = self.config.get("mcpServers", {})
        client_config = {}
        
        for server_name, server_config in mcp_servers.items():
            if "command" in server_config:
                # 创建 stdio 连接对象
                connection = StdioConnection(
                    transport="stdio",
                    command=server_config["command"],
                    args=server_config.get("args", []),
                    env=server_config.get("env", {}),
                )
                client_config[server_name] = connection
        
        return client_config
    
    async def load_tools(self) -> List[Any]:
        """加载所有配置的 MCP 工具"""
        mcp_servers = self.config.get("mcpServers", {})
        if not mcp_servers:
            logger.debug("未配置 MCP 服务器")
            return []
        
        try:
            # 转换配置格式
            client_config = self._convert_config_for_client()
            
            if not client_config:
                logger.warning("没有有效的 MCP 服务器配置")
                return []
            
            # 创建 MultiServerMCPClient
            self.client = MultiServerMCPClient(client_config)
            
            # 获取工具
            tools = await self.client.get_tools()
            
            self.loaded_tools = tools
            logger.debug(f"总共加载了 {len(tools)} 个 MCP 工具")
            
            # 打印工具信息
            for tool in tools:
                logger.debug(f"已加载工具: {tool.name}")
            
            return tools
            
        except Exception as e:
            logger.error(f"加载 MCP 工具失败: {e}")
            return []
    
    def get_loaded_tools(self) -> List[Any]:
        """获取已加载的工具"""
        return self.loaded_tools
    
    async def close(self):
        """关闭 MCP 客户端"""
        if self.client:
            try:
                await self.client.close()
            except Exception as e:
                logger.error(f"关闭 MCP 客户端失败: {e}")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.load_tools()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close() 