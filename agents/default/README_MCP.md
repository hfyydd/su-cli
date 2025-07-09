# MCP (Model Context Protocol) 集成指南

本项目已集成 MCP 支持，允许您轻松添加外部工具来扩展 AI 代理的能力。

## 什么是 MCP？

Model Context Protocol (MCP) 是一个开放标准，允许 AI 助手与外部数据源和工具进行安全、受控的集成。通过 MCP，您可以连接到文件系统、数据库、API、本地服务等。

## 配置 MCP 服务器

### 1. 编辑配置文件

编辑 `mcp_config.json` 文件来配置您的 MCP 服务器：

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
      "env": {}
    },
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "your_brave_api_key_here"
      }
    },
    "github": {
      "command": "uvx",
      "args": ["mcp-server-github", "--repo", "owner/repo"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your_github_token"
      }
    }
  }
}
```

### 2. 配置字段说明

- `command`: 要执行的命令（如 `npx`, `uvx`, `python` 等）
- `args`: 命令参数数组
- `env`: 环境变量字典，用于传递 API 密钥等敏感信息

### 3. 常用 MCP 服务器

以下是一些常用的 MCP 服务器：

#### 文件系统访问
```json
"filesystem": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/directory"],
  "env": {}
}
```

#### 网络搜索 (Brave)
```json
"brave-search": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-brave-search"],
  "env": {
    "BRAVE_API_KEY": "your_api_key"
  }
}
```

#### GitHub 集成
```json
"github": {
  "command": "uvx",
  "args": ["mcp-server-github"],
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "your_token"
  }
}
```

#### PostgreSQL 数据库
```json
"postgres": {
  "command": "uvx",
  "args": ["mcp-server-postgres", "postgresql://user:password@localhost/dbname"],
  "env": {}
}
```

## 使用方式

### 1. 自动加载

MCP 工具会在应用启动时自动加载。您可以在日志中看到加载状态：

```
INFO:src.agent.mcp_utils:正在加载 MCP 服务器: filesystem
INFO:src.agent.mcp_utils:已加载工具: read_file (来自 filesystem)
INFO:src.agent.mcp_utils:已加载工具: write_file (来自 filesystem)
INFO:src.agent.mcp_utils:总共加载了 5 个 MCP 工具
```

### 2. 在对话中使用

一旦 MCP 工具加载完成，AI 代理就可以在对话中自动使用这些工具：

```
用户: 请帮我在 /tmp 目录下创建一个新文件，内容是今天的日期和时间
AI: 我来帮您创建这个文件...
[使用 write_file 工具创建文件]
```

### 3. 查看可用工具

您可以询问 AI 代理有哪些可用的工具：

```
用户: 你现在有哪些工具可以使用？
AI: 我目前可以使用以下工具：
1. get_current_time - 获取当前时间
2. read_file - 读取文件内容 (来自 filesystem)
3. write_file - 写入文件 (来自 filesystem)
4. search_web - 网络搜索 (来自 brave-search)
...
```

## 故障排除

### 1. 工具加载失败

如果看到以下错误：
```
ERROR:src.agent.mcp_utils:从 MCP 服务器获取工具失败 (npx): ...
```

检查：
- 确保相关的包已安装（如 `npx`、`uvx`）
- 验证环境变量是否正确设置
- 检查网络连接和权限

### 2. 环境变量配置

建议将敏感信息（如 API 密钥）设置为环境变量：

```bash
export BRAVE_API_KEY="your_api_key"
export GITHUB_PERSONAL_ACCESS_TOKEN="your_token"
```

然后在配置文件中引用：
```json
"env": {
  "BRAVE_API_KEY": "${BRAVE_API_KEY}"
}
```

### 3. 权限问题

某些 MCP 服务器可能需要特定权限：
- 文件系统访问需要读写权限
- 数据库连接需要相应的数据库权限
- API 调用需要有效的认证信息

## 扩展更多工具

要添加新的 MCP 工具：

1. 在 `mcp_config.json` 中添加新的服务器配置
2. 重启应用，工具会自动加载
3. 测试新工具是否正常工作

查看 [MCP 服务器目录](https://github.com/modelcontextprotocol/servers) 了解更多可用的服务器。

## 安全注意事项

- 仅连接到可信的 MCP 服务器
- 谨慎配置文件系统访问路径
- 定期更新 MCP 服务器以获得安全补丁
- 使用环境变量管理敏感信息 