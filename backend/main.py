import os
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

import models
from database import get_db, engine, Base
from agent import app_agent, get_empty_draft
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq

# Load env variables
load_dotenv()

# Initialize tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI-First CRM HCP API")

# Add CORS Middleware to support React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify front-end domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------
# Pydantic Schemas
# ----------------------------------------------------

class HCPSchema(BaseModel):
    id: int
    name: str
    specialty: str
    hospital: str
    email: str

    class Config:
        from_attributes = True

class ProductSchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    material_type: str
    stock: int

    class Config:
        from_attributes = True

class InteractionCreateSchema(BaseModel):
    hcp_id: int
    date: str
    time: str
    type: str
    attendees: Optional[str] = ""
    topics: Optional[str] = ""
    sentiment: Optional[str] = "Neutral"
    outcomes: Optional[str] = ""
    follow_ups: Optional[str] = ""
    material_ids: List[int] = []

class InteractionSchema(BaseModel):
    id: int
    hcp_id: int
    hcp_name: str = ""
    date: str
    time: str
    type: str
    attendees: Optional[str] = ""
    topics: Optional[str] = ""
    sentiment: Optional[str] = "Neutral"
    outcomes: Optional[str] = ""
    follow_ups: Optional[str] = ""
    materials: List[ProductSchema] = []

    class Config:
        from_attributes = True

class ChatMessageSchema(BaseModel):
    sender: str  # 'user' or 'ai'
    text: str

class ChatRequest(BaseModel):
    messages: List[ChatMessageSchema]
    form_draft: Dict[str, Any]
    current_hcp_id: Optional[int] = None
    current_interaction_id: Optional[int] = None

class ChatResponse(BaseModel):
    messages: List[ChatMessageSchema]
    form_draft: Dict[str, Any]
    current_hcp_id: Optional[int] = None
    current_interaction_id: Optional[int] = None

class VoiceSummarizeRequest(BaseModel):
    transcript: str

# ----------------------------------------------------
# Endpoints
# ----------------------------------------------------

@app.get("/api/hcps", response_model=List[HCPSchema])
def get_hcps(q: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.HCP)
    if q:
        query = query.filter(
            (models.HCP.name.like(f"%{q}%")) |
            (models.HCP.specialty.like(f"%{q}%")) |
            (models.HCP.hospital.like(f"%{q}%"))
        )
    return query.all()

@app.get("/api/products", response_model=List[ProductSchema])
def get_products(db: Session = Depends(get_db)):
    return db.query(models.ProductInfo).all()

@app.get("/api/interactions", response_model=List[InteractionSchema])
def get_interactions(db: Session = Depends(get_db)):
    interactions = db.query(models.Interaction).all()
    results = []
    for i in interactions:
        materials_schemas = [
            ProductSchema(
                id=m.id,
                name=m.name,
                description=m.description,
                material_type=m.material_type,
                stock=m.stock
            ) for m in i.materials
        ]
        results.append(
            InteractionSchema(
                id=i.id,
                hcp_id=i.hcp_id,
                hcp_name=i.hcp.name if i.hcp else "",
                date=i.date,
                time=i.time,
                type=i.type,
                attendees=i.attendees,
                topics=i.topics,
                sentiment=i.sentiment,
                outcomes=i.outcomes,
                follow_ups=i.follow_ups,
                materials=materials_schemas
            )
        )
    return results

@app.post("/api/interactions", response_model=InteractionSchema)
def create_interaction(data: InteractionCreateSchema, db: Session = Depends(get_db)):
    hcp = db.query(models.HCP).filter(models.HCP.id == data.hcp_id).first()
    if not hcp:
        raise HTTPException(status_code=404, detail="HCP not found")
        
    interaction = models.Interaction(
        hcp_id=data.hcp_id,
        date=data.date,
        time=data.time,
        type=data.type,
        attendees=data.attendees,
        topics=data.topics,
        sentiment=data.sentiment,
        outcomes=data.outcomes,
        follow_ups=data.follow_ups
    )
    
    if data.material_ids:
        materials = db.query(models.ProductInfo).filter(models.ProductInfo.id.in_(data.material_ids)).all()
        interaction.materials.extend(materials)
        
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    
    materials_schemas = [
        ProductSchema(
            id=m.id,
            name=m.name,
            description=m.description,
            material_type=m.material_type,
            stock=m.stock
        ) for m in interaction.materials
    ]
    
    return InteractionSchema(
        id=interaction.id,
        hcp_id=interaction.hcp_id,
        hcp_name=hcp.name,
        date=interaction.date,
        time=interaction.time,
        type=interaction.type,
        attendees=interaction.attendees,
        topics=interaction.topics,
        sentiment=interaction.sentiment,
        outcomes=interaction.outcomes,
        follow_ups=interaction.follow_ups,
        materials=materials_schemas
    )

@app.put("/api/interactions/{id}", response_model=InteractionSchema)
def update_interaction(id: int, data: InteractionCreateSchema, db: Session = Depends(get_db)):
    interaction = db.query(models.Interaction).filter(models.Interaction.id == id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
        
    hcp = db.query(models.HCP).filter(models.HCP.id == data.hcp_id).first()
    if not hcp:
        raise HTTPException(status_code=404, detail="HCP not found")
        
    interaction.hcp_id = data.hcp_id
    interaction.date = data.date
    interaction.time = data.time
    interaction.type = data.type
    interaction.attendees = data.attendees
    interaction.topics = data.topics
    interaction.sentiment = data.sentiment
    interaction.outcomes = data.outcomes
    interaction.follow_ups = data.follow_ups
    
    # Update materials
    interaction.materials.clear()
    if data.material_ids:
        materials = db.query(models.ProductInfo).filter(models.ProductInfo.id.in_(data.material_ids)).all()
        interaction.materials.extend(materials)
        
    db.commit()
    db.refresh(interaction)
    
    materials_schemas = [
        ProductSchema(
            id=m.id,
            name=m.name,
            description=m.description,
            material_type=m.material_type,
            stock=m.stock
        ) for m in interaction.materials
    ]
    
    return InteractionSchema(
        id=interaction.id,
        hcp_id=interaction.hcp_id,
        hcp_name=hcp.name,
        date=interaction.date,
        time=interaction.time,
        type=interaction.type,
        attendees=interaction.attendees,
        topics=interaction.topics,
        sentiment=interaction.sentiment,
        outcomes=interaction.outcomes,
        follow_ups=interaction.follow_ups,
        materials=materials_schemas
    )

@app.post("/api/chat", response_model=ChatResponse)
def chat_with_agent(payload: ChatRequest):
    # Convert incoming history into LangChain message objects
    langchain_messages = []
    for msg in payload.messages:
        if msg.sender == "user":
            langchain_messages.append(HumanMessage(content=msg.text))
        else:
            langchain_messages.append(AIMessage(content=msg.text))
            
    # Compile initial state
    initial_state = {
        "messages": langchain_messages,
        "form_draft": payload.form_draft or get_empty_draft(),
        "current_hcp_id": payload.current_hcp_id,
        "current_interaction_id": payload.current_interaction_id
    }
    
    try:
        # Run state machine
        final_state = app_agent.invoke(initial_state)
        
        # Compile response message list
        output_messages = []
        for msg in final_state.get("messages", []):
            if isinstance(msg, HumanMessage):
                output_messages.append(ChatMessageSchema(sender="user", text=msg.content))
            elif isinstance(msg, AIMessage):
                # Ignore tool message contents in user view unless they are part of final response
                if msg.content:
                    output_messages.append(ChatMessageSchema(sender="ai", text=msg.content))
                    
        # Return updated state details
        return ChatResponse(
            messages=output_messages,
            form_draft=final_state.get("form_draft", get_empty_draft()),
            current_hcp_id=final_state.get("current_hcp_id"),
            current_interaction_id=final_state.get("current_interaction_id")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution error: {str(e)}")

@app.post("/api/voice-summarize")
def summarize_voice_note(payload: VoiceSummarizeRequest):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not set in backend/.env")
        
    try:
        llm = ChatGroq(
            model_name="llama-3.3-70b-versatile",
            groq_api_key=api_key,
            temperature=0.1
        )
        system_prompt = (
            "You are a medical scribe. Summarize the following raw voice transcription of a medical sales rep's meeting "
            "with a doctor. Produce a concise clinical/interaction summary (1-3 sentences) detailing key points discussed, "
            "doctor reactions, and any requested materials. Do not include introductory text like 'Here is the summary'."
        )
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=payload.transcript)
        ])
        return {"summary": response.content.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/seed")
def trigger_seed():
    from seed import seed_database
    seed_database()
    return {"status": "success", "message": "Database seeded successfully."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
