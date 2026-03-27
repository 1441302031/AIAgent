from aiagent.agents.router import TaskRouter
from aiagent.domain.models import AgentRequest


def test_task_router_routes_planning_requests_to_planner():
    router = TaskRouter()

    route = router.select(AgentRequest(user_input="请帮我拆解这个需求并给出步骤"))

    assert route == "planner"


def test_task_router_routes_general_requests_to_direct():
    router = TaskRouter()

    route = router.select(AgentRequest(user_input="你好，请简单介绍一下自己"))

    assert route == "direct"


def test_task_router_allows_metadata_override():
    router = TaskRouter()

    route = router.select(
        AgentRequest(
            user_input="你好",
            metadata={"route": "planner"},
        )
    )

    assert route == "planner"
