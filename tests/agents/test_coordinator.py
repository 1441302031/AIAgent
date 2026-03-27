from aiagent.agents.assistant import AssistantAgent
from aiagent.agents.subagent import PlannerSubAgent
from aiagent.domain.models import AgentRequest, AgentResponse, CompletionEvent, CompletionRequest, CompletionResponse, Message
from aiagent.agents.coordinator import CoordinatorAgent
from aiagent.session.history import SessionHistory


class FakeAgent:
    def __init__(self, final_text: str) -> None:
        self.final_text = final_text
        self.requests: list[AgentRequest] = []

    def run(self, request: AgentRequest) -> AgentResponse:
        self.requests.append(request)
        return AgentResponse(
            final_text=self.final_text,
            messages=[
                Message(role="user", content=request.user_input),
                Message(role="assistant", content=self.final_text),
            ],
        )

    def run_stream(self, request: AgentRequest):
        self.requests.append(request)
        yield CompletionEvent(kind="content", text=self.final_text)
        yield CompletionEvent(kind="done")


class FakeRouter:
    def __init__(self, route: str) -> None:
        self.route = route
        self.requests: list[AgentRequest] = []

    def select(self, request: AgentRequest) -> str:
        self.requests.append(request)
        return self.route


class SequenceRouter:
    def __init__(self, routes: list[str]) -> None:
        self._routes = iter(routes)

    def select(self, request: AgentRequest) -> str:
        return next(self._routes)


class CapturingProvider:
    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.requests: list[CompletionRequest] = []

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        self.requests.append(request)
        return CompletionResponse(
            model=request.model,
            message=Message(role="assistant", content=self.response_text),
        )


def test_coordinator_agent_uses_primary_agent_for_direct_route():
    primary = FakeAgent(final_text="primary reply")
    planner = FakeAgent(final_text="planner reply")
    router = FakeRouter(route="direct")
    agent = CoordinatorAgent(primary_agent=primary, planner_agent=planner, router=router)

    response = agent.run(AgentRequest(user_input="hello"))

    assert response.final_text == "primary reply"
    assert response.handoffs == []
    assert len(primary.requests) == 1
    assert planner.requests == []


def test_coordinator_agent_delegates_to_planner_and_records_handoff():
    primary = FakeAgent(final_text="primary reply")
    planner = FakeAgent(final_text="planner reply")
    router = FakeRouter(route="planner")
    agent = CoordinatorAgent(primary_agent=primary, planner_agent=planner, router=router)

    response = agent.run(AgentRequest(user_input="请帮我拆解这个需求"))

    assert response.final_text == "planner reply"
    assert len(response.handoffs) == 1
    assert response.handoffs[0]["agent"] == "planner"
    assert response.handoffs[0]["reason"] == "task_router"
    assert primary.requests == []
    assert len(planner.requests) == 1


def test_coordinator_agent_streams_final_response_as_content_and_done_events():
    primary = FakeAgent(final_text="primary reply")
    planner = FakeAgent(final_text="planner reply")
    router = FakeRouter(route="planner")
    agent = CoordinatorAgent(primary_agent=primary, planner_agent=planner, router=router)

    events = list(agent.run_stream(AgentRequest(user_input="请帮我拆解这个需求")))

    assert [(event.kind, event.text) for event in events] == [
        ("content", "planner reply"),
        ("done", ""),
    ]


def test_coordinator_agent_can_show_subagent_stream_for_planner_route():
    primary = FakeAgent(final_text="primary reply")
    planner = FakeAgent(final_text="planner reply")
    router = FakeRouter(route="planner")
    agent = CoordinatorAgent(
        primary_agent=primary,
        planner_agent=planner,
        router=router,
        show_subagents=True,
    )

    events = list(agent.run_stream(AgentRequest(user_input="please break this down into steps")))

    assert [(event.kind, event.text) for event in events] == [
        ("content", "[planner]\n"),
        ("content", "planner reply"),
        ("done", ""),
    ]


def test_coordinator_agent_can_show_primary_stream_for_direct_route():
    primary = FakeAgent(final_text="primary reply")
    planner = FakeAgent(final_text="planner reply")
    router = FakeRouter(route="direct")
    agent = CoordinatorAgent(
        primary_agent=primary,
        planner_agent=planner,
        router=router,
        show_subagents=True,
    )

    events = list(agent.run_stream(AgentRequest(user_input="hello")))

    assert [(event.kind, event.text) for event in events] == [
        ("content", "[primary]\n"),
        ("content", "primary reply"),
        ("done", ""),
    ]


def test_coordinator_agent_preserves_shared_history_across_planner_then_direct_turns():
    shared_history = SessionHistory()
    primary_provider = CapturingProvider(response_text="primary reply")
    planner_provider = CapturingProvider(response_text="planner reply")
    agent = CoordinatorAgent(
        primary_agent=AssistantAgent(
            provider=primary_provider,
            history=shared_history,
            model="mock-model",
        ),
        planner_agent=PlannerSubAgent(
            provider=planner_provider,
            history=shared_history,
            model="mock-model",
        ),
        router=SequenceRouter(["planner", "direct"]),
    )

    first_response = agent.run(AgentRequest(user_input="请拆解这个需求"))
    second_response = agent.run(AgentRequest(user_input="继续总结刚才的结果"))

    assert first_response.final_text == "planner reply"
    assert second_response.final_text == "primary reply"
    assert planner_provider.requests
    assert primary_provider.requests
    assert [(message.role, message.content) for message in primary_provider.requests[0].messages] == [
        ("system", "You are a helpful AI assistant."),
        ("user", "请拆解这个需求"),
        ("assistant", "planner reply"),
        ("user", "继续总结刚才的结果"),
    ]
