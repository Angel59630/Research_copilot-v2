from typing import (
    Annotated,
    TypedDict,
)

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    SystemMessage,
)
from langgraph.graph import (
    END,
    START,
    StateGraph,
)
from langgraph.graph.message import (
    add_messages,
)
from langgraph.prebuilt import (
    ToolNode,
)

from backend.rag.prompts import (
    SYSTEM_PROMPT,
)
from backend.rag.retrieval import (
    retrieve_papers,
)
from backend.rag.types import (
    RagRuntimeContext,
)
from config import settings


class AgentState(TypedDict):
    messages: Annotated[
        list[BaseMessage],
        add_messages,
    ]

    tool_call_count: int


def build_rag_graph(
    model,
):
    tools = [
        retrieve_papers
    ]

    tool_model = (
        model.bind_tools(
            tools
        )
    )

    async def agent_decide(
        state: AgentState,
    ):
        messages = [
            SystemMessage(
                content=SYSTEM_PROMPT
            ),
            *state["messages"],
        ]

        response = (
            await tool_model.ainvoke(
                messages
            )
        )

        return {
            "messages": [
                response
            ]
        }

    def route_agent(
        state: AgentState,
    ) -> str:
        message = (
            state["messages"][-1]
        )

        if (
            isinstance(
                message,
                AIMessage,
            )
            and message.tool_calls
        ):
            call_count = (
                state.get(
                    "tool_call_count",
                    0,
                )
            )

            if (
                call_count
                >= settings.max_tool_calls
            ):
                return "insufficient"

            return "tools"

        return "direct"

    async def count_tool_call(
        state: AgentState,
    ):
        current = state.get(
            "tool_call_count",
            0,
        )

        return {
            "tool_call_count":
                current + 1
        }

    async def direct_answer(
        state: AgentState,
    ):
        return {}

    async def insufficient(
        state: AgentState,
    ):
        return {
            "messages": [
                AIMessage(
                    content=(
                        "当前论文检索结果不足以"
                        "支持可靠回答。"
                    )
                )
            ]
        }

    graph = StateGraph(
        AgentState,
        context_schema=(
            RagRuntimeContext
        ),
    )

    graph.add_node(
        "agent_decide",
        agent_decide,
    )

    graph.add_node(
        "tools",
        ToolNode(tools),
    )

    graph.add_node(
        "count_tool_call",
        count_tool_call,
    )

    graph.add_node(
        "direct",
        direct_answer,
    )

    graph.add_node(
        "insufficient",
        insufficient,
    )

    graph.add_edge(
        START,
        "agent_decide",
    )

    graph.add_conditional_edges(
        "agent_decide",
        route_agent,
        {
            "tools":
                "tools",
            "direct":
                "direct",
            "insufficient":
                "insufficient",
        },
    )

    graph.add_edge(
        "tools",
        "count_tool_call",
    )

    graph.add_edge(
        "count_tool_call",
        "agent_decide",
    )

    graph.add_edge(
        "direct",
        END,
    )

    graph.add_edge(
        "insufficient",
        END,
    )

    return graph.compile()