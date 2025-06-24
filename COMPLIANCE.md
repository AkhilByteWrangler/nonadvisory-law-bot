# Compliance Documentation: Nonadvisory Law Bot

## Legal Disclaimer
- All responses are for general informational purposes only and do not constitute legal advice.
- Users are reminded to consult a qualified attorney for legal advice.
- See `DISCLAIMER.md` for full disclaimer text.

## Data Handling
- No personal data is stored or shared.
- Conversation and feedback are stored in memory only (not persistent).
- No user authentication or PII is processed in production.

## Responsible AI
- LLM outputs are filtered for responsible use.
- Citations are checked and hallucination warnings are shown.
- Feedback is used to improve accuracy and reduce hallucinations.

## Regulatory Notes
- Not certified for GDPR, CCPA, or HIPAA compliance.
- If storing user data, review and implement appropriate compliance measures.
- For production, add privacy policy and terms of service.

## Security
- API keys are stored in environment variables.
- Use HTTPS in production.
- CORS is restricted to trusted origins.

## User Guidance
- Users are informed of limitations and responsible use on the landing page and in documentation.

