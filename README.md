# nonadvisory-law-bot

**nonadvisory-law-bot** is a real-time, voice-enabled legal information system designed for constrained, domain-specific question answering. The system integrates fine-tuned transformer-based language models with telephony infrastructure to enable spoken legal information retrieval—without providing legal advice.

---

## Objective

This system enables users to query publicly available legal knowledge (e.g., tenant rights, labor regulations) via a phone call interface. The goal is to:

- Demonstrate modular, MLOps-compliant deployment of fine-tuned LLMs.
- Explore latency-constrained inference in speech-driven environments.
- Provide a safe, non-advisory way to deliver legal information using voice and NLP.  

> This system is explicitly non-advisory and is not a substitute for a licensed attorney. See [`DISCLAIMER.md`](./DISCLAIMER.md).

---

## System Architecture

    ┌──────────────┐
    │ Phone Caller │
    └──────┬───────┘
           │
    Twilio Voice (Webhook)
           │
     ┌─────▼─────┐
     │ Transcribe│  ← Whisper / Deepgram
     └─────┬─────┘
           │
    ┌──────▼──────┐
    │ Query Engine│ ← Fine-tuned LLM
    └──────┬──────┘
           │
     ┌─────▼──────┐
     │ Synthesize │ ← ElevenLabs / Bark
     └─────┬──────┘
           │
    Respond via Twilio Voice


---

## Formal Model Definition

Let:

- xₜ ∈ ℝⁿ be the input audio waveform at time step t.

- sₜ = STT(xₜ) be the transcribed text output from speech-to-text (STT).

- yₜ = f_θ(sₜ, hₜ) be the model’s predicted response given current input and context history.

- aₜ = TTS(yₜ) be the audio synthesized from the generated response.

The model is fine-tuned on a task-specific dataset 𝒟 = { (qᵢ, aᵢ) } for i = 1 to N, using the following objective:

- L(θ) = Σᵢ CE(f_θ(qᵢ), aᵢ) + λ ⋅ DriftPenalty(f_θ).

Where:

- CE is the cross-entropy loss between predicted and target tokens.

- DriftPenalty(f_θ) penalizes semantic deviation from domain-specific response formats and scope.

- λ is a hyperparameter controlling regularization weight.


---

## Model

| Component         | Details |
|------------------|---------|
| Base Model       | `gpt2`, `mistral-7b`, or `falcon-7b-instruct` |
| Fine-Tuning      | LoRA (4-bit PEFT) on legal Q&A corpus |
| Training Tooling | Hugging Face `transformers`, `peft`, `datasets` |
| Quantization     | 4-bit for low-latency CPU inference |
| Target Latency   | < 2s per 100-token generation |

---

##  Dataset

| Source | Examples |
|--------|----------|
| Public legal FAQs | gov websites (e.g., HUD.gov, FTC.gov) |
| Synthetic | Rule-based dialogue generation |
| Format | JSONL: `{ "input": "...", "output": "..." }` |
| Filters | Off-topic removal, contradiction detection, consistency scoring |

---

## Deployment

| Layer | Tech Stack |
|-------|------------|
| API Server | FastAPI |
| TTS       | ElevenLabs (fallback: Bark, pyttsx3) |
| STT       | OpenAI Whisper / Deepgram |
| Telephony | Twilio Voice API (programmable webhook) |
| Model Hosting | Local inference / Hugging Face Endpoint / Ollama |
| Containerization | Docker (GPU and CPU variants) |
| Monitoring | Logging middleware + call/session tracking |

---

## Setup (Coming Soon)

```bash
git clone https://github.com/AkhilByteWrangler/nonadvisory-law-bot.git
cd nonadvisory-law-bot
pip install -r requirements.txt
```

## References

- Hu et al. 2021: LoRA - Low-Rank Adaptation of LLMs
- OpenAI Whisper (Speech-to-Text): https://github.com/openai/whisper
- Hugging Face Transformers: https://huggingface.co/docs/transformers
- Twilio Programmable Voice: https://www.twilio.com/docs/voice




