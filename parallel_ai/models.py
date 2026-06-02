from __future__ import annotations

from dataclasses import dataclass
from typing import Any


SCORE_KEYS = [
    "wealth",
    "happiness",
    "stress",
    "career_growth",
    "regret",
    "opportunity",
]


PROFILE_FIELDS = [
    "age",
    "education",
    "profession",
    "experience",
    "monthly_income",
    "savings",
    "skills",
    "career_goals",
    "family_responsibilities",
    "risk_tolerance",
    "time_available",
]


@dataclass
class Profile:
    age: int
    education: str
    profession: str
    experience: str
    monthly_income: int
    savings: int
    skills: str
    career_goals: str
    family_responsibilities: str
    risk_tolerance: str
    time_available: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "age": self.age,
            "education": self.education,
            "profession": self.profession,
            "experience": self.experience,
            "monthly_income": self.monthly_income,
            "savings": self.savings,
            "skills": self.skills,
            "career_goals": self.career_goals,
            "family_responsibilities": self.family_responsibilities,
            "risk_tolerance": self.risk_tolerance,
            "time_available": self.time_available,
        }


def default_profile() -> dict[str, Any]:
    return {
        "age": 24,
        "education": "",
        "profession": "",
        "experience": "",
        "monthly_income": 50000,
        "savings": 200000,
        "skills": "",
        "career_goals": "",
        "family_responsibilities": "",
        "risk_tolerance": "Moderate",
        "time_available": "10-15 hours/week",
    }

