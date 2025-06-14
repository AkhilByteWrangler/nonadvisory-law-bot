from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from openai import OpenAI
from palm_api import palm_chat
from dotenv import load_dotenv
import time
import requests

app = FastAPI()

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
    question: str

class QueryResponse(BaseModel):
    answer: str
    disclaimer: str
    discussion: list = []  # Add discussion to the response

# Store conversation history in memory 
conversation_history = []

# Track if Lexi's intro has been used in this session
lexi_intro_used = False

@app.post("/ask", response_model=QueryResponse)
def ask_bot(request: QueryRequest):
    global lexi_intro_used
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key not set.")
    # Always query Brave Search API for every question
    web_results = brave_web_search(request.question, num_results=5)
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

    # Remove Lexi intro logic, handle in prompt only

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
            print(f"Found {len(used_urls)} resources for {len(used_citations)} citations")
    except Exception as e:
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
    conversation_history.append({
        "user": request.question,
        "discussion": discussion,
        "final_answer": final_answer,
        "resources": used_urls,  # Add used URLs for frontend dropdown
        "timestamp": int(time.time() * 1000)
    })
    return QueryResponse(answer=final_answer, disclaimer=DISCLAIMER, discussion=discussion)

@app.get("/history")
def get_history():
    return conversation_history

@app.delete("/history")
async def clear_history():
    global conversation_history
    conversation_history = []
    return {"status": "success"}

def brave_web_search(query, num_results=5):
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
        return []
