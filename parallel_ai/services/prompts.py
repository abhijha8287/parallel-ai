SYSTEM_PROMPT = """
You are Parallel AI, a careful decision intelligence analyst.
Blend startup product strategy, career coaching, behavioral psychology,
personal finance reasoning, and realistic life planning.

Output must be specific, grounded, emotionally resonant, and practical.
Avoid certainty. Mention assumptions and risks. Use Indian context when the
profile or income suggests it, but do not force it.
"""


def simulation_prompt(decision: str, option_a: str, option_b: str, profile: dict) -> str:
    return f"""
Create a complete future simulation for this decision.

Decision: {decision}
Option A: {option_a}
Option B: {option_b}
Option C: No action taken / current path continues

User profile:
{profile}

Return JSON matching this shape:
{{
  "executive_summary": "short premium product-style summary",
  "recommendation": "clear but nuanced recommendation",
  "confidence_score": 0-100,
  "confidence_explanation": "why",
  "futures": [
    {{
      "id": "A",
      "name": "Future A",
      "choice": "chosen option",
      "success_probability": 0-100,
      "scores": {{
        "wealth": 0-100,
        "happiness": 0-100,
        "stress": 0-100,
        "career_growth": 0-100,
        "regret": 0-100,
        "opportunity": 0-100
      }},
      "summary": "realistic explanation",
      "timeline": [
        {{
          "period": "6 Months Later",
          "career_situation": "...",
          "income": "...",
          "lifestyle": "...",
          "emotional_state": "...",
          "skills_acquired": ["..."],
          "lost_opportunities": ["..."]
        }}
      ],
      "future_letter": "Dear Future Me...",
      "opportunity_costs": ["..."],
      "alternate_life": "...",
      "headlines": ["2030: ...", "2031: ..."]
    }}
  ],
  "regret_analysis": {{
    "financial": 0-100,
    "career": 0-100,
    "lifestyle": 0-100,
    "family": 0-100,
    "opportunity": 0-100,
    "overall": 0-100,
    "explanation": "..."
  }},
  "bias_profile": {{
    "risk_aversion": 0-100,
    "fear_of_failure": 0-100,
    "analysis_paralysis": 0-100,
    "overconfidence": 0-100,
    "short_term_thinking": 0-100,
    "comfort_zone_bias": 0-100,
    "insights": ["..."]
  }},
  "advisor_debate": [
    {{"speaker": "Optimistic Advisor", "message": "..."}},
    {{"speaker": "Skeptical Advisor", "message": "..."}}
  ],
  "life_dashboard": {{
    "career_outlook": 0-100,
    "financial_outlook": 0-100,
    "learning_outlook": 0-100,
    "relationship_outlook": 0-100,
    "mental_wellness_outlook": 0-100,
    "future_potential_score": 0-100
  }},
  "recommendations": ["..."]
}}

Create exactly three futures: A, B, C.
Each future must have timeline entries for exactly:
6 Months Later, 1 Year Later, 3 Years Later, 5 Years Later.
"""

