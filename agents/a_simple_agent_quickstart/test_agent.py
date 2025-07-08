#!/usr/bin/env python3
"""
a_simple_agent 测试用例

测试场景：
1. 基本对话流程
2. MCP 工具确认接受
3. MCP 工具确认拒绝
4. 错误处理
5. 图结构验证
"""

import asyncio
import pytest
from uuid import uuid4
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.types import Command

from src.agent.graph import build_graph_with_memory, build_graph
from src.agent.state import State


class TestSimpleAgent:
    """a_simple_agent 测试类"""
    
    def setup_method(self):
        """每个测试方法前的准备工作"""
        self.graph = build_graph_with_memory()
        self.config = {
            "configurable": {
                "thread_id": str(uuid4())
            }
        }
    
    async def run_until_interrupt_or_end(self, initial_state):
        """运行图直到中断或结束，返回事件列表和最后状态"""
        events = []
        last_state = None
        
        async for event in self.graph.astream(initial_state, self.config):
            events.append(event)
            last_state = event
            
            # 如果遇到中断，停止
            if "__interrupt__" in event:
                break
                
        return events, last_state
    
    async def resume_with_confirmation(self, confirmation):
        """使用确认信息恢复图的执行"""
        events = []
        
        async for event in self.graph.astream(
            Command(resume=confirmation), 
            self.config
        ):
            events.append(event)
            
        return events

    async def test_basic_conversation_flow(self):
        """测试基本对话流程"""
        print("\n🧪 测试 1: 基本对话流程")
        
        initial_state = {
            "messages": [HumanMessage(content="你好")]
        }
        
        events, last_state = await self.run_until_interrupt_or_end(initial_state)
        
        # 验证chatbot节点执行成功
        assert any("chatbot" in event for event in events), "chatbot节点应该被执行"
        
        # 验证会触发MCP中断
        assert "__interrupt__" in last_state, "应该触发MCP确认中断"
        
        interrupt_data = last_state["__interrupt__"][0].value
        assert interrupt_data["type"] == "mcp_confirmation", "中断类型应该是mcp_confirmation"
        assert "您确认要执行 MCP 工具操作吗？" in interrupt_data["question"], "应该包含MCP确认问题"
        
        print("✅ 基本对话流程测试通过")

    async def test_mcp_confirmation_accepted(self):
        """测试MCP确认接受的情况"""
        print("\n🧪 测试 2: MCP确认接受")
        
        initial_state = {
            "messages": [HumanMessage(content="请帮我搜索信息")]
        }
        
        # 执行到中断
        events, last_state = await self.run_until_interrupt_or_end(initial_state)
        assert "__interrupt__" in last_state, "应该触发中断"
        
        # 用户确认接受
        resume_events = await self.resume_with_confirmation("[ACCEPTED]")
        
        # 验证tool节点执行成功
        assert any("tool" in event for event in resume_events), "tool节点应该被执行"
        
        # 验证返回成功消息
        tool_event = next(event for event in resume_events if "tool" in event)
        tool_messages = tool_event["tool"]["messages"]
        assert len(tool_messages) > 0, "tool节点应该返回消息"
        assert "✅ MCP 工具已成功处理请求" in tool_messages[0].content, "应该返回成功消息"
        
        print("✅ MCP确认接受测试通过")

    async def test_mcp_confirmation_rejected(self):
        """测试MCP确认拒绝的情况"""
        print("\n🧪 测试 3: MCP确认拒绝")
        
        initial_state = {
            "messages": [HumanMessage(content="请帮我处理文件")]
        }
        
        # 执行到中断
        events, last_state = await self.run_until_interrupt_or_end(initial_state)
        assert "__interrupt__" in last_state, "应该触发中断"
        
        # 用户确认拒绝
        resume_events = await self.resume_with_confirmation("[REJECTED]")
        
        # 验证tool节点执行并返回取消消息
        assert any("tool" in event for event in resume_events), "tool节点应该被执行"
        
        tool_event = next(event for event in resume_events if "tool" in event)
        tool_messages = tool_event["tool"]["messages"]
        assert len(tool_messages) > 0, "tool节点应该返回消息"
        assert "好的，我已取消 MCP 工具操作" in tool_messages[0].content, "应该返回取消消息"
        
        print("✅ MCP确认拒绝测试通过")

    async def test_invalid_confirmation_format(self):
        """测试无效确认格式的处理"""
        print("\n🧪 测试 4: 无效确认格式")
        
        initial_state = {
            "messages": [HumanMessage(content="测试无效格式")]
        }
        
        # 执行到中断
        events, last_state = await self.run_until_interrupt_or_end(initial_state)
        assert "__interrupt__" in last_state, "应该触发中断"
        
        # 提供无效格式的确认
        resume_events = await self.resume_with_confirmation("invalid_format")
        
        # 验证返回格式错误消息
        tool_event = next(event for event in resume_events if "tool" in event)
        tool_messages = tool_event["tool"]["messages"]
        assert "输入格式不正确，已取消 MCP 工具操作" in tool_messages[0].content, "应该返回格式错误消息"
        
        print("✅ 无效确认格式测试通过")

    async def test_graph_structure(self):
        """测试图结构"""
        print("\n🧪 测试 5: 图结构验证")
        
        # 获取图的节点和边
        nodes = list(self.graph.nodes.keys())
        
        # 验证节点存在
        assert "chatbot" in nodes, "应该包含chatbot节点"
        assert "tool" in nodes, "应该包含tool节点"
        
        # 验证图可以正常编译
        assert self.graph is not None, "图应该能正常编译"
        
        print("✅ 图结构验证通过")

    async def test_message_flow(self):
        """测试消息流转"""
        print("\n🧪 测试 6: 消息流转")
        
        test_messages = [
            "你能帮我写代码吗？",
            "今天天气怎么样？", 
            "请搜索最新的技术新闻"
        ]
        
        for msg in test_messages:
            initial_state = {"messages": [HumanMessage(content=msg)]}
            
            # 执行到中断
            events, last_state = await self.run_until_interrupt_or_end(initial_state)
            
            # 验证chatbot响应
            chatbot_event = next((event for event in events if "chatbot" in event), None)
            assert chatbot_event is not None, f"消息'{msg}'应该触发chatbot响应"
            
            # 验证中断触发
            assert "__interrupt__" in last_state, f"消息'{msg}'应该触发MCP中断"
            
            # 接受并完成流程
            resume_events = await self.resume_with_confirmation("[ACCEPTED]")
            assert any("tool" in event for event in resume_events), f"消息'{msg}'应该完成tool节点执行"
        
        print("✅ 消息流转测试通过")

    async def test_state_persistence(self):
        """测试状态持久化"""
        print("\n🧪 测试 7: 状态持久化")
        
        initial_state = {
            "messages": [HumanMessage(content="测试状态持久化")]
        }
        
        # 第一次执行到中断
        events1, last_state1 = await self.run_until_interrupt_or_end(initial_state)
        
        # 使用相同的配置恢复执行
        resume_events = await self.resume_with_confirmation("[ACCEPTED]")
        
        # 验证状态得到保持和正确恢复
        assert len(resume_events) > 0, "应该能够正确恢复执行"
        
        print("✅ 状态持久化测试通过")


async def run_all_tests():
    """运行所有测试"""
    print("🚀 开始运行 a_simple_agent 测试套件")
    print("=" * 60)
    
    test_instance = TestSimpleAgent()
    
    test_methods = [
        test_instance.test_basic_conversation_flow,
        test_instance.test_mcp_confirmation_accepted, 
        test_instance.test_mcp_confirmation_rejected,
        test_instance.test_invalid_confirmation_format,
        test_instance.test_graph_structure,
        test_instance.test_message_flow,
        test_instance.test_state_persistence
    ]
    
    passed = 0
    failed = 0
    
    for test_method in test_methods:
        try:
            # 重新初始化测试实例
            test_instance.setup_method()
            await test_method()
            passed += 1
        except Exception as e:
            print(f"❌ 测试失败: {test_method.__name__}")
            print(f"   错误: {e}")
            failed += 1
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed} 通过, {failed} 失败")
    
    if failed == 0:
        print("🎉 所有测试通过!")
    else:
        print("⚠️  部分测试失败，请检查错误信息")
    
    return failed == 0


async def test_manual_interaction():
    """手动交互测试 - 模拟真实用户交互"""
    print("\n🎮 手动交互测试")
    print("=" * 40)
    
    graph = build_graph_with_memory()
    config = {
        "configurable": {
            "thread_id": str(uuid4())
        }
    }
    
    # 模拟用户输入
    user_input = "请帮我查找关于Python的信息"
    print(f"👤 用户输入: {user_input}")
    
    initial_state = {
        "messages": [HumanMessage(content=user_input)]
    }
    
    print("\n📊 执行流程:")
    
    # 执行到中断
    events = []
    async for event in graph.astream(initial_state, config):
        events.append(event)
        print(f"   事件: {list(event.keys())}")
        
        if "__interrupt__" in event:
            interrupt_data = event["__interrupt__"][0].value
            print(f"\n⏸️  系统中断:")
            print(f"   消息: {interrupt_data['message']}")
            print(f"   问题: {interrupt_data['question']}")
            
            # 模拟用户确认
            user_choice = "[ACCEPTED]"  # 可以改为 "[REJECTED]" 测试拒绝情况
            print(f"\n👤 用户选择: {user_choice}")
            
            # 恢复执行
            print("\n📊 恢复执行:")
            async for event in graph.astream(Command(resume=user_choice), config):
                print(f"   事件: {list(event.keys())}")
                if "tool" in event:
                    tool_response = event["tool"]["messages"][0].content
                    print(f"\n🤖 工具响应: {tool_response}")
            
            break
    
    print("\n✅ 手动交互测试完成")


if __name__ == "__main__":
    # 运行所有自动化测试
    success = asyncio.run(run_all_tests())
    
    # 运行手动交互测试
    asyncio.run(test_manual_interaction())
    
    # 退出码
    exit(0 if success else 1) 