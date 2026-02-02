import sys
from langgraph.graph import StateGraph, END
from models import AgentState
from agents import document_intelligence_node, matching_node, discrepancy_node, resolution_node

# build the workflow graph
workflow = StateGraph(AgentState)

# add agents as nodes
workflow.add_node("extractor", document_intelligence_node)
workflow.add_node("matcher", matching_node)
workflow.add_node("checker", discrepancy_node)
workflow.add_node("resolver", resolution_node)

# define the flow (linear for now)
workflow.set_entry_point("extractor")
workflow.add_edge("extractor", "matcher")
workflow.add_edge("matcher", "checker")
workflow.add_edge("checker", "resolver")
workflow.add_edge("resolver", END)

# compile the app
app = workflow.compile()

def process_invoice(file_path):
    print(f"starting pipeline for: {file_path}")
    
    initial_state = AgentState(file_path=file_path)
    
    # run the graph
    result = app.invoke(initial_state)
    
    # print simple summary
    print(f"\n--- final output ---")
    print(f"status: {result['recommendation']}")
    print(f"reason: {result['reasoning']}")
    
    if result['discrepancies']:
        print("discrepancies:")
        for d in result['discrepancies']:
            print(f" - {d.details}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        process_invoice(sys.argv[1])
    else:
        print("usage: python main.py <invoice_file.pdf>")