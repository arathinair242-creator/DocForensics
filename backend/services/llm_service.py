"""
Configurable LLM Service for AI-Assisted Document Forensic Explanations.
Supports Google Gemini and OpenAI when API keys are configured,
and provides robust evidence-based local heuristic fallback if no key is supplied.
Complies with requirement: Do not make application dependent on a paid API.
"""
import os
import httpx
from typing import Dict, Any, Optional

LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "").strip()


def get_llm_status() -> Dict[str, Any]:
    """Returns current LLM integration status and configured model."""
    configured = bool(LLM_API_KEY)
    provider = "none"
    model = LLM_MODEL or "local-rule-engine"
    if configured:
        if LLM_API_KEY.startswith("AIza") or "gemini" in model.lower():
            provider = "Google Gemini"
            if not LLM_MODEL:
                model = "gemini-1.5-flash"
        elif LLM_API_KEY.startswith("sk-") or "gpt" in model.lower():
            provider = "OpenAI"
            if not LLM_MODEL:
                model = "gpt-4o-mini"
        else:
            provider = "Generic / Custom"

    return {
        "configured": configured,
        "provider": provider,
        "model": model,
        "fallback_available": True
    }


def explain_anomaly(anomaly_type: str, description: str, evidence: str, doc_name: str = "") -> str:
    """
    Generates a clear forensic explanation for an anomaly using configured LLM,
    or falls back to evidence-based local intelligence.
    Never invents facts outside of provided evidence.
    """
    status = get_llm_status()
    if not status["configured"]:
        return _local_heuristic_explanation(anomaly_type, description, evidence, doc_name)

    prompt = f"""You are a certified digital document forensic investigator.
Analyze the following detected document anomaly strictly based on the provided evidence.
Do not invent any facts, numbers, or conclusions not backed by the evidence.

Document: {doc_name}
Anomaly Category: {anomaly_type}
Finding Description: {description}
Supporting Evidence: {evidence}

Provide a concise 2-3 sentence forensic explanation covering:
1. Why this pattern represents a structural, visual, or contextual inconsistency.
2. The recommended forensic verification action for the investigator.
Keep the tone objective, precise, and professional."""

    try:
        if status["provider"] == "Google Gemini":
            model = status["model"] or "gemini-1.5-flash"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={LLM_API_KEY}"
            resp = httpx.post(
                url,
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=12.0
            )
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                return text
        elif status["provider"] == "OpenAI":
            model = status["model"] or "gpt-4o-mini"
            resp = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {LLM_API_KEY}"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are a senior document forensics investigator."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2
                },
                timeout=12.0
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()
    except Exception:
        pass

    # Graceful fallback to deterministic local heuristic
    return _local_heuristic_explanation(anomaly_type, description, evidence, doc_name)


def _local_heuristic_explanation(anomaly_type: str, description: str, evidence: str, doc_name: str) -> str:
    """Deterministic, evidence-grounded forensic explanation without external API dependency."""
    cat = anomaly_type.lower()
    if "visual" in cat:
        return (
            f"Visual forensic analysis detected localized artifacts indicative of potential post-processing "
            f"or tampering. Supporting evidence indicates '{evidence or description}'. An investigator should inspect "
            f"the pixel neighborhood at high magnification and verify underlying compression quantization."
        )
    elif "contextual" in cat:
        return (
            f"Contextual intelligence identified an internal logic mismatch within the document: '{description}'. "
            f"Evidence: {evidence or 'Field cross-computation variance'}. This warrants human cross-referencing against "
            f"primary issuer records or underlying source documentation."
        )
    elif "cross" in cat or "discrepancy" in cat:
        return (
            f"Cross-document entity correlation revealed conflicting data across submitted documents: '{description}'. "
            f"Evidence: {evidence}. Verification with external registry or applicant interview is recommended."
        )
    else:
        return (
            f"Forensic observation identified: {description}. Evidence captured: {evidence or 'Pattern anomaly'}. "
            f"Recommended action: human review and secondary verification."
        )
