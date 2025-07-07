#!/usr/bin/env python3
"""
测试中断功能的简单脚本
"""
import asyncio
import sys
import uuid
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agent.graph import graph
from langchain_core.messages import HumanMessage
from langgraph.types import Command


async def test_interrupt():
    """测试中断功能"""
    print("🧪 测试中断功能...")
    
    # 创建测试状态
    state = {
        "messages": [HumanMessage(content="你好，请帮我做一些任务")],
        "confirmed": None,
        "user_input": None
    }
    
    # 配置线程ID
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    
    try:
        print("📤 发送初始请求...")
        # 第一次调用，应该会遇到中断
        result = await graph.ainvoke(state, config=config)
        
        if '__interrupt__' in result:
            interrupt_info = result['__interrupt__'][0]
            interrupt_data = interrupt_info.value
            
            print(f"⏸️  收到中断请求:")
            print(f"   消息: {interrupt_data.get('message', 'N/A')}")
            print(f"   问题: {interrupt_data.get('question', 'N/A')}")
            
            # 模拟用户确认
            print("✅ 模拟用户确认 'yes'...")
            result = await graph.ainvoke(Command(resume="yes"), config=config)
            
            if 'messages' in result:
                last_message = result['messages'][-1]
                print(f"🤖 Agent回复: {last_message.content}")
                print("✅ 中断功能测试成功！")
            else:
                print("❌ 没有收到预期的消息响应")
                print(f"实际结果: {result}")
                
        else:
            print("❌ 没有收到预期的中断")
            print(f"实际结果: {result}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_interrupt_cancel():
    """测试中断取消功能"""
    print("\n🧪 测试中断取消功能...")
    
    # 创建测试状态
    state = {
        "messages": [HumanMessage(content="你好，请帮我做一些任务")],
        "confirmed": None,
        "user_input": None
    }
    
    # 配置线程ID
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    
    try:
        print("📤 发送初始请求...")
        # 第一次调用，应该会遇到中断
        result = await graph.ainvoke(state, config=config)
        
        if '__interrupt__' in result:
            interrupt_info = result['__interrupt__'][0]
            interrupt_data = interrupt_info.value
            
            print(f"⏸️  收到中断请求:")
            print(f"   消息: {interrupt_data.get('message', 'N/A')}")
            print(f"   问题: {interrupt_data.get('question', 'N/A')}")
            
            # 模拟用户取消
            print("❌ 模拟用户取消 'no'...")
            result = await graph.ainvoke(Command(resume="no"), config=config)
            
            if 'messages' in result and len(result['messages']) > 0:
                last_message = result['messages'][-1]
                print(f"🤖 Agent回复: {last_message.content}")
                if "取消" in last_message.content:
                    print("✅ 中断取消功能测试成功！")
                else:
                    print("❌ 取消功能可能有问题")
            else:
                print("✅ 用户取消后没有产生消息，这是正确的行为")
                
        else:
            print("❌ 没有收到预期的中断")
            print(f"实际结果: {result}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主测试函数"""
    print("🚀 开始测试中断功能\n")
    
    await test_interrupt()
    await test_interrupt_cancel()
    
    print("\n✨ 测试完成！")


if __name__ == "__main__":
    asyncio.run(main()) 