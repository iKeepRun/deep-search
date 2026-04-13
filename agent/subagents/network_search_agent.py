from deepagents import create_deep_agent

from agent.prompts import sub_agents_info
from tools.tavily_tool import internal_search

# 网络搜索子智能体
# 创建子智能体的两种方式： 1.字典 2.compiledSubAgent(langchain.langgraph)

network_search_agent ={
    "name":  sub_agents_info["tavily"]["name"]  ,
    "description": sub_agents_info["tavily"]["description"],
    "system_prompt": sub_agents_info["tavily"]["system_prompt"],
    "tools": [internal_search],
}





