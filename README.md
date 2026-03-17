# Luma Agentic System: Architecture and Workflow

This document provides a comprehensive breakdown of the Luma ChatBot system, its core components, and the underlying LangGraph orchestration that powers its intelligence. This system includes the latest integration of the Data Analysis Agent.

---

## System Overview

The system is built as a multi-layered AI application that combines Natural Language Processing (NLP), Retrieval-Augmented Generation (RAG), Structured Data Analysis (SQL), and Business Intelligence Analytics.

### 1. Orchestration Layer (app.py)
* Web Framework: Flask handles HTTP requests and serves the frontend.
* Session Bridge: Uses the SessionManager to persist chat history in a local SQLite database (chatbot.db).
* Media Engine: Integrates AssemblyAI for voice-to-text transcription and OpenAI for Roman-Urdu transliteration.

### 2. The Intelligence Brain (react_agent_system_langgraph.py)
This is where the magic happens. Luma uses a LangGraph State Machine to process queries. Instead of a single flat prompt, it breaks down the user's intent and routes it to specialized Agents (Nodes).

### 3. Data and Knowledge Layer
* Vector Memory (chat.py and ingest.py): A ChromaDB vector database stores portal documentation. When you ask how to do something, Luma retrieves the right manual page.
* Operational Data (mysql_service.py): Connects to the real system database to fetch live records like distributors, employees, or regions.
* Sales Analytics (data_analysis_agent): Ingests JSON payloads to dynamically plot and summarize high-level BI charts for management.

---

## Node Management: Router-Based Design

Luma uses a Router-Based Centralized Decision pattern (often called a Brain or Manager router). 

It is NOT strictly Supervisor-based. In a Supervisor pattern, a central node repeatedly calls workers and receives reports until the task is done. 
Instead, it is a High-Precision Dispatcher. The route_decision node analyzes the query once and dispatches it to the single best specialist. This is faster and more reliable for deterministic tasks like How-to tutorials, SQL generation, or Data Analysis.

Key Advantage: By routing early, we save tokens and latency because the Tutorial Agent does not need to know how to write SQL, the SQL Agent does not need to read tutorials, and the Data Analysis agent does not need to generate strict database queries.

---

## The Agentic Workflow

The following describes exactly how a user query moves through the LangGraph system from start to finish.

### Phase 1: Request Analysis
When a user submits a query, it first enters the analyze_request node. This node uses a Language Model to evaluate the text and classify the user's intent into one of several predefined categories (e.g., general, tutorial, sql_query, data_analysis).

### Phase 2: The Routing Decision
The system then passes the classified intent and a confidence score to the route_decision node. Based on the intent detected, the router forwards the state to one of the following specialized sub-agents:

1. General Agent: 
Targeted for casual conversation. If a user asks "Salam Luma, kaise ho?", the general agent crafts a plain conversational response, usually greeting the user in Roman-Urdu and asking how to help.

2. Tutorial Agent: 
Targeted for instructional queries. If a user asks "How to add a new region?", this agent uses RAG to retrieve the exact steps from the knowledge base, returning a step-by-step breakdown using bullet points.

3. SQL Query Pipeline: 
Targeted for database extraction. If a user asks for a "List of permanent employees in Karachi", the query goes to the sql_query_generator, which writes the exact MySQL query. The result is passed to the sql_runner to execute against the live database, and finally reaches the sql_data_analyst_agent which formats the raw rows into a readable response.

4. Data Analysis (BI) Agent: 
Targeted for high-level sales insights. If a user asks "Analyse the sales data", it reads the JSON dataset, uses an LLM to extract top 10 insights, and concurrently generates 10 visual graphs (saved locally) before returning a unified Markdown summary.

5. Capabilities Agent: 
Targeted for self-discovery queries. If a user asks "What can you do for me?", this agent generates a comprehensive list of all the tools and features the chatbot supports.

6. Clarification Agent: 
Targeted for deep-dives into previous answers. If a user asks "Explain step 3 of the creation process", this agent takes the previous specific tutorial context and simplifies it for the user.

7. History Summary Agent: 
Targeted for memory recall. If a user asks "What was my last question about distributors?", it looks through the SQLite chatbot database to summarize past conversations.

8. Fallback Agent: 
Triggered automatically when the router's confidence score in the intent matching is too low. It politely explains that it is a portal assistant and suggests system-relevant actions to guide the user back on track.

### Phase 3: Final Validation and Output
Regardless of which specialized agent performed the work, the result is forwarded to a final validate_response node. This node acts as a quality assurance check, ensuring the response is formatted correctly and aligns with the expected output standard. Once cleared, the state hits the END node, and the final text and graphs are returned to the Flask application to be sent to the user interface.

---

## Key Files and Their Responsibilities

1. app.py: The Gatekeeper - Entry point for the UI/API (Flask routing).
2. chat.py: The Librarian - Handles documentation embedding search (RAG).
3. ingest.py: The Teacher - Teaches the AI new tutorial JSONs and stores them in Chroma.
4. database.py: The Record Keeper - Sets up the SQLite database initialization.
5. mysql_service.py: The Data Courier - Handles the direct Python-to-MySQL connection stream.
6. agent_test.py: The Prototyper - The standalone script used to prototype the Data Analysis logic before full integration.
7. react_agent_system_langgraph.py: The Brain - Contains the LangGraph State Graph logic, prompt templates, and all specialized agent nodes.
8. session_manager.py: The Folder - Manages individual user chat sessions tying DB context together.
