from pathlib import Path

import yaml


def load_prompt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


path=Path(__file__).parents[1]/ "prompt" / "prompts.yaml"

result=load_prompt(path)
main_agent_info=result["main_agent"]
sub_agents_info=result["sub_agents"]

# print(main_agent_info)
# print(100* '*')
# print(sub_agents_info)
