# Aegis AI-First CRM - HCP Interaction Center

An AI-first Customer Relationship Management (CRM) system specifically designed for the Healthcare Professional (HCP) module. It empowers life science sales representatives to log, edit, and manage their interactions with HCPs. 

Representatives can log interactions through two seamless workflows:
1. **A highly-polished structured form** featuring Google Inter typography, dynamic inputs, sentiment radios, materials checklists, and suggestion chips.
2. **A conversational AI Assistant** powered by a LangGraph Agent and Groq's `gemma2-9b-it` LLM, which automatically extracts details, seeds the draft form in real-time, and logs/edits data via background tool execution.

---

## Technical Stack & Architecture

### Backend (Python)
- **Framework**: FastAPI (async REST endpoints, CORS middleware).
- **AI Agent Framework**: LangGraph (StateGraph orchestration, conditional routing).
- **LLM Engine**: Groq Cloud (`gemma2-9b-it` / `llama-3.3-70b-versatile` fallback).
- **ORM & Database**: SQLAlchemy targeting a local SQLite connection (fully configurable to MySQL or PostgreSQL via environment variables).

### Frontend (React)
- **Scaffold**: Vite (fast module bundling).
- **State Management**: Redux Toolkit & React-Redux (maintaining global states for form drafts, active entities, and message feeds).
- **Aesthetics**: Premium Custom Vanilla CSS featuring glassmorphism, responsive split-grid layouts, custom scrollbars, and interactive micro-animations.
- **Icons**: Lucide React.
- **Typography**: Google Inter font.

---

## Project Directory Structure

```text
ai-crm-hcp-module/
├── backend/
│   ├── .env                  # Environment configurations (GROQ_API_KEY)
│   ├── main.py                # FastAPI app entrypoint & API endpoints
│   ├── agent.py               # LangGraph state graph & LLM Tools
│   ├── models.py              # SQLAlchemy database tables (HCP, Product, Interaction, Task)
│   ├── database.py            # Database engine & Session makers
│   ├── seed.py                # Database seeder script
│   ├── test_backend.py        # Automated test suite
│   ├── requirements.txt       # Python package dependencies
│   └── crm.db                 # Seeded SQLite database file
├── frontend/
│   ├── index.html             # Google Inter Font link & app mount
│   ├── package.json           # npm dependencies
│   └── src/
│       ├── main.jsx           # Mounting with Redux Provider wrapper
│       ├── App.jsx            # Split-pane UI layout & event handlers
│       ├── store.js           # Redux state slices & Async Thunks
│       └── index.css          # Design system & dark glassmorphic styling
└── README.md                  # This documentation file
```

---

## LangGraph AI Agent & Tools

### Role of the LangGraph Agent
The LangGraph agent acts as the brain of the CRM conversational panel. When a sales representative type or pastes information, the agent processes the chat history, uses the LLM to understand intent, and decides whether to fetch more information (HCP details, marketing brochure details) or execute actions (populate form draft, log/edit interactions in the database).

By integrating the agent directly with our Redux store, any tool called by the agent (e.g., `update_ui_draft` or `log_interaction`) immediately syncs and reflects in the structured form on the user's screen in real-time.

### The 5 Required Tools (+ 1 Extra)

1. **`search_hcp(query: str)`**:
   - Searches the database table for HCP profiles matching a name, specialty, or clinic hospital.
   - If exactly one HCP matches, the agent automatically associates it with the interaction draft.

2. **`log_interaction(hcp_id, date, time, interaction_type, attendees, topics, sentiment, outcomes, follow_ups, material_ids)`**:
   - Captures and commits interaction details directly to the SQL database.
   - Summarizes and associates any shared marketing materials or patient samples.

3. **`edit_interaction(interaction_id, updates)`**:
   - Updates fields of an existing logged record inside the SQL database.
   - Used when a rep says: "Change the sentiment of my last meeting to Positive" or "Add Dr. Sharma to the meeting attendees."

4. **`get_product_info(query: str)`**:
   - Queries the product details database to fetch marketing materials (PDFs, brochures) and sample starter kits, along with their current inventory stock levels.

5. **`create_follow_up_task(hcp_id, description, due_date)`**:
   - Creates a pending sales reminder task in the database for the representative.

6. **`update_ui_draft(...)` [Extra State Tool]**:
   - Dynamically updates the frontend React/Redux form values without committing them to the database yet. It allows the rep to see the form filling up on their screen as they chat.

---

## Setup & How to Run

### 1. Prerequisites
- **Python**: version `3.10` or higher.
- **Node.js**: version `20` or higher, along with `npm`.
- **Groq API Key**: Create an API Key in the [Groq Console](https://console.groq.com/keys).

### 2. Backend Setup
1. Open a terminal and navigate to the backend folder:
   ```powershell
   cd backend
   ```
2. Create and activate a virtual environment:
   ```powershell
   python -m venv venv
   # On Windows:
   .\venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install package dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Open the `.env` file and input your Groq API Key:
   ```text
   GROQ_API_KEY=gsk_your_actual_key_here
   ```
5. Seed the local database with pre-populated HCPs and products:
   ```bash
   python seed.py
   ```
6. Run the FastAPI development server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   *The Swagger API documentation will be available at `http://127.0.0.1:8000/docs`.*

### 3. Frontend Setup
1. Open a new terminal window and navigate to the frontend folder:
   ```bash
   cd frontend
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. Launch the Vite local dev server:
   ```bash
   npm run dev
   ```
4. Open your browser and navigate to the local server URL (usually `http://localhost:5173`).

---

## Demonstration Guide for Video Submission

For your 10-15 minute video recording, follow this structured demo sequence:

1. **Introduction**:
   - State the project title: **Aegis AI-First CRM - HCP Module**.
   - Briefly explain the core objective: a dual-method log screen allowing medical sales reps to log interactions via a form or an AI-assistant chat.
   
2. **Review Project Structure**:
   - Open VS Code/IDE and show the `backend` and `frontend` directories, detailing `agent.py` (LangGraph agent & tools), `main.py` (FastAPI), and `App.jsx`/`store.js` (React/Redux).
   
3. **Seeded Data Walkthrough**:
   - Scroll down to the bottom of the webpage and show the **Database Logged HCP Interactions History** table, which is loaded directly from the database containing mock logs.

4. **Structured Form Flow Demo**:
   - Select an HCP from the dropdown (e.g. *Dr. John Smith*).
   - Enter Date/Time, attendees, outcomes.
   - Under **Topics Discussed**, choose one of the simulated voice transcripts from the dropdown (e.g. Transcript #1 or #2) and click **Summarize Voice**. Watch the FastAPI server return a parsed summary using the LLM and auto-populate the textarea.
   - Toggle shared materials (checkboxes) and observed sentiment.
   - Click **Log HCP Interaction** and verify it updates the history table instantly.

5. **AI Agent Chat Flow Demo (All 5 Tools)**:
   - Go to the chat panel on the right.
   - **Demo `search_hcp`**: Type: *"Find a doctor specializing in Oncology."* The agent will call the tool and return *Dr. Alice Sharma* along with her specialty and hospital.
   - **Demo `update_ui_draft` & Real-Time Sync**: Type: *"I met Dr. Alice Sharma today at 2 PM. We discussed the OncoBoost clinical trial. She was very positive about it."* Notice how the structured form on the left instantly populates with Alice Sharma as HCP, date as today, time as 14:00, topics as the clinical trial, and sentiment as Positive!
   - **Demo `get_product_info`**: Type: *"Do we have any marketing brochures or report details on OncoBoost?"* The agent queries the database and reports the available trial report PDF and stock.
   - **Demo `log_interaction` via Chat**: Type: *"Looks good, let's log this interaction."* The agent logs it and returns the confirmation. Look at the database table at the bottom to verify it is appended.
   - **Demo `create_follow_up_task`**: Type: *"Create a follow-up reminder for Alice Sharma to send her the trial report PDF next week."* The agent schedules it and returns a success confirmation.
   - **Demo `edit_interaction`**: Type: *"Actually, I made a mistake, update the last logged meeting sentiment to Negative."* The agent locates the log, modifies it, and the database table updates to show 'Negative'.
   - **Demo Form Loading**: Click **Load to Edit** on any row in the history table. Verify the form fields immediately load that record, allowing you to manually edit and click **Update Interaction Logs**.
#   a i - f i r s t - c r m - h c p - m o d u l e  
 #   a i - f i r s t - c r m - h c p - m o d u l  
 #   a i - f i r s t - c r m - h c p - m o d u l  
 #   a i - f i r s t - c r m - h c p - m o d u l  
 #   a i - f i r s t - c r m - h c p - m o d u l  
 