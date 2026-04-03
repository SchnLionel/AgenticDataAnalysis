import os
import json
import pandas as pd
from typing import List, Dict, Any, Annotated, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import plotly.io as pio

from backend.db import models
from backend.security.code_sandbox import execute_code_safely
from backend.core.config import settings

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], "The messages in the conversation"]
    current_variables: Dict[str, Any]
    session_id: int
    user_id: int
    dataset_path: str
    intermediate_outputs: List[Dict[str, Any]]
    output_figures: List[Dict[str, Any]]

# --- Tools Definition ---

@tool
def execute_data_cleaning(thought: str, python_code: str, state: Annotated[dict, "Current agent state"]):
    """
    Cleans and transforms the user's dataset.
    Use this for handling missing values, duplicates, and type boat conversions.
    """
    result = execute_code_safely(python_code, state["current_variables"])
    return {
        "output": result["output"],
        "thought": thought,
        "code": python_code,
        "new_variables": result["persistent_vars"]
    }

@tool
def execute_visualization(thought: str, python_code: str, state: Annotated[dict, "Current agent state"]):
    """
    Generates Plotly figures for data visualization.
    The code should append figures to a list named `plotly_figures`.
    Example: `plotly_figures.append(px.histogram(df, x='age'))`
    """
    result = execute_code_safely(python_code, state["current_variables"])
    figures_json = [pio.to_json(fig) for fig in result["plotly_figures"]]
    return {
        "output": result["output"],
        "thought": thought,
        "code": python_code,
        "figures": figures_json,
        "new_variables": result["persistent_vars"]
    }

@tool
def execute_statistical_analysis(thought: str, python_code: str, state: Annotated[dict, "Current agent state"]):
    """
    Performs statistical analyses (correlations, t-tests, etc.) using pandas/scipy/numpy.
    """
    result = execute_code_safely(python_code, state["current_variables"])
    return {
        "output": result["output"],
        "thought": thought,
        "code": python_code,
        "new_variables": result["persistent_vars"]
    }

# --- Graph Nodes ---

def call_model(state: AgentState):
    model = ChatOpenAI(api_key=settings.OPENAI_API_KEY, model="gpt-4o")
    tools = [execute_data_cleaning, execute_visualization, execute_statistical_analysis]
    model_with_tools = model.bind_tools(tools)
    response = model_with_tools.invoke(state["messages"])
    return {"messages": [response]}

def call_tools(state: AgentState):
    """Custom tool node to handle our specialized outputs"""
    last_message = state["messages"][-1]
    tool_map = {
        "execute_data_cleaning": execute_data_cleaning,
        "execute_visualization": execute_visualization,
        "execute_statistical_analysis": execute_statistical_analysis
    }
    
    new_messages = []
    intermediate_outputs = []
    output_figures = []
    current_variables = state["current_variables"].copy()

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        # Pass state to tools that need it
        tool_args["state"] = state
        
        tool_func = tool_map[tool_name]
        result = tool_func.invoke(tool_args)
        
        # result is a dict with output, thought, code, etc.
        from langchain_core.messages import ToolMessage
        new_messages.append(ToolMessage(
            tool_call_id=tool_call["id"],
            content=json.dumps(result["output"])
        ))
        
        intermediate_outputs.append({
            "thought": result["thought"],
            "code": result["code"],
            "output": result["output"]
        })
        
        if "figures" in result:
            output_figures.extend(result["figures"])
            
        if "new_variables" in result:
            current_variables.update(result["new_variables"])

    return {
        "messages": new_messages,
        "current_variables": current_variables,
        "intermediate_outputs": intermediate_outputs,
        "output_figures": output_figures
    }

class AgentManager:
    def __init__(self):
        self.workflow = self._create_workflow()

    def _create_workflow(self):
        workflow = StateGraph(AgentState)
        workflow.add_node("agent", call_model)
        workflow.add_node("tools", call_tools)
        
        workflow.set_entry_point("agent")
        workflow.add_conditional_edges("agent", self._should_continue)
        workflow.add_edge("tools", "agent")
        
        return workflow.compile()

    def _should_continue(self, state: AgentState):
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            return "tools"
        return END

    async def process_query(self, db, session_id: int, user_id: int, query: str):
        # 1. Load session context
        session = db.query(models.AnalysisSession).filter(
            models.AnalysisSession.id == session_id,
            models.AnalysisSession.user_id == user_id
        ).first()
        
        if not session:
            raise Exception("Session not found")

        # 2. Reconstruct chat history
        messages = []
        for msg in session.messages:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            else:
                messages.append(AIMessage(content=msg.content))
        
        messages.append(HumanMessage(content=query))

        # 3. Load dataset variables
        current_variables = {}
        if session.dataset_id:
            dataset = db.query(models.Dataset).get(session.dataset_id)
            if dataset:
                df = pd.read_csv(dataset.file_path)
                var_name = dataset.filename.split('.')[0]
                current_variables[var_name] = df

        initial_state = {
            "messages": messages,
            "current_variables": current_variables,
            "session_id": session_id,
            "user_id": user_id,
            "intermediate_outputs": [],
            "output_figures": []
        }

        # 4. Invoke the workflow
        final_state = self.workflow.invoke(initial_state)

        # 5. Persist results
        # Save User Message
        db_user_msg = models.Message(session_id=session_id, role="user", content=query)
        db.add(db_user_msg)
        
        # Save Assistant Response
        assistant_msg = final_state["messages"][-1]
        db_assistant_msg = models.Message(session_id=session_id, role="assistant", content=assistant_msg.content)
        db.add(db_assistant_msg)
        
        db.commit()
        db.refresh(db_assistant_msg)

        # Save Visualizations
        for fig_json in final_state.get("output_figures", []):
            db_viz = models.Visualization(
                session_id=session_id,
                message_id=db_assistant_msg.id,
                figure_json=json.loads(fig_json),
                title="Generated Plot"
            )
            db.add(db_viz)
        
        db.commit()
        
        return {
            "synthesis": assistant_msg.content,
            "figures": final_state.get("output_figures", [])
        }
