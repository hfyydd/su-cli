#!/usr/bin/env python3
"""
智能路由测试
验证系统只在需要文件操作时才调用 MCP 工具
"""

import asyncio
from uuid import uuid4
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from src.agent.graph import build_graph_with_memory


async def test_no_file_operation():
    """测试普通对话，不应该调用 MCP 工具"""
    print("🚀 测试普通对话（不需要文件操作）")
    print("-" * 50)
    
    graph = build_graph_with_memory()
    config = {"configurable": {"thread_id": str(uuid4())}}
    
    # 普通聊天消息，不涉及文件操作
    initial_state = {"messages": [HumanMessage(content="你好，今天天气怎么样？")]}
    
    print("✓ 发送普通聊天消息...")
    events = []
    final_state = None
    
    async for event in graph.astream(initial_state, config):
        events.append(event)
        print(f"  📊 事件: {list(event.keys())}")
        
        # 保存最终状态
        if event:
            final_state = event
    
    # 检查是否有中断（不应该有）
    has_interrupt = any("__interrupt__" in event for event in events)
    has_tool_execution = any("tool" in event for event in events)
    
    if not has_interrupt and not has_tool_execution:
        print("✅ 正确：普通对话没有调用 MCP 工具")
        return True
    else:
        print(f"❌ 错误：普通对话调用了 MCP 工具 (中断: {has_interrupt}, 工具执行: {has_tool_execution})")
        return False


async def test_file_operation_request():
    """测试文件操作请求，应该调用 MCP 工具"""
    print("\n🚀 测试文件操作请求（需要调用 MCP 工具）")
    print("-" * 50)
    
    graph = build_graph_with_memory()
    config = {"configurable": {"thread_id": str(uuid4())}}
    
    # 文件操作消息
    initial_state = {"messages": [HumanMessage(content="帮我创建一个文件")]}
    
    print("✓ 发送文件操作请求...")
    events = []
    
    async for event in graph.astream(initial_state, config):
        events.append(event)
        print(f"  📊 事件: {list(event.keys())}")
        
        if "__interrupt__" in event:
            print("  ⏸️  触发 MCP 确认中断")
            break
    
    # 检查是否有正确的中断
    has_interrupt = any("__interrupt__" in event for event in events)
    has_chatbot = any("chatbot" in event for event in events)
    
    if has_interrupt and has_chatbot:
        print("✅ 正确：文件操作请求触发了 MCP 工具调用")
        return True
    else:
        print(f"❌ 错误：文件操作请求没有触发 MCP 工具 (中断: {has_interrupt}, chatbot: {has_chatbot})")
        return False


async def main():
    """主测试函数"""
    try:
        print("🧪 开始智能路由测试...")
        print("=" * 60)
        
        results = []
        
        # 1. 测试普通对话
        result1 = await test_no_file_operation()
        results.append(("普通对话", result1))
        
        # 2. 测试文件操作请求
        result2 = await test_file_operation_request()
        results.append(("文件操作请求", result2))
        
        # 汇总结果
        print("\n" + "=" * 60)
        print("📊 智能路由测试结果汇总:")
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
            print("\n🎉 所有智能路由测试通过!")
            print("🧠 智能路由功能工作正常 - 只在需要时调用 MCP 工具!")
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
