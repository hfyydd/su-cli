
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from src.agent.state import State
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from src.agent.utils import create_agent
from src.agent.prompts import system_prompt 
from src.agent.tools import get_current_time

load_dotenv()

# 创建ChatOpenAI实例
model_name = os.getenv("DEEPSEEK_MODEL") or os.getenv("MODEL_NAME")
llm = ChatOpenAI(
    model=model_name,
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    temperature=0
)

async def chatbot_node(state: State):
    """聊天机器人节点"""
    try:
        # 创建agent，添加系统提示
        agent = create_agent("chatbot", llm, [get_current_time], system_prompt)
        
        # create_react_agent需要传入整个状态，而不是消息列表
        response = await agent.ainvoke(state)
        
        # create_react_agent返回字典格式 {'messages': [...]}
        # 需要提取新消息（agent的回复），而不是替换整个消息列表
        if isinstance(response, dict) and 'messages' in response:
            # 获取新消息（通常是最后一条，即agent的回复）
            new_messages = response['messages'][len(state['messages']):]
            return {"messages": new_messages}
        else:
            # 如果格式不符合预期，直接返回
            return response
        
    except Exception as e:
        # 静默处理错误，避免显示技术细节
        raise e


def _build_base_graph():
    """构建基础图结构"""
    builder = StateGraph(State)
    
    # 添加节点
    builder.add_node("chatbot", chatbot_node)
    
    # 添加边
    builder.add_edge(START, "chatbot")
    builder.add_edge("chatbot", END)
    
    return builder


def build_graph():
    """构建不带内存的图"""
    builder = _build_base_graph()
    return builder.compile()


def build_graph_with_memory():
    """构建带内存的图"""
    # 使用持久内存保存对话历史
    memory = MemorySaver()
    
    builder = _build_base_graph()
    return builder.compile(checkpointer=memory)


# 默认图（不带内存）
graph = build_graph()




