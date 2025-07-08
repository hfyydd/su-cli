# 文件系统 MCP 使用说明

## 概述

本项目已成功集成**官方文件系统 MCP 服务器** (`@modelcontextprotocol/server-filesystem`)，支持安全的本地文件操作，并在执行前要求用户确认。

## 🧠 智能图结构

```
用户输入 → chatbot 节点 ┬→ tool 节点 → 结束
                ↓      │       ↓
            分析消息内容 │   触发文件系统确认中断
            判断是否需要 │
            文件操作    │
                      └→ 直接结束（普通对话）
```

### 智能路由逻辑
- **普通对话**：直接由 chatbot 处理并结束，不调用 MCP 工具
- **文件操作请求**：chatbot 分析后转入 tool 节点进行文件操作

## 🔧 已集成的文件系统工具

系统提供 **12 个强大的文件操作工具**：

### 📁 文件读取
1. **read_file** - 读取单个文件内容，支持多种编码
2. **read_multiple_files** - 同时读取多个文件，提高效率

### ✏️ 文件写入与编辑  
3. **write_file** - 创建新文件或完全覆盖现有文件
4. **edit_file** - 基于行的文件编辑，返回 git 风格的差异

### 📂 目录操作
5. **create_directory** - 创建目录，支持嵌套创建
6. **list_directory** - 列出目录内容，区分文件和文件夹
7. **list_directory_with_sizes** - 带文件大小的目录列表
8. **directory_tree** - 递归树形结构 JSON 格式

### 🔍 文件管理
9. **move_file** - 移动/重命名文件和目录
10. **search_files** - 递归搜索匹配模式的文件
11. **get_file_info** - 获取文件详细元数据（大小、时间、权限）
12. **list_allowed_directories** - 显示允许访问的目录

## 🎯 智能识别功能

系统能够智能识别用户消息类型，只在需要时调用 MCP 工具：

### 📝 普通对话（不调用 MCP）
```
用户：你好，今天天气怎么样？
AI：直接回复 → 结束（无 MCP 调用）

用户：什么是人工智能？
AI：直接回复 → 结束（无 MCP 调用）

用户：帮我解释一下这个概念
AI：直接回复 → 结束（无 MCP 调用）
```

### 📁 文件操作请求（自动调用 MCP）
```
用户：帮我创建一个文件
AI：分析需要文件操作 → 触发 MCP 确认 → 执行操作

用户：列出桌面上的文件
AI：分析需要文件操作 → 触发 MCP 确认 → 执行操作

用户：读取某个文件的内容
AI：分析需要文件操作 → 触发 MCP 确认 → 执行操作
```

### 🔍 关键词识别

系统通过以下关键词识别文件操作需求：
- **文件相关**：文件、桌面、下载、目录、文件夹
- **操作相关**：创建、读取、列出、搜索、删除、移动、保存、打开

## 🛡️ 安全配置

### 允许访问的路径
- **桌面**：`/Users/username/Desktop`
- **下载**：`/Users/username/Downloads`

### 安全机制
- ✅ **路径限制**：只能操作指定目录内的文件
- ✅ **用户确认**：每次文件操作都需要用户明确同意
- ✅ **错误处理**：完善的错误信息和解决方案提示

## MCP 服务器配置

在 `tool_node` 函数中，您可以配置 MCP 服务器：

```python
# 示例 MCP 服务器配置
mcp_servers = {
    "example_server": {
        "transport": "stdio",
        "command": "python",  # MCP 服务器命令
        "args": ["-c", "print('Hello from MCP')"],  # 命令参数
        "env": {}  # 环境变量
    }
}
```

### 支持的传输类型

1. **stdio** 传输：
```python
{
    "transport": "stdio",
    "command": "uvx",
    "args": ["mcp-server-name"],
    "env": {"API_KEY": "your_api_key"}
}
```

2. **sse** 传输：
```python
{
    "transport": "sse", 
    "url": "http://localhost:3000/sse",
    "env": {"API_KEY": "your_api_key"}
}
```

## 实际使用 MCP 工具

要启用真实的 MCP 工具调用，请在 `tool_node` 函数中取消注释以下代码：

```python
async with MultiServerMCPClient(mcp_servers) as client:
    # 获取可用工具
    tools = client.get_tools()
    
    # 选择并调用工具
    if tools:
        tool = tools[0]
        result = await client.call_tool(tool.name, {})
        mcp_result = f"MCP 工具 '{tool.name}' 执行结果: {result}"
    else:
        mcp_result = "没有可用的 MCP 工具"
```

## 用户交互

### 中断确认格式

当执行到 tool 节点时，系统会触发中断，显示：
```
检测到需要使用 MCP 工具处理请求: [用户消息]
您确认要执行 MCP 工具操作吗？(yes/no)
```

### 用户响应格式

- **接受操作**：`[ACCEPTED]` 
- **拒绝操作**：`[REJECTED]`

## 测试

运行测试文件验证功能：

```bash
python test_mcp_flow.py
```

测试包含：
1. 用户接受 MCP 操作的完整流程
2. 用户拒绝 MCP 操作的处理

## 常用 MCP 服务器示例

### 1. GitHub Trending
```python
{
    "transport": "stdio",
    "command": "uvx", 
    "args": ["mcp-github-trending"]
}
```

### 2. Tavily Search
```python
{
    "transport": "stdio",
    "command": "npx",
    "args": ["-y", "tavily-mcp@0.1.3"],
    "env": {"TAVILY_API_KEY": "your_tavily_key"}
}
```

### 3. 文件系统操作
```python
{
    "transport": "stdio",
    "command": "uvx",
    "args": ["mcp-server-filesystem", "/path/to/allowed/directory"]
}
```

## 注意事项

1. **安全性**：MCP 工具可能访问外部资源，用户确认是重要的安全机制
2. **配置**：根据实际需求配置 MCP 服务器的命令和参数
3. **错误处理**：已包含完整的错误处理，MCP 调用失败会返回错误信息
4. **环境变量**：敏感信息（如 API 密钥）应通过环境变量传递

## 扩展功能

可以根据需要扩展 tool 节点功能：
- 根据用户消息智能选择合适的 MCP 工具
- 支持多个 MCP 服务器并行调用
- 添加工具调用结果的后处理逻辑 