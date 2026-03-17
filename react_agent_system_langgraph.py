import os
import json
import re
from typing import TypedDict, Any, Dict, List, Annotated, Optional
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage, SystemMessage
from openai import OpenAI
import textwrap
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

from chat import get_bot_response, format_step_text
from mysql_service import MySQLService

load_dotenv()
MODEL = os.getenv("OPENAI_MODEL")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATA_FILE      = Path(__file__).parent / "data.json"
GRAPHS_DIR     = Path(__file__).parent / "analysis_graphs"
GRAPHS_DIR.mkdir(exist_ok=True)
MAX_RECORDS_FOR_LLM = 200

DATA_ANALYSIS_SYSTEM_PROMPT = textwrap.dedent("""
You are an expert Business Intelligence & Sales Data Analyst.

You will receive a summarised JSON payload of sales transaction records. The data
may represent a single user, a specific region, a product category, or the entire
organisation — derive your insights purely from what is present, without assuming
what is absent.

Fields you may encounter include:
  region / territory / distributor / employee / product / brand / SKU,
  quantity sold (sumqty), revenue metrics (beforediscount, total_after_tax,
  total_tp_incl, ex_factory_price, distributor_incl), discount values, visits,
  lppc, drop-size, weightTon, and date ranges.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CURRENCY RULE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ALWAYS express every monetary / revenue figure using "Rs." as the currency
symbol.  Never use "$", "USD", or any other symbol.
Example: Rs. 42,720,736

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR TASK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Critically analyse the data and return EXACTLY the top 10 key business insights.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT  (strict markdown — follow exactly)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 📊 Sales Data Analysis Report

> A critical review of the available sales data covering key performance
> indicators across regions, distributors, products, and employees.

---

## 🔑 Top 10 Key Insights

### Insight 1 — [Short Descriptive Title e.g. "Revenue Concentration in North B"]

**Observation:** One concrete, data-backed sentence (include exact Rs. figures).
A second sentence may elaborate if needed (max 3 sentences total).

> **▶ Recommendation:** Actionable next step in one sentence.

---

### Insight 2 — [Short Descriptive Title]

**Observation:** …

> **▶ Recommendation:** …

---

*(repeat this exact pattern for insights 3 through 10)*

---

## 📝 Executive Summary

Three to five sentences summarising the overall health of the business as
reflected in this data, referencing the most critical findings above.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INSIGHT DIVERSITY RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cover a DIVERSE set of angles — do NOT repeat the same theme across insights.
Suggested angles (adapt to what is present in data):
  • Top / Bottom performers (product, distributor, employee, region)
  • Revenue concentration / Pareto observations
  • Volume vs. revenue mismatches
  • Discount patterns and split patterns
  • Visit efficiency (revenue per visit, drop-size trends)
  • Geographic / territorial distribution of sales
  • Product-mix or brand-mix observations
  • Employee productivity comparisons
  • Pricing anomalies (ex-factory vs. distributor vs. TP gap)
  • Risk / opportunity flags (zero-revenue SKUs, unusually high/low lppc)

Cite actual values from the data in every insight.
Never use markdown tables or code blocks.
""").strip()

# ==================== DATA ANALYTICS HELPERS ====================
def _wrap_labels(labels: list[str], width: int = 18) -> list[str]:
    return ["\n".join(textwrap.wrap(str(l), width)) for l in labels]

def _save(fig: plt.Figure, name: str) -> Path:
    path = GRAPHS_DIR / name
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    return path

def _top_n(records: list[dict], group_by: str, value_field: str,
           n: int = 10) -> tuple[list[str], list[float]]:
    agg: dict[str, float] = defaultdict(float)
    for rec in records:
        key = str(rec.get(group_by) or "Unknown")
        try:
            agg[key] += float(rec.get(value_field) or 0)
        except (TypeError, ValueError):
            pass
    top = sorted(agg.items(), key=lambda x: x[1], reverse=True)[:n]
    labels, values = zip(*top) if top else ([], [])
    return list(labels), list(values)

def generate_graphs(records: list[dict]) -> list[str]:
    saved: list[str] = []
    PALETTE = plt.cm.tab10.colors

    # 1. Revenue by Region
    labels, values = _top_n(records, "regionname", "total_after_tax")
    if labels:
        fig, ax = plt.subplots(figsize=(10, 5))
        bars = ax.barh(_wrap_labels(labels), values, color=PALETTE[:len(labels)])
        ax.set_xlabel("Total Revenue (after discount)")
        ax.set_title("Revenue by Region")
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
        ax.invert_yaxis()
        fig.tight_layout()
        saved.append(str(_save(fig, "01_revenue_by_region.png").name))

    # 2. Top Distributors
    labels, values = _top_n(records, "distributorname", "total_after_tax")
    if labels:
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.bar(_wrap_labels(labels, 14), values, color=PALETTE[:len(labels)])
        ax.set_ylabel("Revenue")
        ax.set_title("Top Distributors by Revenue")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
        ax.tick_params(axis="x", labelsize=8)
        fig.tight_layout()
        saved.append(str(_save(fig, "02_top_distributors_revenue.png").name))

    # 3. Volume by Category
    labels, values = _top_n(records, "productcategoryname", "sumqty")
    if labels:
        fig, ax = plt.subplots(figsize=(7, 7))
        ax.pie(values, labels=_wrap_labels(labels, 15), autopct="%1.1f%%", startangle=140, colors=PALETTE[:len(labels)])
        ax.set_title("Sales Volume by Product Category")
        fig.tight_layout()
        saved.append(str(_save(fig, "03_volume_by_category.png").name))

    # 4. Top SKUs
    labels, values = _top_n(records, "itemname", "sumqty")
    if labels:
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.bar(_wrap_labels(labels, 14), values, color=PALETTE[:len(labels)])
        ax.set_ylabel("Quantity Sold")
        ax.set_title("Top SKUs by Quantity Sold")
        ax.tick_params(axis="x", labelsize=7)
        fig.tight_layout()
        saved.append(str(_save(fig, "04_top_skus_quantity.png").name))

    # 5. Revenue by Brand
    labels, values = _top_n(records, "brandname", "total_after_tax")
    if labels:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.barh(_wrap_labels(labels), values, color=PALETTE[:len(labels)])
        ax.set_xlabel("Revenue")
        ax.set_title("Revenue Contribution by Brand")
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
        ax.invert_yaxis()
        fig.tight_layout()
        saved.append(str(_save(fig, "05_revenue_by_brand.png").name))

    # 6. Employee RPV
    emp_rev: dict[str, float] = defaultdict(float)
    emp_visits: dict[str, float] = defaultdict(float)
    for rec in records:
        name = str(rec.get("emp_name") or "Unknown")
        try:
            emp_rev[name]    += float(rec.get("total_after_tax") or 0)
            emp_visits[name] += float(rec.get("unique_visits")   or 0)
        except (TypeError, ValueError):
            pass
    emp_rpv = {k: emp_rev[k] / max(emp_visits[k], 1) for k in emp_rev}
    top_emp = sorted(emp_rpv.items(), key=lambda x: x[1], reverse=True)[:10]
    if top_emp:
        e_labels, e_vals = zip(*top_emp)
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.bar(_wrap_labels(list(e_labels), 14), e_vals, color=PALETTE[:len(e_labels)])
        ax.set_ylabel("Revenue per Visit")
        ax.set_title("Top Employees – Revenue per Visit")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
        ax.tick_params(axis="x", labelsize=8)
        fig.tight_layout()
        saved.append(str(_save(fig, "06_employee_revenue_per_visit.png").name))

    # 7. Revenue by Territory
    labels, values = _top_n(records, "territoryname", "total_after_tax")
    if labels:
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.bar(_wrap_labels(labels, 14), values, color=PALETTE[:len(labels)])
        ax.set_ylabel("Revenue")
        ax.set_title("Revenue by Territory (Top 10)")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
        ax.tick_params(axis="x", labelsize=8)
        fig.tight_layout()
        saved.append(str(_save(fig, "07_revenue_by_territory.png").name))

    # 8. Pricing Gap
    items: dict[str, dict[str, float]] = defaultdict(lambda: {"ex": 0.0, "dist": 0.0, "tp": 0.0})
    for rec in records:
        sku = str(rec.get("itemname") or rec.get("sku_code") or "Unknown")
        try:
            items[sku]["ex"]   += float(rec.get("ex_factory_price") or 0)
            items[sku]["dist"] += float(rec.get("distributor_incl")  or 0)
            items[sku]["tp"]   += float(rec.get("total_tp_incl")     or 0)
        except (TypeError, ValueError):
            pass
    top_items = sorted(items.items(), key=lambda x: x[1]["tp"], reverse=True)[:10]
    if top_items:
        i_labels  = [i[0] for i in top_items]
        i_ex      = [i[1]["ex"]   for i in top_items]
        i_dist    = [i[1]["dist"] for i in top_items]
        i_tp      = [i[1]["tp"]   for i in top_items]
        x         = np.arange(len(i_labels))
        width     = 0.28
        fig, ax   = plt.subplots(figsize=(14, 6))
        ax.bar(x - width, i_ex,   width, label="Ex-Factory",   color="#4C72B0")
        ax.bar(x,          i_dist, width, label="Distributor Incl.", color="#DD8452")
        ax.bar(x + width, i_tp,   width, label="Trade Price Incl.", color="#55A868")
        ax.set_xticks(x)
        ax.set_xticklabels(_wrap_labels(i_labels, 12), fontsize=7)
        ax.set_ylabel("Value")
        ax.set_title("Pricing Gap: Ex-Factory vs Distributor vs Trade Price (Top 10 Items)")
        ax.legend()
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
        fig.tight_layout()
        saved.append(str(_save(fig, "08_pricing_gap_analysis.png").name))

    # 9. Dist Type
    labels, values = _top_n(records, "distributor_type", "total_after_tax", n=len(records))
    if labels:
        fig, ax = plt.subplots(figsize=(7, 7))
        ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90, colors=PALETTE[:len(labels)])
        ax.set_title("Revenue Share by Distributor Type")
        fig.tight_layout()
        saved.append(str(_save(fig, "09_distributor_type_revenue_share.png").name))

    # 10. Revenue vs Qty
    dist_rev: dict[str, float] = defaultdict(float)
    dist_qty: dict[str, float] = defaultdict(float)
    for rec in records:
        key = str(rec.get("distributorname") or "Unknown")
        try:
            dist_rev[key] += float(rec.get("total_after_tax") or 0)
            dist_qty[key] += float(rec.get("sumqty")          or 0)
        except (TypeError, ValueError):
            pass
    if dist_rev:
        d_names = list(dist_rev.keys())
        d_rev   = [dist_rev[k] for k in d_names]
        d_qty   = [dist_qty[k] for k in d_names]
        fig, ax = plt.subplots(figsize=(10, 6))
        sc = ax.scatter(d_qty, d_rev, alpha=0.7, c=range(len(d_names)), cmap="tab20", edgecolors="white", s=80)
        ax.set_xlabel("Total Quantity Sold")
        ax.set_ylabel("Total Revenue")
        ax.set_title("Revenue vs Quantity Sold – by Distributor")
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
        top5_idx = sorted(range(len(d_rev)), key=lambda i: d_rev[i])[-5:]
        for i in top5_idx:
            ax.annotate("\n".join(textwrap.wrap(d_names[i], 14)), (d_qty[i], d_rev[i]),
                        textcoords="offset points", xytext=(6, 4), fontsize=6, ha="left")
        fig.tight_layout()
        saved.append(str(_save(fig, "10_revenue_vs_quantity_scatter.png").name))

    return saved

def build_data_summary(records: list[dict]) -> str:
    total   = len(records)
    numeric_fields = ["sumqty", "beforediscount", "total_after_tax", "total_tp_incl",
                      "ex_factory_price", "distributor_incl", "total_discount_value",
                      "total_tax_charged", "cnt_items", "total_visits", "unique_visits",
                      "lppc", "qtyCTN"]
    aggregates: dict[str, float] = defaultdict(float)
    for rec in records:
        for f in numeric_fields:
            try:
                aggregates[f] += float(rec.get(f) or 0)
            except (TypeError, ValueError):
                pass
    def uniq(field):
        return list({str(r.get(field, "")) for r in records if r.get(field)})
    summary = {
        "metadata": {
            "total_records_in_file": total,
            "records_analysed":      len(records),
            "date_range": {
                "start": records[0].get("startdate") if records else None,
                "end":   records[0].get("enddate") if records else None,
            },
        },
        "dimensions": {
            "regions":            uniq("regionname"),
            "regional_distributors": uniq("regionaldistributor"),
            "territories":        uniq("territoryname"),
            "distributor_types":  uniq("distributor_type"),
            "distributors":       uniq("distributorname"),
            "brands":             uniq("brandname"),
            "product_categories": uniq("productcategoryname"),
            "products":           uniq("productname"),
            "employee_types":     uniq("emptype"),
            "employees":          uniq("emp_name"),
        },
        "totals": {k: round(v, 2) for k, v in aggregates.items()},
        "sample_records": records[:30],
    }
    return json.dumps(summary, indent=2, ensure_ascii=False)

load_dotenv()
MODEL = os.getenv("OPENAI_MODEL")

# ==================== STATE DEFINITION ====================
class AgentState(TypedDict):
    """Enhanced state for LangGraph"""
    user_query: str
    llm_intent: str
    confidence: float
    detected_language: str
    is_confused: bool
    requires_clarification: bool
    step_to_clarify: Optional[int]
    response: Dict[str, Any]
    conversation_history: Annotated[List[str], "append"]
    last_tutorial: List[Dict[str, Any]]
    suggestions: List[str]
    next_node: str
    processing_path: List[str]
    validation_results: Dict[str, Any]
    sql_query: Optional[str]
    sql_result: Optional[Any]

# ==================== LLM-BASED TOOLS ====================
class RequestAnalyzer:
    """Combined Intent and Language Analyzer to reduce latency"""
    
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.0, model=MODEL)
        
    def analyze(self, user_query: str, conversation_history: List[str]) -> Dict[str, Any]:
        """Analyze intent and language in a single pass"""
        
        history_context = ""
        if conversation_history:
            history_context = "\nRecent conversation:\n" + "\n".join(conversation_history[-3:])
        
        system_prompt = """You are the 'Request Analyzer' for Luma, a Management Portal assistant.
Analyze the user query to determine the primary intent.

Available Intents:
- "tutorial": Use this for ANY request asking for STEPS, instructions, or "HOW TO" perform an action (e.g., "How to add a region", "Process for creating a bank", "View details of User"). If the user is asking how to navigate or perform a feature, it's a tutorial.
- "capabilities": ONLY use this when the user asks about Luma herself (e.g., "What can you do?", "Who are you?", "System features"). 
- "general": Greetings, chit-chat, or simple conversational emotional markers.
- "clarify": User explicitly asks for an explanation of a specific step or says "Help me with step X".
- "history_recall": User asks about previous questions or answers (e.g., "What was my last question?", "What did you say about Bank?").
- "summarization": User asks for a summary of the whole chat (e.g., "Summarize our chat," "What is the conversation that I did to you?").
- "sql_query": Use this when the user is looking for SPECIFIC RECORDS, LISTS of data, or status of actual items in the database (e.g., "List of distributors", "Distributors in Karachi", "Which employees are permanent?"). 
- "data_analysis": Use this when the user asks to analyse sales data, generate a report, get key insights from data, or view business analytics (e.g. "Analyse the sales data", "Give me top insights", "Generate report").
- "fallback": Unclear or completely out-of-scope queries.

CRITICAL DISTINCTION:
1. Procedural Query (Tutorial): "View details of User", "How to view details", "Steps to create agent".
2. Data Query (SQL): "Details of distributor Al-Talha", "Show me permanent employees", " Islamabad distributors".

Return JSON format:
{
    "intent": "tutorial",
    "confidence": 0.9,
    "language": "English", 
    "is_confused": false,
    "step_number": null,
    "original_query": "user query here"
}

Language Detection Rules:
- If user uses Roman Urdu words (e.g., 'kaisay', 'kahan', 'madad'), classify as "Roman-Urdu".
- If user uses Urdu script, classify as "Urdu".
- If user uses any OTHER language (e.g., Spanish, French), classify as "English" (so we can politely refuse in English).
- Default to "English".
"""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"{history_context}\n\nUser Query: {user_query}")
            ]
            
            response = self.llm.invoke(messages)
            result = json.loads(response.content.strip())
            
            # Normalize Intent
            valid_intents = ["general", "tutorial", "capabilities", "clarify", "history_recall", "summarization", "sql_query", "data_analysis", "fallback"]
            result["intent"] = result.get("intent", "fallback").lower()
            if result["intent"] not in valid_intents:
                result["intent"] = "fallback"
            
            # Normalize Confidence
            result["confidence"] = max(0.0, min(1.0, result.get("confidence", 0.5)))
            
            # Normalize Language
            raw_lang = result.get("language", "english").lower()
            if any(variant in raw_lang for variant in ["hindi", "urdu", "roman", "hinglish"]):
                result["language"] = "Roman-Urdu"
            else:
                result["language"] = "English"
                
            result["is_confused"] = bool(result.get("is_confused", False))
            result["step_number"] = result.get("step_number")
            
            return result
            
        except Exception as e:
            # Fallback safe response
            return {
                "intent": "fallback",
                "confidence": 0.3,
                "language": "English",
                "is_confused": False,
                "step_number": None
            }


class KnowledgeBase:
    """Loads and caches available tutorial topics from the documents directory"""
    
    def __init__(self, doc_dir: str = "documents"):
        self.doc_dir = doc_dir
        self.capabilities: Dict[str, List[str]] = {
            "english": [],
            "roman-urdu": []
        }
        self.refresh()

    def refresh(self):
        """Re-scan documents and refresh cached topics"""
        self.capabilities["english"] = []
        self.capabilities["roman-urdu"] = []
        self._load_knowledge()

    def _load_knowledge(self):
        """Extract unique section titles from ChromaDB metadata as the single source of truth"""
        try:
            # Connect to vector store to get current indexed topics
            embeddings = OpenAIEmbeddings(model=os.getenv("EMBEDDING_MODEL"))
            vectordb = Chroma(
                persist_directory=os.getenv("CHROMA_PERSIST_DIR"), 
                embedding_function=embeddings
            )
            
            # Fetch all metadata currently in Luma's memory
            data = vectordb.get(include=['metadatas'])
            metadatas = data.get('metadatas', [])
            
            for meta in metadatas:
                title = meta.get("section_title")
                lang_code = meta.get("language", "").lower()
                
                # Normalize language key
                base_lang = "english"
                if "roman" in lang_code or "ur" in lang_code:
                    base_lang = "roman-urdu"
                    
                if title and title not in self.capabilities[base_lang]:
                    self.capabilities[base_lang].append(title)
                    
        except Exception as e:
            # Silently handle empty DB during first run
            pass

    def get_topics(self, language: str) -> List[str]:
        """Get topics for a language"""
        lang_key = "roman-urdu" if "roman" in language.lower() or "urdu" in language.lower() else "english"
        return self.capabilities.get(lang_key, [])


class DynamicSuggestionGenerator:
    """Dynamic suggestion generation"""
    
    def __init__(self, knowledge_base: KnowledgeBase = None):
        self.llm = ChatOpenAI(temperature=0.3, model=MODEL)
        self.kb = knowledge_base or KnowledgeBase()
    
    def generate(self, user_query: str, intent: str, conversation_history: List[str], language: str = "English") -> List[str]:
        """Generate context-aware suggestions"""
        
        history_context = "\n".join(conversation_history[-4:]) if conversation_history else "No recent history"
        
        # Determine strict language instruction
        lang_instruction = f"Strictly generate suggestions in {language}."
        input_lang = language.lower().replace(" ", "-")
        if input_lang in ["roman-urdu", "urdu"]:
            lang_instruction = "Strictly generate suggestions in Roman Urdu (Urdu written in English alphabets)."

        # Get grounded topics
        available_topics = self.kb.get_topics(language)
        topics_str = ", ".join(available_topics[:15]) # Limit to 15 topics for prompt brevity

        # Custom instruction for fallback
        if intent == "fallback":
            query_context = "Ignore the user query as it was out of scope. Suggest 4 diverse, valid actions based on the available topics."
        else:
            query_context = f"User Query: {user_query}"

        system_prompt = f"""Generate 4 relevant follow-up questions for Luma, a Management Portal assistant.
{lang_instruction}

CRITICAL: Only suggest actions that Luma can actually do. 
Available topics Luma can help with: [{topics_str}]

Guidelines:
1. Every suggestion MUST directly relate to the available topics listed above.
2. If Intent is 'fallback', DO NOT hallucinate based on the user's invalid query. Suggest broad, valid system actions instead.
3. If the user query is about a specific valid topic (e.g., 'Region'), suggest sub-tasks like 'View details of Region'.
4. Do NOT hallucinate features Luma doesn't have.

{query_context}
Intent: {intent}
Recent History: {history_context}

Return ONLY a JSON array of strings: ["Suggestion 1", "Suggestion 2", ...]"""
        
        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content="Generate suggestions")
            ])
            
            content = response.content.strip()
            
            # Use regex to find the JSON array in case there's conversational filler
            match = re.search(r"(\[.*\])", content, re.DOTALL)
            if match:
                suggestions = json.loads(match.group(1))
            else:
                # Direct attempt if regex fails
                suggestions = json.loads(content)
                
            if isinstance(suggestions, list) and len(suggestions) > 0:
                return suggestions
            else:
                raise Exception("Empty suggestions list")
            
        except Exception:
            input_lang = language.lower().replace(" ", "-")
            if input_lang in ["roman-urdu", "urdu"]:
                return [
                    "Naya region kaisay add karain?",
                    "Distributor bananay ke steps kya hain?",
                    "Aap mairi kaisay madad kar saktay hain?"
                ]
            return [
                "How to add a new region?",
                "Steps to create a distributor",
                "What can you help me with?"
            ]


class GreetingGenerator:
    """Personalizes the introduction for tutorial steps"""
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.3, model=MODEL)

    def generate(self, user_query: str, section_title: str, language: str = "English") -> str:
        """Generate a personalized greeting"""
        system_prompt = f"""You are 'Luma', the portal assistant. 
Create a ONE-LINE, natural greeting to introduce a list of tutorial steps.
The greeting should bridge the user's question and the topic, using the USER'S terminology where appropriate.

User's Question: {user_query}
Retrieved Topic: {section_title}
Language: {language}

CRITICAL:
- If Language is "English", the greeting MUST be in English.
- If Language is "Roman Urdu", the greeting MUST be in Roman Urdu.
- Do NOT output in Spanish, French, or any other language, even if the user input is in that language.

Examples:
Input: "where is the agents page?"
Topic: "Where is Agent page located"
Response: "Here are the steps to find the agents page:"

Input: "create new stuff"
Topic: "Add New Item"
Response: "Here are the steps to create new stuff:"

Input: "bank kahan hai?"
Topic: "Where is Bank page located"
Response: "Bank page kahan hai, iske baray mein steps yeh hain:"

Rules:
- Keep it to a single line.
- End with a colon (:).
- Be polite and direct.
- Mirror the user's keywords/terminology if safe to do so.
"""
        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"User's Question: {user_query}")
            ])
            return response.content.strip()
        except Exception:
            # Fallback to generic if LLM fails
            if language.lower() in ["urdu", "roman-urdu"]:
                return "Yeh rahe steps:"
            return "Here are the steps:"


# ==================== LANGGRAPH NODES ====================
class AgentNodes:
    """Collection of LangGraph nodes"""
    
    def __init__(self):
        self.refresh()
    
    def refresh(self):
        """Re-initialize all internal components with fresh retrieval indices."""
        from chat import get_components
        self.knowledge_base = KnowledgeBase()
        self.request_analyzer = RequestAnalyzer()
        self.suggestion_generator = DynamicSuggestionGenerator(self.knowledge_base)
        self.greeting_generator = GreetingGenerator()
        self.general_llm = ChatOpenAI(temperature=0.9, model=MODEL)
        self.tutorial_llm = ChatOpenAI(temperature=0.0, model=MODEL)
        
        # Share the same vectordb from chat.py to save resources
        components = get_components()
        self.vectordb = components.get("vectordb")
        self.mysql_service = MySQLService()
    
    def analyze_request(self, state: AgentState) -> AgentState:
        """Analyze intent and language in one step"""
        analysis_result = self.request_analyzer.analyze(
            state["user_query"], 
            state["conversation_history"]
        )
        
        state["llm_intent"] = analysis_result["intent"]
        state["confidence"] = analysis_result["confidence"]
        state["detected_language"] = analysis_result["language"]
        state["is_confused"] = analysis_result["is_confused"]
        state["step_to_clarify"] = analysis_result["step_number"]
        state["requires_clarification"] = analysis_result["intent"] == "clarify" and not analysis_result["step_number"]
        
        # Store validation results as well for backward compatibility
        state["validation_results"]["language_analysis"] = {
            "language": analysis_result["language"],
            "has_emotional_content": False
        }
        
        state["processing_path"].append("analyze_request")
        return state
    
    def route_decision(self, state: AgentState) -> AgentState:
        """Decide which agent to route to"""
        intent = state["llm_intent"]
        confidence = state.get("confidence", 0.5)
        
        # Determine next node
        if confidence < 0.4:
            state["next_node"] = "fallback_agent"
        else:
            route_map = {
                "general": "general_agent",
                "tutorial": "tutorial_agent",
                "capabilities": "capabilities_agent",
                "clarify": "clarification_agent",
                "history_recall": "history_summary_agent",
                "summarization": "history_summary_agent",
                "sql_query": "sql_query_generator",
                "data_analysis": "data_analysis_agent",
                "fallback": "fallback_agent",
            }
            state["next_node"] = route_map.get(intent, "fallback_agent")
        
        state["processing_path"].append("route_decision")
        return state
    
    def general_agent(self, state: AgentState) -> AgentState:
        """Handle general conversations"""
        lang_info = state["validation_results"].get("language_analysis", {})
        is_urdu = lang_info.get("language", "").lower() in ["urdu", "roman-urdu"]
        
        if is_urdu:
            system_prompt = "You are Luma, a Roman-Urdu Management Portal assistant. You must STRICTLY answer only in Roman Urdu. Do not use English script or any other language."
        else:
            system_prompt = "You are Luma, a Management Portal assistant. You must STRICTLY answer only in English. If the user speaks a different language (e.g., Spanish, French, Arabic), politely reply in English stating that you only support English and Roman Urdu."
        
        # Parallelize General LLM response and Suggestion Generation
        with ThreadPoolExecutor() as executor:
            future_content = executor.submit(
                self._generate_general_response, 
                system_prompt, 
                state["conversation_history"], 
                state["user_query"],
                is_urdu
            )
            future_suggestions = executor.submit(
                self.suggestion_generator.generate,
                state["user_query"],
                "general",
                state["conversation_history"],
                "Roman Urdu" if is_urdu else "English"
            )
            
            content = future_content.result()
            suggestions = future_suggestions.result()
        
        state["response"] = {
            "type": "general",
            "content": content,
            "suggested_actions": suggestions,
            "is_urdu": is_urdu
        }
        
        state["suggestions"] = suggestions
        state["processing_path"].append("general_agent")
        return state

    def _generate_general_response(self, system_prompt, history, query, is_urdu):
        try:
            messages = [SystemMessage(content=system_prompt)]
            for msg in history[-4:]:
                messages.append(HumanMessage(content=msg))
            messages.append(HumanMessage(content=query))
            
            response = self.general_llm.invoke(messages)
            return response.content
        except Exception:
            return "Hello! How can I help you?" if not is_urdu else "Hi! Main aapki kaisay madad kar sakti hoon."
    
    def capabilities_agent(self, state: AgentState) -> AgentState:
        """Explain system capabilities in a layman-friendly, rich way"""
        lang_info = state["validation_results"].get("language_analysis", {})
        is_urdu = lang_info.get("language", "").lower() in ["urdu", "roman-urdu"]
        
        if is_urdu:
            title = "Hi! Main hoon Luma"
            subtitle = "Main aapki Management Portal ka har kaam asaan bananay mein madad kar sakti hoon."
            
            features = [
                {
                    "title": "Aam Sawalaat",
                    "description": "Greetings ho ya aam guftagu, main hamesha hazir hoon.",
                    "icon": "👋"
                },
                {
                    "title": "Step-by-Step Tutorials",
                    "description": "Add Region ho ya Distributor setup, har kaam ki tasweeri tutorial mujh se lain.",
                    "icon": "📸"
                },
                {
                    "title": "Easy Explaination",
                    "description": "Agar koi step mushkil lagay, bas mujh se poochain aur main usay asaan alfaz mein bataungi.",
                    "icon": "💡"
                },
                {
                    "title": "Portal Ki Maloomat",
                    "description": "Kaunsi cheez kahan hai? Main portal ke har kone se waqif hoon.",
                    "icon": "🗺️"
                },
                {
                    "title": "Urdu aur English",
                    "description": "Main aap se English aur Roman-Urdu dono mein baat kar sakti hoon.",
                    "icon": "🗣️"
                }
            ]
            cta = "Aap kya seekhna chahte hain?"
        else:
            title = "I'm Luma, Your Portal Guide"
            subtitle = "I'm here to make managing your portal as simple as having a conversation."
            
            features = [
                {
                    "title": "General Assistance",
                    "description": "From a friendly greeting to general questions, I'm always ready to chat.",
                    "icon": "👋"
                },
                {
                    "title": "Visual Walkthroughs",
                    "description": "Need to add a Region or set up a Distributor? I'll show you exactly how with pictures.",
                    "icon": "📸"
                },
                {
                    "title": "Crystal Clear Clarity",
                    "description": "Confused about a step? Just ask! I'll break it down into even simpler English for you.",
                    "icon": "💡"
                },
                {
                    "title": "Portal Navigation",
                    "description": "I know where every page is located. Just ask me where to find something.",
                    "icon": "🗺️"
                },
                {
                    "title": "Bilingual Support",
                    "description": "Whether you prefer English or Roman-Urdu, I've got you covered.",
                    "icon": "🗣️"
                }
            ]
            cta = "What would you like to learn today?"
        
        suggestions = self.suggestion_generator.generate(
            state["user_query"],
            "capabilities",
            state["conversation_history"],
            language="Roman Urdu" if is_urdu else "English"
        )
        
        state["response"] = {
            "type": "capabilities",
            "title": title,
            "content": subtitle,
            "features": features,
            "footer_cta": cta,
            "suggested_actions": suggestions,
            "is_urdu": is_urdu
        }
        
        state["suggestions"] = suggestions
        state["processing_path"].append("capabilities_agent")
        return state
    
    def tutorial_agent(self, state: AgentState) -> AgentState:
        """Handle tutorial requests"""
        if state["step_to_clarify"]:
            return self._handle_step_clarification(state)
        
        try:
            bot_response = get_bot_response(state["user_query"])
            
            if bot_response.get("type") == "tutorial" and bot_response.get("steps"):
                steps = bot_response["steps"]
                formatted_steps = []
                
                for i, s in enumerate(steps, 1):
                    formatted_steps.append({
                        "step_number": i,
                        "text": s.get("text", s.get("description", "")),
                        "image": s.get("image") or s.get("snapshot")
                    })
                
                
                # Removed redundant LLM summary generation to improve latency
                # summary = self._generate_step_summary(...)
                # Instead, we use static introductions based on language
                
                lang_info = state["validation_results"].get("language_analysis", {})
                is_urdu = lang_info.get("language", "").lower() in ["urdu", "roman-urdu"]
                
                # Dynamic Personalized Greeting and Suggestions in Parallel
                section_title = bot_response.get("section_title", "")
                
                with ThreadPoolExecutor() as executor:
                    future_intro = executor.submit(
                        self.greeting_generator.generate,
                        state["user_query"], 
                        section_title, 
                        "Roman Urdu" if is_urdu else "English"
                    )
                    future_suggestions = executor.submit(
                        self.suggestion_generator.generate,
                        state["user_query"],
                        "tutorial",
                        state["conversation_history"],
                        "Roman Urdu" if is_urdu else "English"
                    )
                    
                    intro = future_intro.result()
                    suggestions = future_suggestions.result()
                
                if is_urdu:
                    summary = f"Main pur-umeed hoon ke in {len(formatted_steps)} steps se aapki madad hui hogi."
                    pro_tip = "Steps ko carefully follow karain."
                    outro = "Shukriya!"
                else:
                    summary = f"I hope these {len(formatted_steps)} steps help you achieve your goal."
                    pro_tip = "Follow each step carefully."
                    outro = "Thank you!"
                
                state["response"] = {
                    "type": "tutorial",
                    "content": intro,
                    "steps": formatted_steps,
                    "summary": summary,
                    "pro_tip": pro_tip,
                    "completion_message": outro,
                    "is_urdu": is_urdu,
                    "suggested_actions": suggestions
                }
                
            elif bot_response.get("type") == "no_relevant_content":
                lang_info = state["validation_results"].get("language_analysis", {})
                is_urdu = lang_info.get("language", "").lower() in ["urdu", "roman-urdu"]
                suggestions = self.suggestion_generator.generate(
                    state["user_query"],
                    "fallback", # Use fallback intent to trigger safer suggestions
                    state["conversation_history"],
                    language="Roman Urdu" if is_urdu else "English"
                )
                
                state["response"] = {
                    "type": "no_relevant_content", # Pass this type through to frontend
                    "content": f"It looks like the topic **'{state['user_query']}'** is not related to this system. If you have a general question, feel free to ask! However, I cannot provide a tutorial for this specific topic as it is not part of the system documentation.",
                    "suggested_actions": suggestions
                }

            else:
                lang_info = state["validation_results"].get("language_analysis", {})
                is_urdu = lang_info.get("language", "").lower() in ["urdu", "roman-urdu"]
                suggestions = self.suggestion_generator.generate(
                    state["user_query"],
                    "tutorial",
                    state["conversation_history"],
                    language="Roman Urdu" if is_urdu else "English"
                )
                
                state["response"] = {
                    "type": "tutorial_fallback",
                    "content": f"No steps found for '{state['user_query']}'.",
                    "suggestions": suggestions
                }
                
        except Exception:
            lang_info = state["validation_results"].get("language_analysis", {})
            is_urdu = lang_info.get("language", "").lower() in ["urdu", "roman-urdu"]
            suggestions = self.suggestion_generator.generate(
                state["user_query"],
                "tutorial",
                state["conversation_history"],
                language="Roman Urdu" if is_urdu else "English"
            )
            
            state["response"] = {
                "type": "error",
                "content": "Error retrieving tutorial.",
                "suggestions": suggestions
            }
        
        state["suggestions"] = suggestions
        state["processing_path"].append("tutorial_agent")
        return state
    
    def _handle_step_clarification(self, state: AgentState) -> AgentState:
        """Handle step clarification"""
        step_idx = state["step_to_clarify"]
        last_tutorial = state.get("last_tutorial", [])
        
        if last_tutorial and 1 <= step_idx <= len(last_tutorial):
            step = last_tutorial[step_idx - 1]
            original_text = step.get("text") or step.get("description", "")
            
            clarified_text = self._clarify_single_step(
                original_text, 
                step_idx,
                state["detected_language"]
            )
            
            lang_info = state["validation_results"].get("language_analysis", {})
            is_urdu = lang_info.get("language", "").lower() in ["urdu", "roman-urdu"]
            suggestions = self.suggestion_generator.generate(
                state["user_query"],
                "clarify",
                state["conversation_history"],
                language="Roman Urdu" if is_urdu else "English"
            )
            
            state["response"] = {
                "type": "tutorial_clarify",
                "content": f"Step {step_idx} clarification:",
                "clarified_step": {
                    "step_number": step_idx,
                    "original": original_text,
                    "clarified": clarified_text,
                    "image": step.get("image") or step.get("snapshot")
                },
                "suggested_actions": suggestions,
                "is_urdu": state["detected_language"] in ["urdu", "roman-urdu"]
            }
            
        else:
            lang_info = state["validation_results"].get("language_analysis", {})
            is_urdu = lang_info.get("language", "").lower() in ["urdu", "roman-urdu"]
            suggestions = self.suggestion_generator.generate(
                state["user_query"],
                "clarify",
                state["conversation_history"],
                language="Roman Urdu" if is_urdu else "English"
            )
            
            state["response"] = {
                "type": "tutorial_clarify_error",
                "content": "Please ask for a tutorial first.",
                "suggested_actions": suggestions
            }
        
        state["suggestions"] = suggestions
        return state
    
    def _clarify_single_step(self, step_text: str, step_number: int, language: str) -> str:
        """Clarify a single step"""
        is_urdu = language in ["urdu", "roman-urdu"]
        
        if is_urdu:
            system_prompt = "Explain this step in clearer Roman-Urdu."
        else:
            system_prompt = "Explain this step more clearly."
        
        try:
            response = self.tutorial_llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Step {step_number}: {step_text}")
            ])
            return response.content.strip()
        except Exception:
            return step_text
    

    
    def clarification_agent(self, state: AgentState) -> AgentState:
        """Handle clarification requests"""
        if state["requires_clarification"]:
            lang_info = state["validation_results"].get("language_analysis", {})
            is_urdu = lang_info.get("language", "").lower() in ["urdu", "roman-urdu"]
            
            suggestions = self.suggestion_generator.generate(
                state["user_query"],
                "clarify",
                state["conversation_history"],
                language="Roman Urdu" if is_urdu else "English"
            )
            
            state["response"] = {
                "type": "clarify_question",
                "content": "Which step would you like me to explain?",
                "suggested_actions": suggestions
            }
        else:
            return self.tutorial_agent(state)
        
        state["suggestions"] = suggestions
        state["processing_path"].append("clarification_agent")
        return state
    
    def history_summary_agent(self, state: AgentState) -> AgentState:
        """Handle conversation history recall and summarization"""
        intent = state["llm_intent"]
        history = state.get("conversation_history", [])
        is_urdu = state["detected_language"] in ["urdu", "roman-urdu"]
        
        if not history:
            state["response"] = {
                "type": "general",
                "content": "Hamari abhi koi baat nahi hui." if is_urdu else "We haven't had much of a conversation yet!"
            }
            return state

        if intent == "summarization":
            # Summarize the conversation
            system_prompt = f"""Summarize the following chat conversation between a user and Luma (Management Portal Assistant).
Provide a high-level summary of what was discussed, the topics covered, and any pending questions.
Language: {'Roman-Urdu' if is_urdu else 'English'}
Format: Bullet points.
"""
            history_text = "\n".join(history)
            try:
                response = self.general_llm.invoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=f"Conversation History:\n{history_text}")
                ])
                summary_content = response.content
            except Exception:
                summary_content = "Summary generation failed."
            
            state["response"] = {
                "type": "summarization",
                "content": summary_content,
                "is_urdu": is_urdu
            }
        
        elif intent == "history_recall":
            # Recall specific parts of the history
            history_text = "\n".join(history[-10:])
            system_prompt = f"""The user is asking a question about the previous conversation.
Based on the provided history, answer the user's question accurately.
If they ask for their 'last question', identify it from the history.
If they ask 'what did you say about X', find the relevant assistant response.
Language: {'Roman-Urdu' if is_urdu else 'English'}
History:
{history_text}
"""
            try:
                response = self.general_llm.invoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=f"User's Recall Question: {state['user_query']}")
                ])
                recall_content = response.content
            except Exception:
                recall_content = "I'm sorry, I couldn't recall that correctly."
            
            state["response"] = {
                "type": "history_recall",
                "content": recall_content,
                "is_urdu": is_urdu
            }

        state["processing_path"].append("history_summary_agent")
        return state

    def sql_query_generator(self, state: AgentState) -> AgentState:
        """Generate a MySQL query based on user query and multiple schemas"""
        schema_dir = "skills"
        all_schemas = []
        try:
            for filename in os.listdir(schema_dir):
                if filename.endswith(".md"):
                    with open(os.path.join(schema_dir, filename), "r") as f:
                        all_schemas.append(f"--- SCHEMA: {filename} ---\n{f.read()}")
            schema_content = "\n\n".join(all_schemas)
        except Exception as e:
            print(f"Error loading schemas: {e}")
            schema_content = "Schema information not fully available."

        system_prompt = f"""You are a MySQL Query Expert for Luma. 
Your task is to convert the user's question into a valid, safe, and efficient MySQL query.

DATABASE SCHEMAS:
{schema_content}

CRITICAL KNOWLEDGE:
1. Broad Schema Support: You have 6 schemas (Customer, Discount, Distributor, Employee, PJP, and Product).
2. Distributor Denormalization: The `distributor` table has `region_name`, `territory_name`, and `regional_distributor_name` stored directly. For location queries (e.g. "Distributors in Karachi"), check THESE fields first using LIKE.
3. Employee Status: Check `emptype` for employment status (e.g. 'Permanent', 'Full-time').
4. Joins: If a query needs data not in the primary table, perform standard JOINs (e.g. `employee` JOIN `territory` on `employee.territory_id = territory.uid`).

RULES:
1. ONLY return the bare SQL query. No markdown, no backticks, no introduction.
2. Always use `LIKE '%term%'` for name or location searches to be flexible.
3. For dates, use 'YYYY-MM-DD'.
4. If unsure, return an empty string.

QUERY OBJECTIVE: Generate a query that answers: "{state["user_query"]}"
"""
        try:
            response = self.tutorial_llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=state["user_query"])
            ])
            # Extra safety: strip any markdown code blocks
            res_content = response.content.strip()
            res_content = re.sub(r"```(sql)?\s*", "", res_content)
            res_content = res_content.replace("```", "").strip()
            state["sql_query"] = res_content
        except Exception as e:
            print(f"Error in sql_query_generator: {e}")
            state["sql_query"] = ""

        state["processing_path"].append("sql_query_generator")
        return state

    def sql_runner(self, state: AgentState) -> AgentState:
        """Execute the generated SQL query"""
        query = state.get("sql_query")
        if not query:
            state["sql_result"] = {"error": "No query generated"}
            return state

        # Remove any lingering backticks or markdown formatting just in case
        query = query.replace("```sql", "").replace("```", "").strip()

        result = self.mysql_service.execute_query(query)
        state["sql_result"] = result
        state["processing_path"].append("sql_runner")
        return state

    def data_analyst_agent(self, state: AgentState) -> AgentState:
        """Analyze the SQL results and provide a premium, concise response"""
        query = state["user_query"]
        data = state.get("sql_result")
        
        if not data or (isinstance(data, dict) and "error" in data):
            error_msg = data.get("error") if isinstance(data, dict) else "No data returned."
            state["response"] = {
                "type": "general",
                "content": f"I couldn't find any information for your request. (Details: {error_msg})"
            }
            return state

        if isinstance(data, list) and len(data) == 0:
            state["response"] = {
                "type": "general",
                "content": "No records were found matching your criteria."
            }
            return state

        data_str = json.dumps(data[:15], indent=2) 
        
        system_prompt = """You are a Senior Data Analyst for Luma. 
Your goal is to provide a PREMIUM, HIGHLY CONCISE response.

STRICT FORMATTING RULES:
1. START with the warm answering tone like "Sure here is the data that you were looking for......". 
2. Use professional GitHub-flavored Markdown Tables for list of items.
3. Tables must have clear, capitalized headers (e.g., | NAME | CONTACT NO | STATUS |).
4. Use introductory phrases like "Here is the data," "Based on your request," or "I found...".
5. After the table, add ONE short summary sentence only but this sentence should encapsulate the entire purpose of the reason behind the query.
6. If the user's question is in Roman Urdu, provide the table and a Roman Urdu summary.

USER QUESTION: {query}
DATA:
{data}
"""
        try:
            # Using tutorial_llm for data analyst to ensure higher precision if general_llm is smaller
            response = self.tutorial_llm.invoke([
                SystemMessage(content=system_prompt.format(query=query, data=data_str))
            ])
            
            # Generate suggestions in parallel with language check
            lang_info = state["validation_results"].get("language_analysis", {})
            is_urdu = lang_info.get("language", "").lower() in ["urdu", "roman-urdu"]
            
            suggestions = self.suggestion_generator.generate(
                state["user_query"],
                "sql_query",
                state["conversation_history"],
                language="Roman Urdu" if is_urdu else "English"
            )

            state["response"] = {
                "type": "sql_query",
                "content": response.content.strip(),
                "is_sql": True,
                "data_preview": data,
                "suggested_actions": suggestions
            }
            state["suggestions"] = suggestions
        except Exception as e:
            print(f"Error in data_analyst_agent: {e}")
            state["response"] = {
                "type": "general",
                "content": "I encountered an error while analyzing the data."
            }

        state["processing_path"].append("data_analyst_agent")
        return state

    def validate_response(self, state: AgentState) -> AgentState:
        """Validate response"""
        if "response" not in state or not state["response"]:
            state["validation_results"]["response_valid"] = False
            return state
        
        response = state["response"]
        is_valid = True
        
        if "type" not in response:
            is_valid = False
        
        if "content" not in response or not response["content"]:
            is_valid = False
        
        state["validation_results"]["response_valid"] = is_valid
        state["processing_path"].append("validate_response")
        return state
    
    def fallback_agent(self, state: AgentState) -> AgentState:
        """Handle fallback cases"""
        lang_info = state["validation_results"].get("language_analysis", {})
        is_urdu = lang_info.get("language", "").lower() in ["urdu", "roman-urdu"]

        suggestions = self.suggestion_generator.generate(
            state["user_query"],
            "fallback",
            state["conversation_history"],
            language="Roman Urdu" if is_urdu else "English"
        )
        
        state["response"] = {
            "type": "fallback",
            "content": "How can I help you today?",
            "suggested_actions": suggestions
        }
        
        state["suggestions"] = suggestions
        state["processing_path"].append("fallback_agent")
        return state

    def data_analysis_agent(self, state: AgentState) -> AgentState:
        """Analyze standalone JSON sales data and generate a full markdown report + graphs"""
        try:
            if not DATA_FILE.exists():
                state["response"] = {
                    "type": "error",
                    "content": "Data file not found for analysis."
                }
                return state

            with open(DATA_FILE, encoding="utf-8") as f:
                records = json.load(f)

            lang_info = state["validation_results"].get("language_analysis", {})
            is_urdu = lang_info.get("language", "").lower() in ["urdu", "roman-urdu"]

            # Parallel execution: LLM analysis and Graph generation
            with ThreadPoolExecutor() as executor:
                # 1. LLM Report
                def get_analysis():
                    payload = build_data_summary(records)
                    client = OpenAI(api_key=OPENAI_API_KEY)
                    system_prompt_language = DATA_ANALYSIS_SYSTEM_PROMPT
                    if is_urdu:
                        system_prompt_language += "\n\nCRITICAL: You MUST write the entire report in Roman Urdu."
                    response = client.chat.completions.create(
                        model=MODEL,
                        temperature=0.2,
                        messages=[
                            {"role": "system", "content": system_prompt_language},
                            {"role": "user", "content": "Here is the sales data to analyse:\n\n" + payload}
                        ],
                    )
                    return response.choices[0].message.content.strip()

                future_analysis = executor.submit(get_analysis)
                future_graphs = executor.submit(generate_graphs, records)
                future_suggestions = executor.submit(
                    self.suggestion_generator.generate,
                    state["user_query"],
                    "data_analysis",
                    state["conversation_history"],
                    language="Roman Urdu" if is_urdu else "English"
                )

                content = future_analysis.result()
                graph_paths = future_graphs.result()
                suggestions = future_suggestions.result()

            state["response"] = {
                "type": "data_analysis",
                "content": content,
                "graphs": graph_paths,
                "suggested_actions": suggestions,
                "is_urdu": is_urdu
            }
            state["suggestions"] = suggestions

        except Exception as e:
            print(f"Error in data_analysis_agent: {e}")
            state["response"] = {
                "type": "error",
                "content": "Failed to analyze data."
            }

        state["processing_path"].append("data_analysis_agent")
        return state

# ==================== LANGGRAPH SETUP ====================
def create_agent_graph(checkpointer=None):
    """Create LangGraph with an optional checkpointer"""
    nodes = AgentNodes()
    workflow = StateGraph(AgentState)
    
    # ... (rest of node setup remains the same)
    # Add nodes
    workflow.add_node("analyze_request", nodes.analyze_request)
    workflow.add_node("route_decision", nodes.route_decision)
    workflow.add_node("general_agent", nodes.general_agent)
    workflow.add_node("capabilities_agent", nodes.capabilities_agent)
    workflow.add_node("tutorial_agent", nodes.tutorial_agent)
    workflow.add_node("clarification_agent", nodes.clarification_agent)
    workflow.add_node("history_summary_agent", nodes.history_summary_agent)
    workflow.add_node("validate_response", nodes.validate_response)
    workflow.add_node("fallback_agent", nodes.fallback_agent)
    workflow.add_node("sql_query_generator", nodes.sql_query_generator)
    workflow.add_node("sql_runner", nodes.sql_runner)
    workflow.add_node("data_analyst_agent", nodes.data_analyst_agent)
    workflow.add_node("data_analysis_agent", nodes.data_analysis_agent)
    
    # Set entry point
    workflow.set_entry_point("analyze_request")
    
    # Add edges
    workflow.add_edge("analyze_request", "route_decision")
    
    # Conditional routing
    def route_from_decision(state: AgentState) -> str:
        return state.get("next_node", "fallback_agent")
    
    workflow.add_conditional_edges(
        "route_decision",
        route_from_decision,
        {
            "general_agent": "general_agent",
            "capabilities_agent": "capabilities_agent",
            "tutorial_agent": "tutorial_agent",
            "clarification_agent": "clarification_agent",
            "history_summary_agent": "history_summary_agent",
            "sql_query_generator": "sql_query_generator",
            "data_analysis_agent": "data_analysis_agent",
            "fallback_agent": "fallback_agent",
        }
    )
    
    # Add validation
    workflow.add_edge("general_agent", "validate_response")
    workflow.add_edge("capabilities_agent", "validate_response")
    workflow.add_edge("tutorial_agent", "validate_response")
    workflow.add_edge("clarification_agent", "validate_response")
    workflow.add_edge("history_summary_agent", "validate_response")
    workflow.add_edge("fallback_agent", "validate_response")
    
    # Linear pipeline for SQL
    workflow.add_edge("sql_query_generator", "sql_runner")
    workflow.add_edge("sql_runner", "data_analyst_agent")
    workflow.add_edge("data_analyst_agent", "validate_response")
    
    # Pipeline for standalone JSON data analysis
    workflow.add_edge("data_analysis_agent", "validate_response")
    
    workflow.add_edge("validate_response", END)
    
    # Compile graph with provided or new checkpointer
    if checkpointer is None:
        checkpointer = MemorySaver()
        
    graph = workflow.compile(checkpointer=checkpointer)
    return graph, nodes

def refresh_knowledge_base():
    """Refresh the entire knowledge base and agent system state"""
    try:
        from chat import refresh_components
        print("AGENT SYSTEM: Starting knowledge refresh...", flush=True)
        
        # 1. Refresh retrieval components in chat.py
        refresh_components()
        
        # 2. Re-create graph and nodes but reuse the EXISTING checkpointer
        system = get_agent_system()
        existing_checkpointer = system.checkpointer
        new_graph, new_nodes = create_agent_graph(checkpointer=existing_checkpointer)
        
        # 3. Update the global system instance
        system.graph = new_graph
        
        print("AGENT SYSTEM: Knowledge refresh complete.", flush=True)
        return True
    except Exception as e:
        print(f"Error refreshing knowledge base: {e}")
        import traceback
        traceback.print_exc()
        return False

def format_response_recursive(data: Any) -> Any:
    """Recursively apply bold formatting to all strings in a data structure."""
    if isinstance(data, str):
        return format_step_text(data)
    elif isinstance(data, list):
        return [format_response_recursive(item) for item in data]
    elif isinstance(data, dict):
        return {k: format_response_recursive(v) for k, v in data.items()}
    return data

# ==================== MAIN INTERFACE ====================
class LangGraphAgentSystem:
    """Main interface"""
    
    def __init__(self):
        self.checkpointer = MemorySaver()
        self.graph, _ = create_agent_graph(checkpointer=self.checkpointer)
        self.config = {"configurable": {"thread_id": "default_thread"}}
    
    def process_user_query(self, user_query: str, conversation_history: List[str] = None, 
                          last_tutorial: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process user query"""
        if conversation_history is None:
            conversation_history = []
        if last_tutorial is None:
            last_tutorial = []
        
        initial_state: AgentState = {
            "user_query": user_query,
            "llm_intent": "",
            "confidence": 0.0,
            "detected_language": "english",
            "is_confused": False,
            "requires_clarification": False,
            "step_to_clarify": None,
            "response": {},
            "conversation_history": conversation_history,
            "last_tutorial": last_tutorial,
            "suggestions": [],
            "next_node": "",
            "processing_path": [],
            "validation_results": {},
            "sql_query": None,
            "sql_result": None
        }
        
        try:
            final_state = self.graph.invoke(initial_state, self.config)
            
            response = final_state["response"]
            assistant_text = response.get("content", "")
            
            conversation_history.append(f"User: {user_query}")
            conversation_history.append(f"Assistant: {assistant_text}")
            
            output = {
                **response,
                "conversation_history": conversation_history,
                "detected_intent": final_state["llm_intent"],
                "generated_sql": final_state.get("sql_query")
            }
            
            # Post-process the output to bold terms in single quotes
            # Only apply to keys that shown in the UI to improve performance
            for key in ["content", "section_title"]:
                if key in output and isinstance(output[key], str):
                    output[key] = format_step_text(output[key])
            
            if "steps" in output and isinstance(output["steps"], list):
                output["steps"] = format_response_recursive(output["steps"])
            
            return output
            
        except Exception as e:
            return {
                "type": "error",
                "content": f"I encountered an error: {str(e)}",
                "conversation_history": conversation_history,
                "suggested_actions": ["How to add a new region?", "What can you help me with?"]
            }


# ==================== INITIALIZE SYSTEM ====================
_langgraph_system = None

def get_agent_system():
    """Lazy initialization of the agent system"""
    global _langgraph_system
    if _langgraph_system is None:
        print("AGENT SYSTEM: Initializing LangGraph system...", flush=True)
        _langgraph_system = LangGraphAgentSystem()
    return _langgraph_system

def refresh_knowledge_base_deprecated():
    """Refresh the knowledge base cache"""
    try:
        system = get_agent_system()
        system.graph = create_agent_graph()
    except Exception as e:
        print(f"Error refreshing knowledge base: {e}")

def process_user_query(user_query: str, conversation_history: List[str] = None, 
                      last_tutorial: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Main entrypoint"""
    system = get_agent_system()
    return system.process_user_query(user_query, conversation_history, last_tutorial)