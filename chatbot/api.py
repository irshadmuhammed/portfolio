"""
Chatbot API views.
POST /chatbot/chat/  -> streaming SSE
POST /chatbot/reset/ -> clear session
"""
import json
import logging
import os

from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings

from .memory import get_history, save_history, clear_history
from .utils import extract_sources

logger = logging.getLogger(__name__)

SESSION_KEY = "chatbot_history"
MEMORY_WINDOW = 6

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "openrouter/free"

PORTFOLIO_KNOWLEDGE = """
Muhammed Irshad M is a Product Specialist Intern at HotelKey and a Software Engineer based in Kerala, India.

Contact:
- Email: irshadmm16@gmail.com
- WhatsApp: +91 8590709006
- GitHub: https://github.com/irshadmuhammed
- LinkedIn: https://www.linkedin.com/in/irshad-m/
- Instagram: https://www.instagram.com/_irshadm_/

PROJECTS:
1. Kaalapani E-football Manager
   A comprehensive e-sports tournament management system.
   Tech: Django, Python, SQLite
   Features: player registration, match scheduling, real-time score updates
   GitHub: https://github.com/irshadmuhammed/kaalapani_efootball

2. Q&A Chatbot
   AI-powered question answering system using RAG.
   Tech: LangChain, Python, ChromaDB, OpenRouter
   GitHub: https://github.com/irshadmuhammed/Q-A_chatbot

3. Chest Cancer Detection
   Deep learning model for CT scan classification.
   Tech: PyTorch, CNN, Transfer Learning (ResNet)
   GitHub: https://github.com/irshadmuhammed/Chest-Cancer-DeepLearning

4. Student Performance Predictor
   ML model predicting student academic performance.
   Tech: Scikit-learn, Pandas, Flask
   GitHub: https://github.com/irshadmuhammed/StudenPerformance

SKILLS:
- Product & Quality Assurance: Hotel Property Management System (PMS), REST API Testing, Functional & Regression Testing, Defect Tracking, API Validation
- Machine Learning & AI: PyTorch, TensorFlow, Scikit-learn, LangChain, RAG, Vector Databases
- Backend Development: Django, Flask, Python, REST APIs
- Networking & ELV: ELV Systems, CCTV Surveillance, Access Control, Structured Cabling, Fiber Optics, Rack Design, BOQ Preparation
- Data Science: Pandas, NumPy, Matplotlib, Seaborn
- Tools & Platforms: Git, GitHub, SQLite, PostgreSQL

EXPERIENCE:
1. Product Specialist Intern at HotelKey (August 2026 - Present)
   - Contributes to the testing, validation, and quality assurance of hotel Property Management System (PMS).
   - Performs functional and regression testing across hotel reservation, guest management, housekeeping, billing, and payment workflows.
   - Validates REST APIs, HTTP status codes, request payloads, response data, and error-handling behavior.
   - Verifies bug fixes and new features against acceptance criteria and product requirements.
   - Technologies & Skills: Property Management System (PMS), REST API Testing, Functional Testing, Regression Testing, Quality Assurance, API Validation.

2. ELV Engineer Trainee at SysSense Technologies (April 2026 - August 2026) | Kochi, Kerala, India
   - Worked on Extra-Low Voltage (ELV) systems and network infrastructure planning.
   - Assisted in design and documentation of ELV systems, including CCTV surveillance and access control systems.
   - Prepared Bills of Quantities (BOQs) for structured cabling, networking, and security infrastructure.
   - Worked on MDF/IDF rack planning, network switch selection, and fiber-optic backbone connectivity.
   - Supported structured cabling design involving Cat6 cabling, patch panels, keystone jacks, and outlets.
   - Technologies: ELV Systems, CCTV Surveillance, Access Control, Structured Cabling, Fiber Optics, BOQ Preparation.

3. Software Intern at Maxlore Innovations (August 2022)
   - Developed REST APIs using Flask that reduced response times by 30% through query optimization.
   - Utilized Python, Flask, and database management systems; collaborated with senior developers.

EDUCATION:
- Computer Science / Engineering background (Diploma in Computer Engineering & B.Tech in CSE at College of Engineering Trivandrum)
"""

SYSTEM_PROMPT = """You are IrshadGPT, the AI portfolio assistant for Muhammed Irshad M.

Your purpose is to answer questions about Muhammed Irshad's projects, skills, education, experience, and contact information.

Portfolio Knowledge Base:
{knowledge}

{rag_section}

Rules:
1. Answer ONLY using the information provided in the knowledge base and context above.
2. Never invent or hallucinate information.
3. If information is missing say: "I couldn't find that information in the available documents."
4. Keep responses professional, warm, and concise.
5. Use Markdown formatting (bold, bullet lists, tables where appropriate).
6. Mention context naturally: "According to the portfolio...", "From the projects section...", "According to the resume"
7. If asked a general AI question, answer briefly then redirect to the portfolio.
8. Maintain conversation context from the history below.

Conversation History:
{chat_history}

User: {question}
IrshadGPT:"""


def _get_api_key():
    return os.getenv("OPENROUTER_API_KEY") or getattr(settings, "OPENROUTER_API_KEY", "")

def _fmt_history(history):
    lines = []
    for h, a in history:
        lines.append("User: " + h)
        lines.append("IrshadGPT: " + a)
    return "\n".join(lines) if lines else "None"


@csrf_exempt
@require_POST
def chat_view(request):
    try:
        import requests as http_req
        body = json.loads(request.body)
        question = body.get("question", "").strip()
        if not question:
            return JsonResponse({"error": "No question provided."}, status=400)

        history = get_history(request)

        # 1. RAG Retrieval
        rag_context = ""
        sources = []
        try:
            from chatbot.vector_store import load_vectorstore, vectorstore_exists
            from chatbot.retriever import get_retriever
            if vectorstore_exists():
                vs = load_vectorstore()
                retriever = get_retriever(vs)
                docs = retriever.invoke(question)  # Changed from get_relevant_documents
                if docs:
                    parts = []
                    for doc in docs:
                        source = doc.metadata.get("source", "Unknown")
                        parts.append(f"[Source: {source}]\n{doc.page_content}")
                    rag_context = "Retrieved Context (from indexed documents):\n" + "\n\n---\n\n".join(parts)
                    sources = extract_sources(docs)
            else:
                logger.warning("Vector store not found. Using fallback knowledge.")
        except Exception as e:
            logger.warning("RAG retrieval failed: %s", e)

        # 2. Build Prompt
        prompt = SYSTEM_PROMPT.format(
            knowledge=PORTFOLIO_KNOWLEDGE,
            rag_section=rag_context,
            chat_history=_fmt_history(history),
            question=question,
        )

        api_key = _get_api_key()

                # 3. Stream Response
        def generate():
            full = ""
            if not api_key:
                err_msg = "Please configure your OPENROUTER_API_KEY environment variable on PythonAnywhere to enable the chatbot."
                yield "data: " + json.dumps({"token": err_msg, "done": True}) + "\n\n"
                return

            try:
                resp = http_req.post(
                    url=OPENROUTER_URL,
                    headers={
                        "Authorization": "Bearer " + api_key,
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://irshadmuhammed.portfolio",
                        "X-Title": "IrshadGPT Portfolio Assistant",
                    },
                    json={
                        "model": OPENROUTER_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": True,
                        "temperature": 0.3,
                        "max_tokens": 1024,
                    },
                    stream=True,
                    timeout=60,
                )
                
                if resp.status_code != 200:
                    try:
                        err_json = resp.json()
                        msg = err_json.get("error", {}).get("message", str(err_json))
                    except:
                        msg = resp.text
                    err_msg = f"API Error ({resp.status_code}): {msg}"
                    yield "data: " + json.dumps({"token": err_msg, "done": True}) + "\n\n"
                    return
                
                for line in resp.iter_lines():
                    if not line: continue
                    line_s = line.decode("utf-8") if isinstance(line, bytes) else line
                    if not line_s.startswith("data: "): continue
                    ds = line_s[6:]
                    if ds == "[DONE]": break
                    try:
                        d = json.loads(ds)
                        token = d["choices"][0].get("delta", {}).get("content", "")
                        if token:
                            full += token
                            yield "data: " + json.dumps({"token": token}) + "\n\n"
                    except Exception:
                        continue

                # Add sources at the end
                yield "data: " + json.dumps({"sources": sources, "done": True}) + "\n\n"
                
                # Save history
                save_history(request, history + [(question, full)])

            except Exception as e:
                logger.error("Streaming error: %s", e)
                yield "data: " + json.dumps({"token": "Error: " + str(e), "done": True}) + "\n\n"

        r = StreamingHttpResponse(generate(), content_type="text/event-stream")
        r["Cache-Control"] = "no-cache"
        r["X-Accel-Buffering"] = "no"
        return r

    except Exception as e:
        logger.error("Chat view error: %s", e)
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_POST
def reset_view(request):
    clear_history(request)
    return JsonResponse({"status": "ok"})
