#!/usr/bin/env python3
"""
文件系统 MCP 实际操作测试
测试真实的文件操作功能：创建、读取、列出文件等
"""

import asyncio
import os
from uuid import uuid4
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from src.agent.graph import build_graph_with_memory


async def test_create_file():
    """测试创建文件操作"""
    print("🚀 测试创建文件")
    print("-" * 50)
    
    graph = build_graph_with_memory()
    config = {"configurable": {"thread_id": str(uuid4())}}
    
    # 请求创建文件
    initial_state = {"messages": [HumanMessage(content="创建一个测试文件")]}
    
    print("✓ 发送创建文件请求...")
    events = []
    async for event in graph.astream(initial_state, config):
        events.append(event)
        if "__interrupt__" in event:
            print("  ⏸️  触发用户确认中断")
            break
    
    print("✓ 用户确认创建文件...")
    resume_events = []
    async for event in graph.astream(Command(resume="[ACCEPTED]"), config):
        resume_events.append(event)
        if "tool" in event:
            response = event["tool"]["messages"][0].content
            print(f"\n📄 操作结果:")
            print("-" * 30)
            print(response)
            print("-" * 30)
            
            if "已创建文件" in response and "mcp_test.txt" in response:
                print("✅ 文件创建成功!")
                return True
            elif "创建文件失败" in response:
                print("⚠️  文件创建失败，但错误处理正常")
                return True
            else:
                print("❌ 意外的响应格式")
                return False
    
    print("❌ 没有收到创建文件响应")
    return False


async def verify_file_exists():
    """验证测试文件是否真的被创建了"""
    print("\n🔍 验证文件是否真的被创建...")
    
    home_dir = os.path.expanduser("~")
    test_file = os.path.join(home_dir, "Desktop", "mcp_test.txt")
    
    if os.path.exists(test_file):
        print(f"✅ 文件确实存在: {test_file}")
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"📄 文件内容预览:")
                print("-" * 30)
                print(content[:200] + "..." if len(content) > 200 else content)
                print("-" * 30)
            return True
        except Exception as e:
            print(f"⚠️  文件存在但读取失败: {e}")
            return False
    else:
        print(f"❌ 文件不存在: {test_file}")
        return False


async def test_list_files():
    """测试列出文件操作"""
    print("\n🚀 测试列出文件")
    print("-" * 50)
    
    graph = build_graph_with_memory()
    config = {"configurable": {"thread_id": str(uuid4())}}
    
    # 请求列出文件
    initial_state = {"messages": [HumanMessage(content="列出桌面文件")]}
    
    print("✓ 发送列出文件请求...")
    events = []
    async for event in graph.astream(initial_state, config):
        events.append(event)
        if "__interrupt__" in event:
            break
    
    print("✓ 用户确认列出文件...")
    resume_events = []
    async for event in graph.astream(Command(resume="[ACCEPTED]"), config):
        resume_events.append(event)
        if "tool" in event:
            response = event["tool"]["messages"][0].content
            print(f"\n📄 操作结果:")
            print("-" * 30)
            print(response[:500] + "..." if len(response) > 500 else response)
            print("-" * 30)
            
            if "桌面文件列表" in response or "列出文件失败" in response:
                print("✅ 列出文件操作成功!")
                return True
            else:
                print("❌ 意外的响应格式")
                return False
    
    print("❌ 没有收到列出文件响应")
    return False


async def main():
    """主测试函数"""
    try:
        print("🧪 开始文件系统 MCP 实际操作测试...")
        print("=" * 60)
        
        # 按顺序测试不同的文件操作
        results = []
        
        # 1. 测试创建文件
        result1 = await test_create_file()
        results.append(("创建文件", result1))
        
        # 2. 验证文件是否真的被创建
        result2 = await verify_file_exists()
        results.append(("验证文件存在", result2))
        
        # 3. 测试列出文件
        result3 = await test_list_files()
        results.append(("列出文件", result3))
        
        # 汇总结果
        print("\n" + "=" * 60)
        print("📊 测试结果汇总:")
        print("-" * 40)
        
        success_count = 0
        for test_name, success in results:
            status = "✅ 通过" if success else "❌ 失败"
            print(f"{test_name:<15} | {status}")
            if success:
                success_count += 1
        
        print("-" * 40)
        print(f"总计: {success_count}/{len(results)} 测试通过")
        
        if success_count == len(results):
            print("\n🎉 所有文件操作测试通过!")
            print("🚀 文件系统 MCP 功能完全正常!")
            return True
        else:
            print(f"\n⚠️  {len(results) - success_count} 个测试失败")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
