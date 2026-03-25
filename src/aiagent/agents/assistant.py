from aiagent.agents.base import Agent
from aiagent.domain.models import AgentRequest, AgentResponse, CompletionRequest, Message
from aiagent.prompts.system import DEFAULT_SYSTEM_PROMPT
from aiagent.prompts.templates import build_messages
from aiagent.providers.base import CompletionProvider
from aiagent.session.history import SessionHistory


class AssistantAgent(Agent):
    def __init__(
        self,
        provider: CompletionProvider,
        history: SessionHistory,
        model: str,
        temperature: float = 0.0,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    ) -> None:
        self._provider = provider
        self._history = history
        self._model = model
        self._temperature = temperature
        self._system_prompt = system_prompt

    def run(self, request: AgentRequest) -> AgentResponse:
        user_message = Message(role="user", content=request.user_input)
        messages = build_messages(
            system_prompt=self._system_prompt,
            history=self._history.all(),
            user_input=request.user_input,
        )
        completion = self._provider.complete(
            CompletionRequest(
                model=self._model,
                messages=messages,
                temperature=self._temperature,
            )
        )
        assistant_message = completion.message
        self._history.add(user_message)
        self._history.add(assistant_message)
        return AgentResponse(
            final_text=assistant_message.content,
            messages=[user_message, assistant_message],
        )
