#!/usr/bin/env python3
"""
MCP 集成测试脚本

运行此脚本来验证 MCP 工具是否正确加载和工作。
"""

import asyncio
import logging
import sys
from pathlib import Path

# 设置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 添加项目路径到 sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.agent.mcp_utils import MCPToolManager
from src.agent.tools import get_all_tools, load_mcp_tools, initialize_tools

async def test_mcp_manager():
    """测试 MCP 工具管理器"""
    print("🔧 测试 MCP 工具管理器...")
    
    manager = MCPToolManager()
    print(f"📝 配置文件路径: {manager.config_path}")
    print(f"📋 配置内容: {manager.config}")
    
    # 加载工具
    tools = await manager.load_tools()
    print(f"✅ 成功加载 {len(tools)} 个 MCP 工具")
    
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")
    
    return tools

def test_tools_integration():
    """测试工具集成"""
    print("\n🔗 测试工具集成...")
    
    # 初始化工具
    success = initialize_tools()
    print(f"🚀 工具初始化: {'成功' if success else '失败'}")
    
    # 获取所有工具
    all_tools = get_all_tools()
    print(f"📦 总共可用工具: {len(all_tools)} 个")
    
    for tool in all_tools:
        print(f"  - {tool.name}: {tool.description}")
    
    return all_tools

async def test_tool_execution(tools):
    """测试工具执行"""
    print("\n⚡ 测试工具执行...")
    
    # 测试本地工具
    for tool in tools:
        if tool.name == "get_current_time":
            try:
                result = tool.invoke("")
                print(f"✅ {tool.name}: {result}")
            except Exception as e:
                print(f"❌ {tool.name}: 执行失败 - {e}")
            break
    
    # 如果有 MCP 工具，尝试测试一个简单的工具
    mcp_tools = [t for t in tools if hasattr(t, '_source') or 'mcp' in str(type(t)).lower()]
    if mcp_tools:
        print(f"🎯 找到 {len(mcp_tools)} 个 MCP 工具，尝试执行第一个...")
        tool = mcp_tools[0]
        try:
            # 注意：这里只是尝试，某些工具可能需要特定参数
            print(f"🔍 工具 {tool.name} 准备就绪")
        except Exception as e:
            print(f"⚠️  工具 {tool.name} 测试跳过: {e}")

async def main():
    """主测试函数"""
    print("🧪 MCP 集成测试开始\n")
    print("=" * 50)
    
    try:
        # 测试 MCP 管理器
        mcp_tools = await test_mcp_manager()
        
        # 测试工具集成
        all_tools = test_tools_integration()
        
        # 测试工具执行
        await test_tool_execution(all_tools)
        
        print("\n" + "=" * 50)
        print("✅ 测试完成！")
        print(f"📊 总结:")
        print(f"  - MCP 工具: {len(mcp_tools)} 个")
        print(f"  - 总工具数: {len(all_tools)} 个")
        
        if len(mcp_tools) == 0:
            print("\n💡 提示:")
            print("  - 检查 mcp_config.json 文件是否存在")
            print("  - 确保已安装相关的 MCP 服务器包")
            print("  - 查看日志了解详细错误信息")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 