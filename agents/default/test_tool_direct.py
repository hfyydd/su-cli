#!/usr/bin/env python3
"""
直接测试工具调用功能
"""

import asyncio
import sys

# 添加项目路径
sys.path.insert(0, 'src')

async def test_direct_tool_call():
    """直接测试工具调用"""
    try:
        from agent.tools import get_all_tools_async
        
        # 获取工具
        tools = await get_all_tools_async()
        print(f"🔧 获取到 {len(tools)} 个工具")
        
        # 找到 list_directory 工具
        list_dir_tool = None
        for tool in tools:
            if tool.name == "list_directory":
                list_dir_tool = tool
                break
        
        if list_dir_tool:
            print(f"✅ 找到 list_directory 工具: {list_dir_tool.description}")
            
            # 直接调用工具（异步）
            print("\n🚀 直接调用 list_directory 工具...")
            result = await list_dir_tool.ainvoke({"path": "/Users/hanfeng/Desktop"})
            print("📋 桌面文件列表:")
            print(result)
            
            return True
        else:
            print("❌ 未找到 list_directory 工具")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 直接测试工具调用\n")
    success = asyncio.run(test_direct_tool_call())
    print(f"\n📊 测试结果: {'✅ 成功' if success else '❌ 失败'}") 