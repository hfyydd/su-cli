import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
import importlib.util
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentScanner:
    """Agent 扫描器，用于动态发现和加载 Langgraph agents"""
    
    def __init__(self, agents_dir: str = "agents"):
        """
        初始化 Agent 扫描器
        
        Args:
            agents_dir: agents 文件夹路径，默认为 "agents"
        """
        self.project_root = Path(__file__).parent.parent
        self.agents_dir = self.project_root / agents_dir
        self.discovered_agents = {}
        
    def scan_agents(self) -> Dict[str, Dict[str, Any]]:
        """
        扫描 agents 文件夹，发现所有可用的 agent
        
        Returns:
            Dict: 发现的 agents 信息字典
                格式: {
                    "agent_name": {
                        "path": "agents/agent_name",
                        "config": {...},
                        "module": module_object,
                        "valid": True/False
                    }
                }
        """
        logger.info(f"开始扫描 agents 文件夹: {self.agents_dir}")
        
        if not self.agents_dir.exists():
            logger.warning(f"Agents 文件夹不存在: {self.agents_dir}")
            return {}
            
        discovered = {}
        
        # 遍历 agents 文件夹中的所有子文件夹
        for item in self.agents_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                agent_info = self._scan_single_agent(item)
                if agent_info:
                    discovered[item.name] = agent_info
                    
        self.discovered_agents = discovered
        logger.info(f"扫描完成，发现 {len(discovered)} 个 agents")
        return discovered
    
    def _scan_single_agent(self, agent_path: Path) -> Optional[Dict[str, Any]]:
        """
        扫描单个 agent 文件夹
        
        Args:
            agent_path: agent 文件夹路径
            
        Returns:
            Dict: agent 信息，如果无效则返回 None
        """
        agent_name = agent_path.name
        logger.info(f"扫描 agent: {agent_name}")
        
        agent_info = {
            "name": agent_name,
            "path": str(agent_path.relative_to(self.project_root)),
            "config": {},
            "module": None,
            "valid": False,
            "entry_point": None,
            "dependencies": []
        }
        
        try:
            # 检查是否是有效的 Langgraph agent 结构
            if self._validate_langgraph_structure(agent_path):
                agent_info["valid"] = True
                agent_info["config"] = self._load_agent_config(agent_path)
                agent_info["entry_point"] = self._find_entry_point(agent_path)
                agent_info["dependencies"] = self._scan_dependencies(agent_path)
                
                logger.info(f"✓ Agent {agent_name} 验证通过")
            else:
                logger.warning(f"✗ Agent {agent_name} 不符合 Langgraph 结构要求")
                
        except Exception as e:
            logger.error(f"扫描 agent {agent_name} 时出错: {e}")
            
        return agent_info
    
    def _validate_langgraph_structure(self, agent_path: Path) -> bool:
        """
        验证是否符合标准的 Langgraph agent 结构
        
        Args:
            agent_path: agent 文件夹路径
            
        Returns:
            bool: 是否有效
        """
        # 检查是否有 langgraph.json 配置文件（标准 Langgraph 项目）
        langgraph_config = agent_path / "langgraph.json"
        if langgraph_config.exists():
            logger.debug("发现 langgraph.json 配置文件")
            return True
        
        # 检查简单的 agent 结构（直接包含 agent 文件）
        required_files = [
            "__init__.py",  # Python 包标识
        ]
        
        # 检查必需文件
        for file_name in required_files:
            if not (agent_path / file_name).exists():
                logger.debug(f"缺少必需文件: {file_name}")
                return False
        
        # 检查是否有常见的 Langgraph agent 文件
        common_files = [
            "agent.py",
            "graph.py", 
            "main.py",
            "workflow.py"
        ]
        
        has_agent_file = any((agent_path / file_name).exists() for file_name in common_files)
        
        if not has_agent_file:
            logger.debug("未找到常见的 agent 入口文件")
            return False
            
        return True
    
    def _load_agent_config(self, agent_path: Path) -> Dict[str, Any]:
        """
        加载 agent 配置文件
        
        Args:
            agent_path: agent 文件夹路径
            
        Returns:
            Dict: 配置信息
        """
        config = {}
        
        # 优先加载 langgraph.json 配置文件
        langgraph_config = agent_path / "langgraph.json"
        if langgraph_config.exists():
            try:
                import json
                with open(langgraph_config, 'r', encoding='utf-8') as f:
                    langgraph_data = json.load(f)
                    config["langgraph"] = langgraph_data
                    logger.debug(f"加载 langgraph.json 配置: {langgraph_data}")
            except Exception as e:
                logger.warning(f"加载 langgraph.json 失败: {e}")
        
        # 尝试加载其他配置文件
        config_files = ["config.json", "config.yaml", "config.yml", "agent_config.json"]
        
        for config_file in config_files:
            config_path = agent_path / config_file
            if config_path.exists():
                try:
                    if config_file.endswith('.json'):
                        import json
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config.update(json.load(f))
                    elif config_file.endswith(('.yaml', '.yml')):
                        try:
                            import yaml
                            with open(config_path, 'r', encoding='utf-8') as f:
                                config.update(yaml.safe_load(f))
                        except ImportError:
                            logger.warning("未安装 PyYAML，跳过 YAML 配置文件")
                except Exception as e:
                    logger.warning(f"加载配置文件 {config_file} 失败: {e}")
                    
        return config
    
    def _find_entry_point(self, agent_path: Path) -> Optional[str]:
        """
        查找 agent 的入口点
        
        Args:
            agent_path: agent 文件夹路径
            
        Returns:
            str: 入口点文件路径或文件名
        """
        # 首先检查是否有 langgraph.json 配置
        langgraph_config = agent_path / "langgraph.json"
        if langgraph_config.exists():
            try:
                import json
                with open(langgraph_config, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    graphs = config.get("graphs", {})
                    if graphs:
                        # 取第一个 graph 的路径
                        first_graph = list(graphs.values())[0]
                        # 格式通常是 "./src/agent/graph.py:graph"，我们只需要文件路径部分
                        if ":" in first_graph:
                            file_path = first_graph.split(":")[0]
                        else:
                            file_path = first_graph
                        
                        # 移除开头的 "./" 
                        if file_path.startswith("./"):
                            file_path = file_path[2:]
                            
                        # 检查文件是否存在
                        full_path = agent_path / file_path
                        if full_path.exists():
                            logger.debug(f"从 langgraph.json 找到入口点: {file_path}")
                            return file_path
                            
            except Exception as e:
                logger.warning(f"解析 langgraph.json 中的 graphs 配置失败: {e}")
        
        # 如果没有 langgraph.json 或解析失败，使用传统方式查找
        entry_points = ["agent.py", "main.py", "graph.py", "workflow.py"]
        
        for entry_point in entry_points:
            if (agent_path / entry_point).exists():
                return entry_point
                
        return None
    
    def _scan_dependencies(self, agent_path: Path) -> List[str]:
        """
        扫描 agent 的依赖
        
        Args:
            agent_path: agent 文件夹路径
            
        Returns:
            List[str]: 依赖列表
        """
        dependencies = []
        
        # 检查 requirements.txt
        req_file = agent_path / "requirements.txt"
        if req_file.exists():
            try:
                with open(req_file, 'r', encoding='utf-8') as f:
                    dependencies.extend([line.strip() for line in f if line.strip() and not line.startswith('#')])
            except Exception as e:
                logger.warning(f"读取依赖文件失败: {e}")
                
        return dependencies
    
    def get_agent_list(self) -> List[str]:
        """
        获取所有发现的 agent 名称列表
        
        Returns:
            List[str]: agent 名称列表
        """
        return list(self.discovered_agents.keys())
    
    def get_valid_agents(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有有效的 agents
        
        Returns:
            Dict: 有效的 agents 信息
        """
        return {name: info for name, info in self.discovered_agents.items() if info.get("valid", False)}
    
    def get_agent_info(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        获取指定 agent 的信息
        
        Args:
            agent_name: agent 名称
            
        Returns:
            Dict: agent 信息，如果不存在则返回 None
        """
        return self.discovered_agents.get(agent_name)
    
    def load_agent_module(self, agent_name: str) -> Optional[Any]:
        """
        动态加载指定的 agent 模块
        
        Args:
            agent_name: agent 名称
            
        Returns:
            模块对象，如果加载失败则返回 None
        """
        agent_info = self.get_agent_info(agent_name)
        if not agent_info or not agent_info.get("valid", False):
            logger.error(f"Agent {agent_name} 无效或不存在")
            return None
            
        try:
            agent_path = self.project_root / agent_info["path"]
            entry_point = agent_info.get("entry_point")
            
            if not entry_point:
                logger.error(f"Agent {agent_name} 没有找到入口点")
                return None
            
            # 动态加载模块
            module_path = agent_path / entry_point
            
            # 将 agent 目录及其src目录添加到 sys.path，确保能正确导入相对模块
            agent_path_str = str(agent_path)
            src_path_str = str(agent_path / "src") if (agent_path / "src").exists() else None
            
            paths_added = []
            
            if agent_path_str not in sys.path:
                sys.path.insert(0, agent_path_str)
                paths_added.append(agent_path_str)
                logger.debug(f"添加路径到 sys.path: {agent_path_str}")
            
            if src_path_str and src_path_str not in sys.path:
                sys.path.insert(0, src_path_str)
                paths_added.append(src_path_str)
                logger.debug(f"添加src路径到 sys.path: {src_path_str}")
            
            # 生成模块名称，处理路径中的斜杠
            module_name = f"agent_{agent_name}_{entry_point.replace('/', '_').replace('.py', '')}"
            
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            
            if spec is None or spec.loader is None:
                logger.error(f"无法创建模块规范: {module_path}")
                # 清理添加的路径
                for path in paths_added:
                    if path in sys.path:
                        sys.path.remove(path)
                return None
                
            module = importlib.util.module_from_spec(spec)
            
            # 将模块添加到 sys.modules
            if module_name not in sys.modules:
                sys.modules[module_name] = module
            
            # 执行模块 - 在这里设置适当的环境变量和上下文
            old_cwd = os.getcwd()
            try:
                # 切换到agent目录，确保相对路径正确
                os.chdir(agent_path)
                spec.loader.exec_module(module)
            finally:
                # 恢复原始工作目录
                os.chdir(old_cwd)
            
            # 缓存模块
            agent_info["module"] = module
            
            logger.info(f"✓ 成功加载 agent: {agent_name}")
            return module
            
        except Exception as e:
            logger.error(f"加载 agent {agent_name} 失败: {e}")
            import traceback
            logger.debug(f"详细错误信息: {traceback.format_exc()}")
            # 清理添加的路径（如果失败了）
            if 'paths_added' in locals():
                for path in paths_added:
                    if path in sys.path:
                        sys.path.remove(path)
            return None


# 创建全局扫描器实例
scanner = AgentScanner()


def scan_agents() -> Dict[str, Dict[str, Any]]:
    """便捷函数：扫描所有 agents"""
    return scanner.scan_agents()


def get_available_agents() -> List[str]:
    """便捷函数：获取可用的 agent 列表"""
    return scanner.get_agent_list()


def get_valid_agents() -> Dict[str, Dict[str, Any]]:
    """便捷函数：获取有效的 agents"""
    return scanner.get_valid_agents()


def load_agent(agent_name: str) -> Optional[Any]:
    """便捷函数：加载指定的 agent"""
    return scanner.load_agent_module(agent_name)


def get_agent_info(agent_name: str) -> Optional[Dict[str, Any]]:
    """便捷函数：获取 agent 信息"""
    return scanner.get_agent_info(agent_name)


if __name__ == "__main__":
    # 测试扫描功能
    print("开始扫描 agents...")
    agents = scan_agents()
    
    print(f"\n发现 {len(agents)} 个 agents:")
    for name, info in agents.items():
        status = "✓ 有效" if info.get("valid", False) else "✗ 无效"
        print(f"  - {name}: {status}")
        if info.get("entry_point"):
            print(f"    入口点: {info['entry_point']}")
        if info.get("dependencies"):
            print(f"    依赖: {', '.join(info['dependencies'])}")
