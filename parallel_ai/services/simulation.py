from __future__ import annotations

import hashlib
import json
import os
from copy import deepcopy
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from parallel_ai.models import SCORE_KEYS
from parallel_ai.services.pendo import track as pendo_track
from parallel_ai.services.prompts import SYSTEM_PROMPT, simulation_prompt


load_dotenv()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-2024-08-06")


SIMULATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "executive_summary",
        "recommendation",
        "confidence_score",
        "confidence_explanation",
        "futures",
        "regret_analysis",
        "bias_profile",
        "advisor_debate",
        "life_dashboard",
        "recommendations",
    ],
    "properties": {
        "executive_summary": {"type": "string"},
        "recommendation": {"type": "string"},
        "confidence_score": {"type": "integer"},
        "confidence_explanation": {"type": "string"},
        "futures": {
            "type": "array",
            "items": {"type": "object"},
        },
        "regret_analysis": {"type": "object"},
        "bias_profile": {"type": "object"},
        "advisor_debate": {
            "type": "array",
            "items": {"type": "object"},
        },
        "life_dashboard": {"type": "object"},
        "recommendations": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
}


def generate_simulation(decision: str, option_a: str, option_b: str, profile: dict[str, Any]) -> dict[str, Any]:
    if os.getenv("OPENAI_API_KEY"):
        try:
            return _generate_with_openai(decision, option_a, option_b, profile)
        except Exception as exc:
            pendo_track("simulation_failed", properties={
                "error_message": str(exc)[:200],
                "decision_text": decision[:200],
                "option_a": option_a[:100],
                "option_b": option_b[:100],
                "openai_model": MODEL,
                "fallback_used": True,
            })
            fallback = _generate_locally(decision, option_a, option_b, profile)
            fallback["api_warning"] = f"OpenAI generation failed, local model used: {exc}"
            return fallback
    return _generate_locally(decision, option_a, option_b, profile)


def _generate_with_openai(decision: str, option_a: str, option_b: str, profile: dict[str, Any]) -> dict[str, Any]:
    client = OpenAI()
    response = client.responses.create(
        model=MODEL,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": simulation_prompt(decision, option_a, option_b, profile)},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "parallel_ai_simulation",
                "schema": SIMULATION_SCHEMA,
                "strict": False,
            }
        },
    )
    return _normalize_simulation(json.loads(response.output_text), decision, option_a, option_b, profile)


def _stable_int(seed: str, minimum: int, maximum: int) -> int:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    value = int(digest[:8], 16)
    return minimum + value % (maximum - minimum + 1)


def _profile_signal(profile: dict[str, Any]) -> dict[str, int]:
    risk = str(profile.get("risk_tolerance", "Moderate")).lower()
    income = int(profile.get("monthly_income") or 0)
    savings = int(profile.get("savings") or 0)
    time_text = str(profile.get("time_available", ""))
    time_score = 70 if "20" in time_text or "full" in time_text.lower() else 55 if "10" in time_text else 42
    runway = min(90, max(20, int((savings / max(income, 1)) * 9))) if income else 45
    risk_score = 78 if "high" in risk else 48 if "low" in risk else 62
    return {"risk": risk_score, "time": time_score, "runway": runway}


def _generate_locally(decision: str, option_a: str, option_b: str, profile: dict[str, Any]) -> dict[str, Any]:
    signal = _profile_signal(profile)
    paths = [
        ("A", "Future A", option_a, 8),
        ("B", "Future B", option_b, -3),
        ("C", "Future C", "No action taken", -16),
    ]
    futures = []
    for future_id, name, choice, tilt in paths:
        futures.append(_future(decision, future_id, name, choice, profile, signal, tilt))

    best = max(futures, key=lambda item: item["scores"]["opportunity"] + item["scores"]["career_growth"] - item["scores"]["regret"])
    regret_values = {
        "financial": max(10, 100 - best["scores"]["wealth"] + 8),
        "career": max(10, 100 - best["scores"]["career_growth"] + 6),
        "lifestyle": max(10, 100 - best["scores"]["happiness"] + 4),
        "family": _stable_int(decision + "family", 25, 72),
        "opportunity": max(10, 100 - best["scores"]["opportunity"] + 10),
    }
    regret_values["overall"] = int(sum(regret_values.values()) / len(regret_values))

    bias_profile = _bias_profile(profile, signal)
    dashboard = {
        "career_outlook": best["scores"]["career_growth"],
        "financial_outlook": best["scores"]["wealth"],
        "learning_outlook": min(96, best["scores"]["opportunity"] + 5),
        "relationship_outlook": max(35, 100 - best["scores"]["stress"] + 8),
        "mental_wellness_outlook": max(35, best["scores"]["happiness"] - best["scores"]["stress"] // 4),
        "future_potential_score": int((best["scores"]["opportunity"] + best["scores"]["career_growth"] + best["success_probability"]) / 3),
    }

    return {
        "executive_summary": (
            f"Parallel AI sees '{best['choice']}' as the strongest future for {decision}, "
            "provided you convert uncertainty into a dated plan with measurable proof points."
        ),
        "recommendation": (
            f"Lean toward {best['choice']}, but treat it as a 90-day experiment before making irreversible commitments."
        ),
        "confidence_score": int((dashboard["future_potential_score"] + signal["time"] + signal["runway"]) / 3),
        "confidence_explanation": "Confidence is based on available time, financial runway, goal alignment, and relative downside.",
        "futures": futures,
        "regret_analysis": {
            **regret_values,
            "explanation": "Regret is highest where delayed action compounds: learning curves, savings runway, and missed market timing.",
        },
        "bias_profile": bias_profile,
        "advisor_debate": _debate(option_a, option_b, profile),
        "life_dashboard": dashboard,
        "recommendations": [
            "Run a 30-day validation sprint before announcing a final decision.",
            "Define one financial guardrail, one learning milestone, and one health boundary.",
            "Speak with three people already living each path before committing.",
            "Schedule a decision review date so analysis does not become avoidance.",
        ],
    }


def _future(decision: str, future_id: str, name: str, choice: str, profile: dict[str, Any], signal: dict[str, int], tilt: int) -> dict[str, Any]:
    base = f"{decision}:{future_id}:{choice}:{profile}"
    wealth = max(18, min(96, _stable_int(base + "wealth", 45, 82) + tilt + signal["runway"] // 12))
    happiness = max(20, min(95, _stable_int(base + "happy", 48, 86) + tilt // 2))
    stress = max(12, min(92, _stable_int(base + "stress", 30, 78) - tilt + (100 - signal["runway"]) // 12))
    growth = max(18, min(97, _stable_int(base + "growth", 44, 90) + tilt + signal["time"] // 15))
    opportunity = max(20, min(98, _stable_int(base + "opp", 46, 91) + tilt + signal["risk"] // 18))
    regret = max(8, min(92, 100 - int((wealth + happiness + growth + opportunity) / 4) + stress // 5))
    success = max(15, min(94, int((wealth + growth + opportunity + signal["time"]) / 4) - stress // 8))
    scores = {
        "wealth": wealth,
        "happiness": happiness,
        "stress": stress,
        "career_growth": growth,
        "regret": regret,
        "opportunity": opportunity,
    }
    return {
        "id": future_id,
        "name": name,
        "choice": choice,
        "success_probability": success,
        "scores": scores,
        "summary": _summary(choice, profile, scores, success),
        "timeline": _timeline(choice, profile, scores),
        "future_letter": _letter(choice, profile, scores),
        "opportunity_costs": _opportunity_costs(choice, future_id),
        "alternate_life": _alternate_life(choice, future_id),
        "headlines": _headlines(choice, scores),
    }


def _summary(choice: str, profile: dict[str, Any], scores: dict[str, int], success: int) -> str:
    return (
        f"Choosing {choice} creates a {success}% success path with strong growth potential "
        f"({scores['career_growth']}/100) and a stress load of {scores['stress']}/100. "
        "The result depends less on motivation and more on consistent weekly execution."
    )


def _timeline(choice: str, profile: dict[str, Any], scores: dict[str, int]) -> list[dict[str, Any]]:
    income = int(profile.get("monthly_income") or 0)
    factors = [1.05, 1.18, 1.75, 2.45]
    periods = ["6 Months Later", "1 Year Later", "3 Years Later", "5 Years Later"]
    return [
        {
            "period": period,
            "career_situation": _career_line(choice, period, scores),
            "income": f"INR {int(max(income, 25000) * factors[index]):,}/month potential range",
            "lifestyle": _lifestyle_line(scores, index),
            "emotional_state": _emotion_line(scores, index),
            "skills_acquired": _skills(choice, index),
            "lost_opportunities": _lost(choice, index),
        }
        for index, period in enumerate(periods)
    ]


def _career_line(choice: str, period: str, scores: dict[str, int]) -> str:
    if "6" in period:
        return f"You are still proving {choice}, building early traction and confronting the first reality checks."
    if "1 Year" in period:
        return f"{choice} has become part of your identity; the market feedback is clearer and your weak spots are visible."
    if "3" in period:
        return f"You have enough compounding skill to negotiate better roles, exams, clients, or ventures around {choice}."
    return f"The path has either matured into a durable advantage or revealed exactly where to pivot next."


def _lifestyle_line(scores: dict[str, int], index: int) -> str:
    if scores["stress"] > 70 and index < 2:
        return "Disciplined but compressed; weekends and comfort spending require boundaries."
    if scores["wealth"] > 72:
        return "More optionality, better tools, and less dependence on a single source of security."
    return "Stable but demanding; the gains are visible only if habits stay consistent."


def _emotion_line(scores: dict[str, int], index: int) -> str:
    if scores["regret"] > 65:
        return "You feel the cost of delay and wonder whether you waited too long."
    if scores["happiness"] > 72:
        return "You feel stretched, but the direction feels deeply yours."
    return "Your confidence rises slowly as evidence replaces imagination."


def _skills(choice: str, index: int) -> list[str]:
    pool = [
        ["Focused routine", "Market research", "Financial discipline"],
        ["Portfolio proof", "Communication", "Mentorship seeking"],
        ["Strategic positioning", "Negotiation", "Resilience under ambiguity"],
        ["Leadership", "Opportunity selection", "Long-term decision hygiene"],
    ]
    return [f"{skill} for {choice}" if skill == "Portfolio proof" else skill for skill in pool[index]]


def _lost(choice: str, index: int) -> list[str]:
    return [
        f"Time spent exploring alternatives outside {choice}",
        "Some short-term income flexibility",
        "Comfort of staying with the familiar",
    ][: index + 1]


def _letter(choice: str, profile: dict[str, Any], scores: dict[str, int]) -> str:
    age = int(profile.get("age") or 24) + 5
    return (
        "Dear Future Me,\n\n"
        f"I am writing from the version of life where we chose {choice}. I am {age} now, "
        "and the biggest surprise is that the decision itself mattered less than the way we kept promises after it. "
        f"The path was not effortless. Stress reached {scores['stress']}/100 at times, but it taught us to separate fear from signal. "
        "We gained a future that feels earned, not accidental.\n\n"
        "Please remember this: clarity did not arrive before action. It arrived because we acted, measured, adjusted, and kept going.\n\n"
        "With gratitude,\nFuture You"
    )


def _opportunity_costs(choice: str, future_id: str) -> list[str]:
    if future_id == "C":
        return ["Momentum in both active options", "Identity-level learning", "A stronger professional network"]
    return [
        f"Deep exposure to the path not chosen while pursuing {choice}",
        "Short-term certainty and familiar routines",
        "The emotional comfort of keeping every option open",
    ]


def _alternate_life(choice: str, future_id: str) -> str:
    if future_id == "C":
        return "In the accidental alternate life, you finally choose a direction after watching peers compound for a year."
    return (
        f"If you had not chosen {choice}, life may have felt calmer initially, but you would keep revisiting the same question "
        "whenever a friend, exam result, promotion, or startup story reminded you of the path."
    )


def _headlines(choice: str, scores: dict[str, int]) -> list[str]:
    return [
        f"2030: {choice} Bet Turns Into a Defining Career Chapter",
        f"2031: Former Doubter Builds Momentum With {scores['career_growth']}/100 Growth Score",
        "2032: A Five-Year Decision Journal Reveals the Cost of Timely Action",
    ]


def _bias_profile(profile: dict[str, Any], signal: dict[str, int]) -> dict[str, Any]:
    risk_aversion = max(12, 100 - signal["risk"])
    short_term = 62 if int(profile.get("savings") or 0) < int(profile.get("monthly_income") or 1) * 3 else 38
    return {
        "risk_aversion": risk_aversion,
        "fear_of_failure": _stable_int(str(profile) + "fear", 35, 78),
        "analysis_paralysis": _stable_int(str(profile) + "analysis", 28, 82),
        "overconfidence": _stable_int(str(profile) + "over", 18, 66),
        "short_term_thinking": short_term,
        "comfort_zone_bias": _stable_int(str(profile) + "comfort", 30, 80),
        "insights": [
            "You appear to value downside protection, so reversible experiments will help you move faster.",
            "Your decision quality improves when goals are converted into weekly evidence rather than abstract ambition.",
            "The biggest psychological risk is confusing temporary discomfort with a wrong path.",
        ],
    }


def _debate(option_a: str, option_b: str, profile: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"speaker": "Optimistic Advisor", "message": f"{option_a} could compound quickly if you turn your existing skills into visible proof."},
        {"speaker": "Skeptical Advisor", "message": f"{option_a} also needs runway. Motivation will not protect you from weak execution or market timing."},
        {"speaker": "Optimistic Advisor", "message": f"{option_b} may offer a cleaner identity shift and a stronger long-term narrative."},
        {"speaker": "Skeptical Advisor", "message": f"{option_b} can become expensive if timelines stretch and your support system is not aligned."},
        {"speaker": "Optimistic Advisor", "message": "The right move is not blind courage; it is a small bet with fast feedback."},
        {"speaker": "Skeptical Advisor", "message": "Set kill criteria now. Otherwise you may call persistence what is really avoidance."},
    ]


def _normalize_simulation(data: dict[str, Any], decision: str, option_a: str, option_b: str, profile: dict[str, Any]) -> dict[str, Any]:
    fallback = _generate_locally(decision, option_a, option_b, profile)
    merged = deepcopy(fallback)
    merged.update({k: v for k, v in data.items() if v not in (None, "", [])})
    if len(merged.get("futures", [])) != 3:
        merged["futures"] = fallback["futures"]
    for future in merged["futures"]:
        future.setdefault("scores", {})
        for key in SCORE_KEYS:
            future["scores"].setdefault(key, 50)
    return merged
