from psqlagent.modules.db import PostgresManager
from psqlagent.modules.orchestrator import Orchestrator
from autogen import (
    AssistantAgent,
    UserProxyAgent,
    GroupChat,
    GroupChatManager,
    config_list_from_json,
    config_list_from_models
)
from psqlagent.agents.prompts import (
    USER_PROXY_PROMPT,
    SECRETARY_PROMPT,
    TRANSLATOR_PROMPT,
    DATA_ENGINEER_PROMPT,
    DATA_ANALYST_PROMPT,
    PRODUCT_MANAGER_PROMPT
)
from psqlagent.agents.agent_config import base_config, run_sql_config, build_function_map_run_query

# Terminate msg function
def is_termination_msg(content):
    have_content = content.get("content", None) is not None
    if have_content and "APPROVED" in content["content"]:
        return True
    return False


# Agent definitions
user_proxy = UserProxyAgent(
    name="Admin",
    system_message=USER_PROXY_PROMPT,
    code_execution_config=False,
    human_input_mode="NEVER",
    is_termination_msg=is_termination_msg
)

secretary = AssistantAgent(
    name="Secretary",
    llm_config=base_config,
    system_message=SECRETARY_PROMPT,
    code_execution_config=False,
    human_input_mode="NEVER",
    is_termination_msg=is_termination_msg
)

translator = AssistantAgent(
    name="Translator",
    llm_config=base_config,
    system_message=TRANSLATOR_PROMPT,
    code_execution_config=False,
    human_input_mode="NEVER",
    is_termination_msg=is_termination_msg
)

def build_engineer_agent(db: PostgresManager) -> AssistantAgent:
    return AssistantAgent(
        name="Engineer",
        llm_config=run_sql_config,
        system_message=DATA_ENGINEER_PROMPT,
        code_execution_config=False,
        human_input_mode="NEVER",
        is_termination_msg=is_termination_msg,
        function_map=build_function_map_run_query(db)
    )

data_analyst = AssistantAgent(
    name="SrDataAnalyst",
    llm_config=base_config,
    system_message=DATA_ANALYST_PROMPT,
    code_execution_config=False,
    human_input_mode="NEVER",
    is_termination_msg=is_termination_msg,
    # function_map=function_map
)

planner = AssistantAgent(
    name="ProductManager",
    system_message=PRODUCT_MANAGER_PROMPT,
    code_execution_config=False,
    llm_config=base_config,
    human_input_mode="NEVER",
    is_termination_msg=is_termination_msg
)


def build_team_orchestrator(team: str, db: PostgresManager) -> Orchestrator:
    team_orchestrator = Orchestrator(
        name=f"{team} Orchestrator",
        agents=[user_proxy, build_engineer_agent(db), data_analyst, planner]
    )
    return team_orchestrator
