import os
import json
from typing import Annotated, Sequence, TypedDict, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from database import SessionLocal
import models

# ----------------------------------------------------
# 1. State Definition
# ----------------------------------------------------
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    form_draft: Dict[str, Any]
    current_hcp_id: Optional[int]
    current_interaction_id: Optional[int]

# Helper to merge draft updates
def get_empty_draft() -> Dict[str, Any]:
    return {
        "hcp_id": None,
        "hcp_name": "",
        "type": "Meeting",
        "date": "",
        "time": "",
        "attendees": "",
        "topics": "",
        "sentiment": "Neutral",
        "outcomes": "",
        "follow_ups": "",
        "material_ids": []
    }

# ----------------------------------------------------
# 2. Tools Definitions
# ----------------------------------------------------

@tool
def search_hcp(query: str) -> str:
    """
    Search for Healthcare Professionals (HCPs) in the database.
    Use this to find an HCP's ID, specialty, hospital, or email when the user mentions a doctor's name or clinic.
    """
    db = SessionLocal()
    try:
        hcps = db.query(models.HCP).filter(
            (models.HCP.name.like(f"%{query}%")) |
            (models.HCP.specialty.like(f"%{query}%")) |
            (models.HCP.hospital.like(f"%{query}%"))
        ).all()
        
        if not hcps:
            return json.dumps({"status": "no_results", "message": f"No HCPs found matching '{query}'."})
        
        results = []
        for h in hcps:
            results.append({
                "id": h.id,
                "name": h.name,
                "specialty": h.specialty,
                "hospital": h.hospital,
                "email": h.email
            })
        return json.dumps({"status": "success", "results": results}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
    finally:
        db.close()

@tool
def get_product_info(query: str) -> str:
    """
    Retrieve information about products, marketing materials (PDFs, brochures), or samples.
    Use this to look up available materials/samples and their current stock levels when requested.
    """
    db = SessionLocal()
    try:
        products = db.query(models.ProductInfo).filter(
            (models.ProductInfo.name.like(f"%{query}%")) |
            (models.ProductInfo.description.like(f"%{query}%"))
        ).all()
        
        if not products:
            return json.dumps({"status": "no_results", "message": f"No products or materials found matching '{query}'."})
        
        results = []
        for p in products:
            results.append({
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "material_type": p.material_type,
                "stock": p.stock
            })
        return json.dumps({"status": "success", "results": results}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
    finally:
        db.close()

@tool
def log_interaction(
    hcp_id: int,
    date: str,
    time: str,
    interaction_type: str,
    attendees: str,
    topics: str,
    sentiment: str,
    outcomes: str,
    follow_ups: str,
    material_ids: List[int] = []
) -> str:
    """
    Log a new HCP interaction to the database.
    Must specify interaction_type (one of 'Meeting', 'Call', 'Email', 'Conference'), hcp_id, date (YYYY-MM-DD),
    time (HH:MM), attendees, topics, sentiment ('Positive', 'Neutral', 'Negative'), outcomes, and follow_ups.
    If materials are shared, pass their IDs in material_ids.
    """
    db = SessionLocal()
    try:
        hcp = db.query(models.HCP).filter(models.HCP.id == hcp_id).first()
        if not hcp:
            return json.dumps({"status": "error", "message": f"HCP with ID {hcp_id} not found."})
        
        # Standardize interaction type capitalization
        i_type = interaction_type.strip().capitalize()
        if i_type not in ["Meeting", "Call", "Email", "Conference"]:
            i_type = "Meeting"
            
        # Standardize sentiment
        i_sent = sentiment.strip().capitalize()
        if i_sent not in ["Positive", "Neutral", "Negative"]:
            i_sent = "Neutral"

        interaction = models.Interaction(
            hcp_id=hcp_id,
            date=date,
            time=time,
            type=i_type,
            attendees=attendees,
            topics=topics,
            sentiment=i_sent,
            outcomes=outcomes,
            follow_ups=follow_ups
        )
        
        if material_ids:
            materials = db.query(models.ProductInfo).filter(models.ProductInfo.id.in_(material_ids)).all()
            interaction.materials.extend(materials)
            
        db.add(interaction)
        db.commit()
        
        return json.dumps({
            "status": "success",
            "message": f"Successfully logged interaction with ID {interaction.id} for HCP {hcp.name}.",
            "interaction_id": interaction.id,
            "details": {
                "hcp_id": hcp_id,
                "hcp_name": hcp.name,
                "date": date,
                "time": time,
                "type": i_type,
                "attendees": attendees,
                "topics": topics,
                "sentiment": i_sent,
                "outcomes": outcomes,
                "follow_ups": follow_ups,
                "material_ids": material_ids
            }
        })
    except Exception as e:
        db.rollback()
        return json.dumps({"status": "error", "message": str(e)})
    finally:
        db.close()

@tool
def edit_interaction(
    interaction_id: int,
    updates: Dict[str, Any]
) -> str:
    """
    Edit an existing logged interaction in the database.
    Pass the interaction_id and a dictionary of fields to update (e.g. date, time, topics, sentiment, outcomes, follow_ups, material_ids).
    """
    db = SessionLocal()
    try:
        interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
        if not interaction:
            return json.dumps({"status": "error", "message": f"Interaction with ID {interaction_id} not found."})
        
        hcp = db.query(models.HCP).filter(models.HCP.id == interaction.hcp_id).first()
        
        # Update text fields
        for field in ["date", "time", "attendees", "topics", "sentiment", "outcomes", "follow_ups"]:
            if field in updates and updates[field] is not None:
                val = updates[field]
                if field == "sentiment":
                    val = str(val).strip().capitalize()
                    if val not in ["Positive", "Neutral", "Negative"]:
                        val = "Neutral"
                elif field == "type":
                    val = str(val).strip().capitalize()
                    if val not in ["Meeting", "Call", "Email", "Conference"]:
                        val = "Meeting"
                setattr(interaction, field, val)
                
        # Update type if present
        if "type" in updates and updates["type"] is not None:
            val = str(updates["type"]).strip().capitalize()
            if val in ["Meeting", "Call", "Email", "Conference"]:
                interaction.type = val

        # Update materials if material_ids are provided
        if "material_ids" in updates and updates["material_ids"] is not None:
            material_ids = updates["material_ids"]
            interaction.materials.clear()
            materials = db.query(models.ProductInfo).filter(models.ProductInfo.id.in_(material_ids)).all()
            interaction.materials.extend(materials)

        db.commit()
        
        # Build updated detail dict
        material_ids = [m.id for m in interaction.materials]
        return json.dumps({
            "status": "success",
            "message": f"Successfully updated interaction with ID {interaction_id}.",
            "interaction_id": interaction_id,
            "details": {
                "hcp_id": interaction.hcp_id,
                "hcp_name": hcp.name if hcp else "",
                "date": interaction.date,
                "time": interaction.time,
                "type": interaction.type,
                "attendees": interaction.attendees,
                "topics": interaction.topics,
                "sentiment": interaction.sentiment,
                "outcomes": interaction.outcomes,
                "follow_ups": interaction.follow_ups,
                "material_ids": material_ids
            }
        })
    except Exception as e:
        db.rollback()
        return json.dumps({"status": "error", "message": str(e)})
    finally:
        db.close()

@tool
def create_follow_up_task(hcp_id: int, description: str, due_date: str) -> str:
    """
    Create a follow-up task or reminder in the database for the sales representative.
    Requires hcp_id, description of the task, and a due_date (YYYY-MM-DD).
    """
    db = SessionLocal()
    try:
        hcp = db.query(models.HCP).filter(models.HCP.id == hcp_id).first()
        if not hcp:
            return json.dumps({"status": "error", "message": f"HCP with ID {hcp_id} not found."})
        
        task = models.Task(
            hcp_id=hcp_id,
            description=description,
            due_date=due_date,
            status="Pending"
        )
        db.add(task)
        db.commit()
        
        return json.dumps({
            "status": "success",
            "message": f"Successfully created follow-up task for {hcp.name}: '{description}' due by {due_date}.",
            "task_id": task.id
        })
    except Exception as e:
        db.rollback()
        return json.dumps({"status": "error", "message": str(e)})
    finally:
        db.close()

@tool
def update_ui_draft(
    hcp_id: Optional[int] = None,
    hcp_name: Optional[str] = None,
    interaction_type: Optional[str] = None,
    date: Optional[str] = None,
    time: Optional[str] = None,
    attendees: Optional[str] = None,
    topics: Optional[str] = None,
    sentiment: Optional[str] = None,
    outcomes: Optional[str] = None,
    follow_ups: Optional[str] = None,
    material_ids: Optional[List[int]] = None
) -> str:
    """
    Update the client-side draft interaction form details without saving them to the database.
    Use this tool when the user provides partial information and you want to reflect it immediately in the UI form
    before logging it. Do not call this tool if you are already logging or editing an interaction.
    """
    # This tool is intercepted by the graph execution to update form_draft.
    return json.dumps({
        "status": "success",
        "message": "Updated draft state.",
        "updates": {k: v for k, v in locals().items() if v is not None and k not in ["db", "SessionLocal"]}
    })

ALL_TOOLS = [search_hcp, get_product_info, log_interaction, edit_interaction, create_follow_up_task, update_ui_draft]
TOOL_MAP = {t.name: t for t in ALL_TOOLS}

# ----------------------------------------------------
# 3. Agent Graph Nodes & Edges
# ----------------------------------------------------

def run_agent(state: AgentState) -> Dict[str, Any]:
    """Agent node that calls Groq LLM to figure out the next step."""
    messages = state.get("messages", [])
    
    # Setup Groq model
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        # Fallback for checking API keys
        return {"messages": [SystemMessage(content="ERROR: GROQ_API_KEY environment variable is not set. Please set it in backend/.env.")]}
    
    llm = ChatGroq(
        model_name="llama-3.3-70b-versatile",
        groq_api_key=api_key,
        temperature=0.1
    ).bind_tools(ALL_TOOLS)
    
    # Build System message
    system_prompt = (
        "You are an expert life science CRM Assistant. Your goal is to help pharmaceutical/medical device field representatives "
        "manage and log their interactions with Healthcare Professionals (HCPs).\n\n"
        "You have access to tools to search HCPs, search products/materials, log interactions to the database, "
        "edit interactions in the database, and schedule tasks/reminders. You can also update the draft form UI at any time "
        "using `update_ui_draft` if the user is providing details but is not ready to save yet.\n\n"
        "GUIDELINES:\n"
        "1. Extract parameters from user input. E.g., if user says 'today', parse the current date from context (assume today is 2026-07-10).\n"
        "2. If user mentions a doctor by name (e.g. 'Dr. Alice Sharma'), FIRST search for them using `search_hcp` to find their correct ID and details.\n"
        "3. When you have enough information to fill out the form fields, you can call `update_ui_draft` to populate the form on the screen for the user.\n"
        "4. If the user tells you to 'save', 'log', or 'record' the interaction (or it is clearly implied they want to log it), call `log_interaction` with the exact fields.\n"
        "5. If they want to modify a logged interaction, call `edit_interaction`.\n"
        "6. Return concise, helpful responses explaining what you have done and what tools you executed.\n\n"
        f"Current state: Form Draft: {json.dumps(state.get('form_draft', {}))}. Selected HCP ID: {state.get('current_hcp_id')}. Selected Interaction ID: {state.get('current_interaction_id')}."
    )
    
    # We prefix system prompt
    full_messages = [SystemMessage(content=system_prompt)] + list(messages)
    
    response = llm.invoke(full_messages)
    return {"messages": [response]}

def execute_tools(state: AgentState) -> Dict[str, Any]:
    """Node that handles execution of tools called by the agent."""
    messages = state.get("messages", [])
    last_message = messages[-1]
    
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return {}
        
    tool_outputs = []
    updated_draft = dict(state.get("form_draft", get_empty_draft()))
    updated_hcp_id = state.get("current_hcp_id")
    updated_interaction_id = state.get("current_interaction_id")
    
    for tool_call in last_message.tool_calls:
        name = tool_call["name"]
        args = tool_call["args"]
        call_id = tool_call["id"]
        
        if name in TOOL_MAP:
            tool_func = TOOL_MAP[name]
            result_str = tool_func.invoke(args)
            
            try:
                result_json = json.loads(result_str)
            except Exception:
                result_json = {"status": "error", "message": result_str}
                
            # Intercept specific tools to update state parameters
            if name == "log_interaction" and result_json.get("status") == "success":
                details = result_json["details"]
                updated_interaction_id = result_json["interaction_id"]
                updated_hcp_id = details["hcp_id"]
                # Sync form draft with logged interaction
                for k, v in details.items():
                    if k == "type":
                        updated_draft["type"] = v
                    elif k in updated_draft:
                        updated_draft[k] = v
                updated_draft["hcp_name"] = details.get("hcp_name", "")
                
            elif name == "edit_interaction" and result_json.get("status") == "success":
                details = result_json["details"]
                updated_interaction_id = result_json["interaction_id"]
                for k, v in details.items():
                    if k == "type":
                        updated_draft["type"] = v
                    elif k in updated_draft:
                        updated_draft[k] = v
                updated_draft["hcp_name"] = details.get("hcp_name", "")

            elif name == "update_ui_draft" and result_json.get("status") == "success":
                # User is updating form draft parameters
                updates = args
                for k, v in updates.items():
                    if k == "interaction_type":
                        updated_draft["type"] = v
                    elif k in updated_draft:
                        updated_draft[k] = v
                
                # If hcp_id changed, try to find hcp_name
                if "hcp_id" in updates and updates["hcp_id"]:
                    updated_hcp_id = updates["hcp_id"]
                    db = SessionLocal()
                    try:
                        h = db.query(models.HCP).filter(models.HCP.id == updated_hcp_id).first()
                        if h:
                            updated_draft["hcp_name"] = h.name
                            updated_draft["hcp_id"] = h.id
                    finally:
                        db.close()
                elif "hcp_name" in updates and updates["hcp_name"]:
                    updated_draft["hcp_name"] = updates["hcp_name"]

            elif name == "search_hcp" and result_json.get("status") == "success":
                # If search succeeded and returned exactly one HCP, auto-populate the draft with it
                results = result_json.get("results", [])
                if len(results) == 1:
                    h = results[0]
                    updated_hcp_id = h["id"]
                    updated_draft["hcp_id"] = h["id"]
                    updated_draft["hcp_name"] = h["name"]
                    
            tool_outputs.append(ToolMessage(
                content=result_str,
                tool_call_id=call_id,
                name=name
            ))
            
    return {
        "messages": tool_outputs,
        "form_draft": updated_draft,
        "current_hcp_id": updated_hcp_id,
        "current_interaction_id": updated_interaction_id
    }

def route_agent(state: AgentState):
    """Router edge to decide if tool execution or END is needed."""
    messages = state.get("messages", [])
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END

# ----------------------------------------------------
# 4. Construct LangGraph Workflow
# ----------------------------------------------------

workflow = StateGraph(AgentState)
workflow.add_node("agent", run_agent)
workflow.add_node("tools", execute_tools)

workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", route_agent, {"tools": "tools", END: END})
workflow.add_edge("tools", "agent")

app_agent = workflow.compile()
