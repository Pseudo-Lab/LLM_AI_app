from langchain_core.runnables import RunnableLambda
from langgraph.graph import StateGraph



from src.graphs.memory import MemoryStorage
from src.graphs.state import GraphState
from src.graphs.node import (
    supervisor_node,
    default_answer_node,
    memory_input_node,
    memory_save_node,
    call_weather_mcp,
    check_duplicated_arxiv_id,
    save_paper,
    summary_paper,
)




def route_logic(state):
    route = state["route"].lower()
    return route if route in ['weather', 'paper', 'default'] else "default"



def build_graph():
    chat_memory = MemoryStorage()


    graph = StateGraph(GraphState)


    graph.add_node("start_node", RunnableLambda(lambda state: memory_input_node(state, chat_memory)))
    graph.add_node("supervisor", RunnableLambda(supervisor_node))

    graph.add_node("default", RunnableLambda(default_answer_node))

    graph.add_node("weather", RunnableLambda(call_weather_mcp))

    graph.add_node("paper-check_duplicated_arxiv_id", RunnableLambda(check_duplicated_arxiv_id))
    graph.add_node("paper-save_paper", RunnableLambda(save_paper))
    graph.add_node("paper-summary", RunnableLambda(summary_paper))

    graph.add_node("end_node", RunnableLambda(lambda state: memory_save_node(state, chat_memory)))

    graph.set_entry_point("start_node")
    graph.add_edge("start_node", "supervisor")
    graph.add_conditional_edges(
                                "supervisor", 
                                route_logic,
                                {
                                    "weather": "weather",
                                    "paper": "paper-check_duplicated_arxiv_id",
                                    "default": "default"
                                })
    
    graph.add_conditional_edges(
                                "paper-check_duplicated_arxiv_id",
                                lambda state: state["paper_duplicated_check"],
                                {
                                    "true": "end_node",
                                    "false": "paper-save_paper",
                                    "error": "end_node"
                                })
    
    graph.add_edge("paper-save_paper", "paper-summary")
    graph.add_edge("paper-summary", "end_node")

    graph.add_edge("weather", "end_node")
    graph.add_edge("default", "end_node")

    graph.set_finish_point("end_node")

    runnable_chain = graph.compile()
    return runnable_chain
    


if __name__ == "__main__":
    import asyncio
    
    print("<<<<<<<<<<<<<<<<<<< test conversation >>>>>>>>>>>>>>>>>>>")
    runnable_chain = build_graph()
    while True:
        user_input = input(f"\nUser: ")
        if user_input.lower() == "exit":
            print("Program exit")
            break

        try:
            result = runnable_chain.invoke({"user_input": user_input})
        except:
            async def main():
                result = await runnable_chain.ainvoke({"user_input": user_input})
                return result
            result = asyncio.run(main())

        print(f"LangGraph-bot: {result}")
        