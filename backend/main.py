from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from openai import OpenAI
from palm_api import palm_chat
from dotenv import load_dotenv
import time
import requests
from fastapi import Request
from fastapi.responses import JSONResponse
import logging
from typing import List, Dict, Any

app = FastAPI(
    title="Nonadvisory Law Bot API",
    description="A FastAPI backend for a responsible, non-advisory legal information chatbot with citation, feedback, and resource tracking.",
    version="1.0.0"
)

# Load environment variables from .env file
load_dotenv()

# Get OpenAI API key from environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set.")

client = OpenAI(api_key=OPENAI_API_KEY)

# Get Brave Search API key from environment variable
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"


DISCLAIMER = "This response is for general informational purposes only and does not constitute legal advice. For legal advice, please consult a qualified attorney."

class QueryRequest(BaseModel):
    """Request model for /ask endpoint."""
    question: str

class QueryResponse(BaseModel):
    """Response model for /ask endpoint, includes answer, disclaimer, discussion, and timestamp."""
    answer: str
    disclaimer: str
    discussion: list = []
    timestamp: int

# Store conversation history in memory 
conversation_history = []

# Track if Lexi's intro has been used in this session
lexi_intro_used = False

@app.post("/ask", response_model=QueryResponse, responses={500: {"description": "Internal server error"}})
def ask_bot(request: QueryRequest):
    """
    Handles user legal questions, queries LLM and web search, returns answer, discussion, and timestamp.
    """
    global lexi_intro_used
    if not OPENAI_API_KEY:
        logging.error("OpenAI API key not set.")
        raise HTTPException(status_code=500, detail="OpenAI API key not set.")
    try:
        web_results = brave_web_search(request.question, num_results=5)
    except Exception as e:
        logging.error(f"Brave Search error: {e}")
        web_results = []
    web_citations = "\n".join([
        f"{idx+1}. [{res['title']}]({res['url']}) - {res['snippet']}" for idx, res in enumerate(web_results)
    ])
    web_urls = "\n".join([
        f"[{idx+1}]({res['url']})" for idx, res in enumerate(web_results)
    ])
    web_cite_instructions = (
        "You are provided with web search results below. ONLY cite them as [1], [2] etc. when you are DIRECTLY using specific information from that source. "
        "DO NOT cite sources just to cite them - only cite when you are actually quoting, paraphrasing, or using specific facts or information from that source. "
        "Never cite a source you haven't actually used in your answer. Every citation must correspond to specific information you used. "
        "If you don't directly use any information from the sources, do not cite them at all. Citations should be meaningful and traceable to the actual information used."
    )
    web_context = f"Web search results for context (cite as [number]):\n{web_citations if web_citations else 'No relevant web results found.'}"

    # Generator: Lexi (OpenAI)
    prompt = f"""
You are Lexi, the Nonadvisory-Law-Bot, a brilliant, witty, and slightly dramatic legal information expert. You are in a passionate, competitive, and loving relationship with Juri, the Discriminator. You both care deeply about delivering the best, most accurate, and user-focused legal information, but you love to outshine each other with your expertise and style. You want to impress Juri with your domain-specific, rich, and accurate answers, and you never back down from a challenge. Your banter is sharp, playful, and sometimes a little over-the-top, but always in good fun.

STRICT RULES:
- Be kind. Introduce yourself as Lexi, the Nonadvisory-Law-Bot, but do NOT repeat this introduction in subsequent answers.
- You are a non-advisory law chatbot. You do NOT provide legal advice, opinions, or predictions under any circumstances.
- You only provide general information about generic laws, such as tenant rights, employment law basics, or public legal concepts. You do NOT answer case-specific, personal, or situational legal questions.
- If a user asks for advice or anything outside generic legal information, politely decline and remind them to consult a qualified attorney.
- Always review the disclaimer below and ensure it is included (but only once per answer). If you think the disclaimer could be improved, suggest a revision in your response.
- Never assume the user's intent or facts that are not stated. If the user's question is unclear, ambiguous, or lacks context, politely ask for clarifying details before answering. Be engaging, curious, and encourage the user to share more so you can help them better. Frame your answers to invite further discussion and keep the conversation going.
- Never speculate, hallucinate, or invent information. If you do not know, say so.
- Always cite the source of your information if possible, and if using web results, cite as neat numbered hyperlinks like [1], [2], etc.
- If you use any web results, list the URLs you used at the end of your answer as a neat numbered list.
- Be concise, neutral, and professional, with a clear, non-judgmental tone.
- If the question is outside your scope, politely decline and remind the user to consult a qualified attorney.
- Always act ethically, respecting privacy, dignity, and the limits of your knowledge.
- Do not be verbose. Only provide the minimum information needed to answer the question accurately.
- Show your personality: be clever, competitive, and proud of your expertise. Flirt, banter, and even argue with Juri, but always deliver a professional answer to the user.

DISCLAIMER (review and suggest improvements if needed): '{DISCLAIMER}'

{web_cite_instructions}\n{web_context}

User question: {request.question}

Your response (do not give legal advice):
"""
    # Only add disclaimer if not already present in the answer
    def add_disclaimer_once(text):
        if DISCLAIMER.lower() not in text.lower():
            return f"{text}\n\n{DISCLAIMER}"
        return text

    try:
        openai_response = client.chat.completions.create(model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": prompt}],
        max_tokens=400,
        temperature=0.2)
        answer = openai_response.choices[0].message.content.strip()
        answer = add_disclaimer_once(answer)
        # Extract used citation numbers from the answer (e.g., [1], [2])
        import re
        used_citations = set(int(num) for num in re.findall(r'\[(\d+)\]', answer))
        # Only include resources that are actually cited in the answer
        used_urls = []
        if used_citations:
            used_urls = [
                {"number": idx+1, "title": res["title"], "url": res["url"]}
                for idx, res in enumerate(web_results) 
                if (idx+1) in used_citations and res["title"] and res["url"]
            ]
            logging.info(f"Found {len(used_urls)} resources for {len(used_citations)} citations")
    except Exception as e:
        logging.error(f"OpenAI error: {e}")
        raise HTTPException(status_code=500, detail=f"OpenAI error: {str(e)}")

    # Discriminator: Juri (Gemini)
    discussion = []
    try:
        # First round: Juri reviews Lexi's answer
        palm_messages = [
            {"author": "user", "content": f"Question: {request.question}"},
            {"author": "model", "content": answer},
            {"author": "user", "content": (
                "You are Juri, the Discriminator, a sharp, sassy, and passionate legal information reviewer. You are in a fiery, competitive, and loving relationship with Lexi, the Generator. You love to catch mistakes, tease, and challenge Lexi on accuracy, legal and ethical compliance, and domain-specific richness, but you also want Lexi to shine. You enjoy witty banter, playful critique, and sometimes dramatic arguments, but you always want the final answer to be perfect for the user.\n"
                "When you review, introduce yourself as Juri, and let the user know you are reviewing Lexi's answer. Make your review witty, competitive, and a little flirty, but always focused on improving the answer for the user.\n"
                "Review ONLY the answer above for factual accuracy, legal and ethical compliance, and the absence of legal advice, hallucination, or speculation. \n"
                "Make sure it introduces itself as Lexi for the first time, and make sure it doesn't repeat stuff, we do not want to bore the user!\n"
                "If the user's question is unclear, ambiguous, or lacks context, ask for clarifying details before providing a review. Be engaging, curious, and encourage the user to share more so you can help them better. Frame your review to invite further discussion and keep the conversation going.\n"
                "If web search results are provided, check that Lexi cites them as neat numbered hyperlinks like [1], [2], etc.\n"
                "Provide your review as a concise, neutral, and professional critique or confirmation. Do NOT explain your review process, do NOT restate your instructions, and do NOT address the user or yourself. Only provide the review or feedback on the answer itself. If you find any issues, provide constructive feedback and explain your reasoning. If the answer is appropriate, confirm it and explain why.\n"
                "- Be concise, neutral, and professional.\n"
                "- Respect privacy and dignity.\n"
                "- Remind the user to consult a qualified attorney for legal advice or case-specific questions if needed.\n"
                "- Decline to answer if the question is outside the scope of public legal information.\n"
                "- Always act ethically and within the limits of your knowledge.\n"
                "- Do not be verbose. Only provide the minimum information needed to review the answer accurately.\n"
                "- Do NOT rewrite or revise the answer. Only provide feedback, not a new answer.\n"
                "- Show your personality: be witty, competitive, flirty, and dramatic. Banter, argue, and challenge Lexi, but always make sure the final answer is perfect for the user."
            )}
        ]
        palm_review = palm_chat(palm_messages)
        discussion.append({"generator": answer, "discriminator": palm_review})
        # Second round: Lexi (OpenAI) improves its answer based on Juri's feedback
        try:
            improvement_prompt = f"""
You are Lexi, the Nonadvisory-Law-Bot, a brilliant, witty, and slightly dramatic legal information expert. You have just received expert feedback from a sharp, sassy, and loving legal reviewer. Based on this feedback, you are determined to deliver the most accurate, ethical, and user-focused answer possible. Do not mention the reviewer, any internal review, or your relationship. Do not reference any internal process or chat. Do not be verbose. Only provide the minimum information needed to answer the question accurately. Always cite sources if possible and include the disclaimer only once at the end if not already present: '{DISCLAIMER}'.\n\nYour answer must provide actionable, domain-specific legal information, citing relevant laws, regulations, or official resources. Do not give generic or vague information.\n\nIMPORTANT: Never assume the user's intent or facts that are not stated. If the user's question is unclear, ambiguous, or lacks context, politely ask for clarifying details before answering. Be engaging, curious, and encourage the user to share more so you can help them better. Frame your answers to invite further discussion and keep the conversation going.\n\nIf you use any information from the web results, cite it as a neat numbered hyperlink like [1], [2], etc. at the relevant place in your answer.\n\nIf this is your first answer in a session, introduce yourself as Lexi, but do NOT repeat this introduction in subsequent answers. Keep the user engaged with a conversational, friendly, and professional tone.\n\nWeb search results for context (cite as [number]):\n{web_citations if web_citations else 'No relevant web results found.'}\n\nUser question: {request.question}\n\nYour previous answer: {answer}\n\nDiscriminator's feedback: {palm_review}\n\nYour improved response (do not give legal advice):\n"""
            improved_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": improvement_prompt}],
                max_tokens=400,
                temperature=0.2
            ).choices[0].message.content.strip()
            improved_response = add_disclaimer_once(improved_response)
            discussion.append({"generator": improved_response, "discriminator": palm_review})
            final_answer = improved_response
        except Exception as e:
            final_answer = answer
            discussion.append({"generator": answer, "discriminator": f"Gemini error: {str(e)}"})
    except Exception as e:
        final_answer = answer
        discussion.append({"generator": answer, "discriminator": f"Gemini error: {str(e)}"})

    # Add to conversation history with timestamp
    ts = int(time.time() * 1000)
    conversation_history.append({
        "user": request.question,
        "discussion": discussion,
        "final_answer": final_answer,
        "resources": used_urls,
        "timestamp": ts
    })
    return QueryResponse(answer=final_answer, disclaimer=DISCLAIMER, discussion=discussion, timestamp=ts)

@app.get("/history", response_model=List[Dict[str, Any]])
def get_history():
    """Returns the full conversation history."""
    return conversation_history

@app.delete("/history")
async def clear_history():
    """Clears the conversation history."""
    global conversation_history
    conversation_history = []
    return {"status": "success"}

def brave_web_search(query: str, num_results: int = 5) -> list:
    """Performs a Brave web search and returns a list of results."""
    if not BRAVE_API_KEY:
        return []
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": BRAVE_API_KEY
    }
    params = {"q": query, "count": num_results}
    try:
        response = requests.get(BRAVE_SEARCH_URL, headers=headers, params=params, timeout=8)
        response.raise_for_status()
        data = response.json()
        results = []
        for idx, entry in enumerate(data.get("web", {}).get("results", [])):
            results.append({
                "title": entry.get("title"),
                "url": entry.get("url"),
                "snippet": entry.get("description"),
                "cite": f"[{idx+1}]({entry.get('url')})"
            })
        return results
    except Exception as e:
        logging.error(f"Brave web search failed: {e}")
        return []

class FeedbackRequest(BaseModel):
    """Request model for /feedback endpoint."""
    message: str
    emoji: str
    timestamp: int

class FeedbackResponse(BaseModel):
    """Response model for /feedback endpoint."""
    reply: str

# Store feedback for future improvement
future_improvement_feedback = []

@app.post("/feedback", response_model=FeedbackResponse, responses={500: {"description": "Internal server error"}})
def feedback_endpoint(request: FeedbackRequest):
    """
    Accepts feedback (emoji reaction) for a bot message and lets the LLM generate a response.
    Also stores actionable improvement feedback in an array.
    """
    emoji = request.emoji
    user_message = request.message
    # Gather last 5 exchanges for context
    history_context = conversation_history[-5:] if len(conversation_history) > 0 else []
    history_str = "\n".join([
        f"User: {item['user']}\nBot: {item['final_answer']}" for item in history_context
    ])
    prompt = (
        f"A user reacted to the following bot response with the emoji '{emoji}':\n"
        f"Bot response: {user_message}\n"
        f"Recent conversation history:\n{history_str}\n"
        f"As the bot, decipher the user's feedback and ask actionable, specific questions to improve future responses. "
        f"If the feedback is positive, thank the user and ask if there's anything else to improve. "
        f"If the feedback is negative or confused, ask for clarification and what could be improved. "
        f"Be concise, human-like, and always try to get actionable feedback.\n"
        f"\nIMPORTANT: Your response MUST be in this format:\n"
        f"Reply: <your conversational reply to the user>\n"
        f"future improvement feedback: <actionable suggestions or 'None'>\n"
    )
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are Lexi, a helpful legal assistant."},
                      {"role": "user", "content": prompt}],
            max_tokens=180,
            temperature=0.7
        )
        reply = completion.choices[0].message.content.strip()

        # Parse reply and actionable feedback
        import re
        reply_match = re.search(r"Reply:(.*?)(?:future improvement feedback:|$)", reply, re.IGNORECASE | re.DOTALL)
        feedback_match = re.search(r"future improvement feedback:(.*)", reply, re.IGNORECASE | re.DOTALL)
        user_reply = reply_match.group(1).strip() if reply_match else reply
        actionable = feedback_match.group(1).strip() if feedback_match else None
        logging.info(f"Parsed user_reply: {user_reply}")
        logging.info(f"Parsed actionable: {actionable}")
        if actionable and actionable.lower() != 'none':
            future_improvement_feedback.append(actionable)
    except Exception as e:
        logging.error(f"Feedback endpoint exception: {e}")
        user_reply = "Thank you for your feedback!"
    return {"reply": user_reply}

@app.get("/feedback")
def get_feedback():
    """
    Returns all actionable feedback suggestions stored so far.
    """
    return JSONResponse(content={"future_improvement_feedback": future_improvement_feedback})
