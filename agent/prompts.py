from pathlib import Path

import yaml

# 加载指定位置的yaml文件

def load_prompt(file_path):
    """
    加载指定位置的yaml文件
    :param file_path:
    :return:
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


path=Path(__file__).parents[1]/ "prompt" / "prompts.yaml"

result=load_prompt(path)
main_agent_info=result["main_agent"]
sub_agents_info=result["sub_agents"]

