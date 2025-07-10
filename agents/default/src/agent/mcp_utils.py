"""MCP (Model Context Protocol) utilities for loading and managing external tools."""

import json
import logging
import subprocess
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StdioConnection

logger = logging.getLogger(__name__)


class QuietStdioConnection(StdioConnection):
    """自定义的 StdioConnection，减少日志输出"""
    
    def __init__(self, transport: str, command: str, args: List[str], env: Dict[str, str]):
        # 添加环境变量以减少输出
        quiet_env = env.copy()
        quiet_env.update({
            "NODE_ENV": "production",
            "PYTHONUNBUFFERED": "1",
            "MCP_VERBOSE": "false",
            "QUIET": "true"
        })
        
        super().__init__(transport=transport, command=command, args=args, env=quiet_env)
    
    async def __aenter__(self):
        """重写连接建立过程以控制输出"""
        # 临时重定向 stderr 来抑制 MCP 服务器的启动日志
        import sys
        import io
        import contextlib
        
        # 创建一个空的输出缓冲区
        null_buffer = io.StringIO()
        
        # 重定向 stderr 并建立连接
        with contextlib.redirect_stderr(null_buffer):
            try:
                result = await super().__aenter__()
                return result
            except Exception:
                # 如果重定向失败，则直接建立连接
                return await super().__aenter__()


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
                # 修改 NPX 参数以减少日志输出
                command = server_config["command"]
                args = server_config.get("args", []).copy()
                
                # 如果是 npx 命令，添加静默参数
                if command == "npx":
                    # 在 npx 参数前添加 --silent 和 --no-install 以减少输出
                    args = ["--silent", "--no-install"] + args
                
                # 使用自定义的 QuietStdioConnection 以减少日志输出
                connection = QuietStdioConnection(
                    transport="stdio",
                    command=command,
                    args=args,
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
            
            # 创建 MultiServerMCPClient 并获取工具
            # 临时重定向所有输出以抑制 MCP 服务器启动日志
            import sys
            import io
            import contextlib
            import os
            
            # 保存原始的 stdout 和 stderr
            original_stdout = sys.stdout
            original_stderr = sys.stderr
            
            try:
                # 创建空的输出缓冲区
                devnull = io.StringIO()
                
                # 临时重定向所有输出
                sys.stdout = devnull
                sys.stderr = devnull
                
                # 也尝试重定向进程级别的输出
                with open(os.devnull, 'w') as devnull_file:
                    # 临时重定向 stdout/stderr 到 /dev/null
                    old_stdout = os.dup(1)
                    old_stderr = os.dup(2)
                    os.dup2(devnull_file.fileno(), 1)
                    os.dup2(devnull_file.fileno(), 2)
                    
                    try:
                        self.client = MultiServerMCPClient(client_config)
                        tools = await self.client.get_tools()
                    finally:
                        # 恢复原始的 stdout/stderr
                        os.dup2(old_stdout, 1)
                        os.dup2(old_stderr, 2)
                        os.close(old_stdout)
                        os.close(old_stderr)
                        
            finally:
                # 恢复 Python 的 stdout/stderr
                sys.stdout = original_stdout
                sys.stderr = original_stderr
            
            # 显示简化的初始化信息
            server_count = len(client_config)
            if server_count > 0:
                print(f"🔗 {server_count} MCP servers initialized")
            
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