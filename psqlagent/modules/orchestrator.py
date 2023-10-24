from typing import List, Optional, Tuple
import autogen
from . import llm

class Orchestrator:
    def __init__(self, name: str, agents: List[autogen.ConversableAgent]):
        self.name = name
        self.agents = agents
        self.messages = []
        self.complete_keyword = "APPROVED"
        self.error_keyword = "ERROR"

        if len(self.agents) < 2:
            raise ValueError("Orchestrator must have at least 2 agents")

    @property
    def total_agents(self):
        return len(self.agents)

    @property
    def last_message_is_dict(self):
        return isinstance(self.messages[-1], dict)

    @property
    def last_message_is_str(self):
        return isinstance(self.messages[-1], str)

    @property
    def last_message_is_func_call(self):
        return self.last_message_is_dict and self.latest_message.get("function_call", None)

    @property
    def last_message_is_content(self):
        return self.last_message_is_dict and self.latest_message.get("content", None)

    @property
    def latest_message(self):
        if not self.messages:
            return None
        return self.messages[-1]

    def has_function(self, agent: autogen.ConversableAgent):
        return agent._function_map is not None

    def add_messages(self, message: str):
        self.messages.append(message)

    def get_message_as_str(self):
        messages_as_str = ""
        for message in self.messages:
            if message is None:
                continue
            if isinstance(message, dict):
                content_from_dict = message.get("content", None)
                function_call_from_dict = message.get("function_call", None)
                content = content_from_dict or function_call_from_dict
                if not content:
                    continue
                messages_as_str += str(content)
            else:
                messages_as_str += str(message)
        return messages_as_str
    
    def get_cost_and_tokens(self):
        return llm.estimate_price_and_tokens(self.get_message_as_str())

    def basic_chat(self,
                   agent_a: autogen.ConversableAgent,
                   agent_b: autogen.ConversableAgent,
                   message: str):

        print(
            f"BasicChat between A: {agent_a.name} and B: {agent_b.name}")

        agent_a.send(message, agent_b)
        reply = agent_b.generate_reply(sender=agent_a)
        self.add_messages(reply)
        print(f"BasicChat response from {agent_b.name} replied with: {reply}")

    def function_chat(self,
                      agent_a: autogen.ConversableAgent,
                      agent_b: autogen.ConversableAgent,
                      message: str):

        print(
            f"FunctionChat between A: {agent_a.name} and B: {agent_b.name}")

        self.basic_chat(agent_a, agent_a, message)
        assert self.last_message_is_content
        self.basic_chat(agent_a, agent_b, self.latest_message)

    def sequential_conversation(self, prompt: str) -> Tuple[bool, List[str]]:
        """
        Runs a sequential conversation between all agents
        For example
        >>> "Agent A" -> "Agent B" -> "Agent C"
        """
        print(
            f"------------ {self.name} is starting a sequential conversation ---------")
        print(
            f"\n\nStarting sequential conversation with {self.total_agents} agents\n\n")

        self.add_messages(prompt)
        # return True, self.messages

        for idx, agent in enumerate(self.agents):
            agent_a = self.agents[idx]
            agent_b = self.agents[idx + 1]

            print(
                f"\n ****** Running iteration {idx} between A: {agent_a.name} and B: {agent_b.name} ****************")

            # agent_a -> chat -> agent_b
            if self.last_message_is_str:
                self.basic_chat(agent_a, agent_b, self.latest_message)

            # agent_a -> function -> agent_b
            elif self.last_message_is_func_call and self.has_function(agent_a):
                self.function_chat(agent_a, agent_b, self.latest_message)

            if idx == self.total_agents - 2:
                print(f"---- Conversation ended with: {agent_b.name} -----")
                print(f"Final message: {self.latest_message}")

                was_successful = False
                if self.latest_message is not None:
                    was_successful = self.complete_keyword in self.latest_message
                print("Successfull" if was_successful else "Unsuccessfull X")

                return was_successful, self.messages[1:]

    def broadcast_conversation(self, prompt: str) -> Tuple[bool, List[str]]:
        """
        Runs a broadcast conversation between all agents
        For example
        >>> "Agent A" -> "Agent B"
        >>> "Agent A" -> "Agent C"
        >>> "Agent A" -> "Agent D"
        """
        print(
            f"\nStarting broadcast conversation with {self.total_agents} agents\n\n")

        self.add_messages(prompt)
        broadcast_agent = self.agents[0]

        for idx, agent in enumerate(self.agents[1:]):  # skip the first agent

            print(
                f"\n ******  Running iteration {idx} between A: {agent_a.name} and B: {agent_b.name} ****************")

            # agent_a -> chat -> agent_b
            if self.last_message_is_str:
                self.basic_chat(agent_a, agent_b, self.latest_message)

            # agent_a -> function -> agent_b
            if self.last_message_is_func_call and self.has_function(agent_a):
                self.function_chat(agent_a, agent_b, self.latest_message)

        was_successful = False
        if self.latest_message is not None:
            was_successful = self.complete_keyword in self.latest_message
        print("Successfull" if was_successful else "Unsuccessfull X")

        return was_successful, self.messages
