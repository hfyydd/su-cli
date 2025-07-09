#!/usr/bin/env python3
"""
简单的 MCP 测试脚本

仅测试 MCP 工具管理器的核心功能，不依赖整个项目。
"""

import asyncio
import logging
import json
from pathlib import Path

# 设置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_config_file():
    """测试配置文件"""
    print("📋 测试 MCP 配置文件...")
    
    config_path = Path("mcp_config.json")
    if not config_path.exists():
        print("❌ mcp_config.json 文件不存在")
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(f"✅ 配置文件读取成功")
        print(f"📝 配置内容: {json.dumps(config, indent=2, ensure_ascii=False)}")
        
        mcp_servers = config.get("mcpServers", {})
        print(f"🔧 配置了 {len(mcp_servers)} 个 MCP 服务器")
        
        for name, server_config in mcp_servers.items():
            print(f"  - {name}: {server_config.get('command', 'unknown')} {server_config.get('args', [])}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置文件读取失败: {e}")
        return False

async def test_mcp_tool_loading():
    """测试 MCP 工具加载"""
    print("\n🔧 测试 MCP 工具加载...")
    
    try:
        from langchain_mcp_adapters.tools import load_mcp_tools
        from langchain_mcp_adapters.sessions import StdioConnection, create_session
        
        print("✅ MCP 相关库导入成功")
        
        # 测试一个简单的文件系统服务器
        # 注意：这需要安装 @modelcontextprotocol/server-filesystem
        connection = StdioConnection(
            transport="stdio",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            env={},
        )
        
        print("🚀 尝试连接到文件系统 MCP 服务器...")
        
        # 设置较短的超时时间用于测试
        try:
            async def load_tools_with_session():
                async with create_session(connection) as session:
                    return await load_mcp_tools(session)
            
            tools = await asyncio.wait_for(
                load_tools_with_session(),
                timeout=30  # 30秒超时
            )
            
            print(f"✅ 成功加载 {len(tools)} 个工具:")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
            
            return True
            
        except asyncio.TimeoutError:
            print("⏰ 连接超时 - 可能需要安装 MCP 服务器或检查网络")
            return False
        except Exception as e:
            print(f"⚠️  连接失败: {e}")
            print("💡 提示: 可能需要运行 'npm install -g @modelcontextprotocol/server-filesystem'")
            return False
        
    except ImportError as e:
        print(f"❌ MCP 库导入失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🧪 简单 MCP 测试开始\n")
    print("=" * 60)
    
    # 测试配置文件
    config_ok = test_config_file()
    
    if config_ok:
        # 测试工具加载
        tools_ok = await test_mcp_tool_loading()
    else:
        tools_ok = False
    
    print("\n" + "=" * 60)
    print("📊 测试总结:")
    print(f"  - 配置文件: {'✅ 通过' if config_ok else '❌ 失败'}")
    print(f"  - 工具加载: {'✅ 通过' if tools_ok else '❌ 失败'}")
    
    if not config_ok:
        print("\n💡 要开始使用 MCP:")
        print("1. 确保 mcp_config.json 文件存在且格式正确")
        print("2. 配置你需要的 MCP 服务器")
    
    if config_ok and not tools_ok:
        print("\n💡 要修复工具加载问题:")
        print("1. 安装 MCP 服务器: npm install -g @modelcontextprotocol/server-filesystem")
        print("2. 检查网络连接")
        print("3. 确保配置的命令和参数正确")

if __name__ == "__main__":
    asyncio.run(main()) 