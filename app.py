from __future__ import annotations

import json
from typing import Any

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from parallel_ai.models import default_profile
from parallel_ai.services.database import delete_decision, list_decisions, save_decision
from parallel_ai.services.pdf_report import build_pdf_report
from parallel_ai.services.pendo import track as pendo_track
from parallel_ai.services.simulation import generate_simulation
from parallel_ai.ui.charts import comparison_bar, dashboard_bar, gauge, opportunity_cost_chart, radar
from parallel_ai.ui.styles import CSS


st.set_page_config(
    page_title="Parallel AI",
    page_icon="PA",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(CSS, unsafe_allow_html=True)


def init_state() -> None:
    st.session_state.setdefault("profile", default_profile())
    st.session_state.setdefault("simulation", None)
    st.session_state.setdefault("decision", "AI Engineer vs UPSC")
    st.session_state.setdefault("option_a", "AI Engineer")
    st.session_state.setdefault("option_b", "UPSC")
    st.session_state.setdefault("show_app", False)


def html_card(body: str, class_name: str = "premium-card") -> None:
    st.markdown(f"<div class='{class_name}'>{body}</div>", unsafe_allow_html=True)


def landing() -> None:
    st.markdown(
        """
        <section class="hero">
          <div>
            <div class="small-muted">Parallel AI Decision Intelligence</div>
            <h1>See The Lives You Don't Live</h1>
            <p>Explore multiple futures before making life-changing decisions. Compare career, wealth, happiness, stress, regret, and opportunity before you commit.</p>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    cta, example = st.columns([1, 2])
    with cta:
        if st.button("Simulate My Future", type="primary", use_container_width=True):
            st.session_state.show_app = True
            st.rerun()
    with example:
        html_card(
            "<b>Example simulations:</b> AI Engineer vs UPSC · Startup vs Job · MBA vs Work Experience · India vs Abroad"
        )
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        html_card("<h3>Future Timelines</h3><p>See 6-month, 1-year, 3-year, and 5-year scenarios for each path.</p>")
    with col2:
        html_card("<h3>Regret Intelligence</h3><p>Quantify financial, career, lifestyle, family, and opportunity regret.</p>")
    with col3:
        html_card("<h3>Reality Check</h3><p>Watch optimistic and skeptical advisors pressure-test your assumptions.</p>")
    st.subheader("What early users say")
    t1, t2, t3 = st.columns(3)
    with t1:
        html_card("“It turned my vague fear into a concrete plan.”<br><span class='small-muted'>Career switcher</span>")
    with t2:
        html_card("“The future letter hit harder than any spreadsheet.”<br><span class='small-muted'>MBA applicant</span>")
    with t3:
        html_card("“Finally, an AI tool that makes tradeoffs visible.”<br><span class='small-muted'>Founder</span>")


def sidebar() -> None:
    st.sidebar.title("Parallel AI")
    st.sidebar.caption("Decision intelligence for lives you have not lived yet.")
    if st.sidebar.button("New Simulation", use_container_width=True):
        st.session_state.simulation = None
        st.session_state.show_app = True
        st.rerun()
    if st.sidebar.button("Landing Page", use_container_width=True):
        st.session_state.show_app = False
        st.rerun()
    st.sidebar.divider()
    st.sidebar.info("Set OPENAI_API_KEY for GPT-4o generation. Without it, the app runs a deterministic local simulation engine.")


def decision_form() -> None:
    st.title("Simulate a Life Decision")
    st.caption("Start with the two active paths you are considering. Parallel AI will also model the cost of taking no action.")
    st.session_state.decision = st.text_area(
        "Decision",
        value=st.session_state.decision,
        height=100,
        placeholder="Example: Should I become an AI engineer or prepare for UPSC?",
    )
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.option_a = st.text_input("Option A", value=st.session_state.option_a)
    with col2:
        st.session_state.option_b = st.text_input("Option B", value=st.session_state.option_b)


def profile_wizard() -> None:
    st.subheader("Profile")
    st.caption("These answers make the futures more personal and less generic.")
    profile = st.session_state.profile
    tab1, tab2, tab3 = st.tabs(["Identity", "Money", "Goals"])
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            profile["age"] = st.number_input("Age", 16, 75, int(profile["age"]))
            profile["education"] = st.text_input("Education", value=profile["education"], placeholder="B.Tech, B.Com, MBA...")
        with c2:
            profile["profession"] = st.text_input("Current profession", value=profile["profession"], placeholder="Student, Software Engineer...")
            profile["experience"] = st.text_input("Experience", value=profile["experience"], placeholder="2 years in support, fresher...")
    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            profile["monthly_income"] = st.number_input("Monthly income (INR)", 0, 5000000, int(profile["monthly_income"]), step=5000)
        with c2:
            profile["savings"] = st.number_input("Savings (INR)", 0, 100000000, int(profile["savings"]), step=10000)
    with tab3:
        profile["skills"] = st.text_area("Existing skills", value=profile["skills"], placeholder="Python, sales, writing, public speaking...")
        profile["career_goals"] = st.text_area("Career goals", value=profile["career_goals"], placeholder="Financial freedom, impact, stable government role...")
        c1, c2 = st.columns(2)
        with c1:
            profile["family_responsibilities"] = st.text_input("Family responsibilities", value=profile["family_responsibilities"])
            profile["risk_tolerance"] = st.select_slider("Risk tolerance", ["Low", "Moderate", "High"], value=profile["risk_tolerance"])
        with c2:
            profile["time_available"] = st.selectbox(
                "Time available",
                ["Less than 5 hours/week", "5-10 hours/week", "10-15 hours/week", "20+ hours/week", "Full-time"],
                index=["Less than 5 hours/week", "5-10 hours/week", "10-15 hours/week", "20+ hours/week", "Full-time"].index(profile["time_available"])
                if profile["time_available"] in ["Less than 5 hours/week", "5-10 hours/week", "10-15 hours/week", "20+ hours/week", "Full-time"]
                else 2,
            )


def simulate_button() -> None:
    disabled = not st.session_state.decision.strip() or not st.session_state.option_a.strip() or not st.session_state.option_b.strip()
    if st.button("Generate Parallel Futures", type="primary", disabled=disabled, use_container_width=True):
        with st.spinner("Simulating future timelines, regret, bias profile, and advisor debate..."):
            st.session_state.simulation = generate_simulation(
                st.session_state.decision,
                st.session_state.option_a,
                st.session_state.option_b,
                st.session_state.profile,
            )
        sim = st.session_state.simulation
        profile = st.session_state.profile
        pendo_track("simulation_generated", properties={
            "decision_text": st.session_state.decision[:200],
            "option_a": st.session_state.option_a[:100],
            "option_b": st.session_state.option_b[:100],
            "generation_source": "fallback" if sim.get("api_warning") else "openai",
            "confidence_score": sim.get("confidence_score", 0),
            "profile_age": profile.get("age", 0),
            "profile_profession": str(profile.get("profession", ""))[:80],
            "profile_risk_tolerance": str(profile.get("risk_tolerance", "")),
            "profile_time_available": str(profile.get("time_available", "")),
            "has_api_warning": bool(sim.get("api_warning")),
            "futures_count": len(sim.get("futures", [])),
        })
        # Track profile completeness at simulation time
        pendo_track("profile_completed", properties={
            "fields_completed_count": sum(1 for f in [
                profile.get("education"), profile.get("profession"),
                profile.get("experience"), profile.get("skills"),
                profile.get("career_goals"), profile.get("family_responsibilities"),
            ] if f),
            "has_education": bool(profile.get("education")),
            "has_profession": bool(profile.get("profession")),
            "has_experience": bool(profile.get("experience")),
            "has_skills": bool(profile.get("skills")),
            "has_career_goals": bool(profile.get("career_goals")),
            "has_family_responsibilities": bool(profile.get("family_responsibilities")),
            "monthly_income_provided": bool(profile.get("monthly_income")),
            "savings_provided": bool(profile.get("savings")),
            "risk_tolerance": str(profile.get("risk_tolerance", "")),
            "time_available": str(profile.get("time_available", "")),
        })
        st.success("Three futures generated.")


def metric_strip(sim: dict[str, Any]) -> None:
    dashboard = sim.get("life_dashboard", {})
    values = [
        ("Confidence", sim.get("confidence_score", 0)),
        ("Potential", dashboard.get("future_potential_score", 0)),
        ("Career", dashboard.get("career_outlook", 0)),
        ("Financial", dashboard.get("financial_outlook", 0)),
        ("Wellness", dashboard.get("mental_wellness_outlook", 0)),
    ]
    cols = st.columns(len(values))
    for col, (label, value) in zip(cols, values):
        with col:
            html_card(f"<div class='metric-title'>{label}</div><div class='metric-value'>{value}</div>")


def render_results() -> None:
    sim = st.session_state.simulation
    if not sim:
        return
    if sim.get("api_warning"):
        st.warning(sim["api_warning"])
    st.divider()
    st.subheader("Decision Intelligence")
    st.write(sim.get("executive_summary", ""))
    metric_strip(sim)

    tabs = st.tabs(
        [
            "Parallel Universe",
            "Timelines",
            "Regret",
            "Reality Check",
            "Bias",
            "Life Dashboard",
            "Report & Journal",
        ]
    )
    with tabs[0]:
        render_parallel_universe(sim)
    with tabs[1]:
        render_timelines(sim)
    with tabs[2]:
        render_regret(sim)
    with tabs[3]:
        render_debate(sim)
    with tabs[4]:
        render_bias(sim)
    with tabs[5]:
        render_dashboard(sim)
    with tabs[6]:
        render_report(sim)


def render_parallel_universe(sim: dict[str, Any]) -> None:
    st.plotly_chart(comparison_bar(sim.get("futures", [])), use_container_width=True)
    cols = st.columns(3)
    for col, future in zip(cols, sim.get("futures", [])):
        with col:
            scores = future.get("scores", {})
            html_card(
                f"""
                <h3>{future.get('name')}</h3>
                <p><b>{future.get('choice')}</b></p>
                <p>{future.get('summary')}</p>
                <div class='small-muted'>Success probability</div>
                <div class='metric-value'>{future.get('success_probability', 0)}%</div>
                """
            )
            st.progress(scores.get("wealth", 0), text="Wealth")
            st.progress(scores.get("happiness", 0), text="Happiness")
            st.progress(scores.get("regret", 0), text="Regret")
            with st.expander("Opportunity costs"):
                for item in future.get("opportunity_costs", []):
                    st.write(f"- {item}")
            with st.expander("Alternate life"):
                st.write(future.get("alternate_life", ""))
            with st.expander("Future news headlines"):
                for headline in future.get("headlines", []):
                    st.markdown(f"<div class='newspaper'>{headline}</div>", unsafe_allow_html=True)


def render_timelines(sim: dict[str, Any]) -> None:
    for future in sim.get("futures", []):
        st.subheader(f"{future.get('name')}: {future.get('choice')}")
        for item in future.get("timeline", []):
            with st.expander(item.get("period", "Future moment"), expanded=item.get("period") == "6 Months Later"):
                st.markdown(f"<span class='timeline-dot'></span><b>{item.get('career_situation')}</b>", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Income:** {item.get('income')}")
                    st.write(f"**Lifestyle:** {item.get('lifestyle')}")
                    st.write(f"**Emotional state:** {item.get('emotional_state')}")
                with c2:
                    st.write("**Skills acquired**")
                    for skill in item.get("skills_acquired", []):
                        st.write(f"- {skill}")
                    st.write("**Lost opportunities**")
                    for lost in item.get("lost_opportunities", []):
                        st.write(f"- {lost}")
        st.markdown("#### Letter From Future You")
        letter = future.get("future_letter", "")
        st.text_area(f"Future letter {future.get('id')}", value=letter, height=260, label_visibility="collapsed")
        copy_button(letter, f"Copy letter {future.get('id')}")
        if st.download_button(
            "Download Letter",
            data=letter,
            file_name=f"future_{future.get('id', 'letter')}_letter.txt",
            mime="text/plain",
            key=f"download-letter-{future.get('id')}",
        ):
            pendo_track("future_letter_downloaded", properties={
                "future_id": str(future.get("id", "")),
                "future_name": str(future.get("name", ""))[:80],
                "future_choice": str(future.get("choice", ""))[:100],
                "decision_text": st.session_state.decision[:200],
                "letter_length": len(letter),
            })
        st.divider()


def copy_button(text: str, label: str) -> None:
    escaped = json.dumps(text)
    components.html(
        f"""
        <button onclick='navigator.clipboard.writeText({escaped})'
          style='border:1px solid #cbd5e1;border-radius:8px;padding:8px 12px;background:white;font-weight:700;cursor:pointer;'>
          {label}
        </button>
        """,
        height=44,
    )


def render_regret(sim: dict[str, Any]) -> None:
    regret = sim.get("regret_analysis", {})
    c1, c2 = st.columns([1, 1])
    with c1:
        st.plotly_chart(gauge(regret.get("overall", 0), "Overall Regret", "#ef4444"), use_container_width=True)
    with c2:
        values = {k.title(): regret.get(k, 0) for k in ["financial", "career", "lifestyle", "family", "opportunity"]}
        st.plotly_chart(radar(values, "Regret Profile"), use_container_width=True)
    st.write(regret.get("explanation", ""))
    for key in ["financial", "career", "lifestyle", "family", "opportunity"]:
        st.progress(regret.get(key, 0), text=f"{key.title()} regret")
    st.plotly_chart(opportunity_cost_chart(sim.get("futures", [])), use_container_width=True)


def render_debate(sim: dict[str, Any]) -> None:
    st.subheader("Reality Check Mode")
    st.caption("Two advisor agents challenge the same decision from opposite directions.")
    for message in sim.get("advisor_debate", []):
        speaker = message.get("speaker", "")
        klass = "chat-optimistic" if "Optimistic" in speaker else "chat-skeptical"
        st.markdown(
            f"<div class='{klass}'><b>{speaker}</b><br>{message.get('message')}</div>",
            unsafe_allow_html=True,
        )
    challenge = st.text_input("Ask the skeptical advisor a follow-up", placeholder="What am I underestimating?")
    if challenge:
        pendo_track("advisor_followup_asked", properties={
            "question_text": challenge[:200],
            "question_length": len(challenge),
            "decision_text": st.session_state.decision[:200],
            "option_a": st.session_state.option_a[:100],
            "option_b": st.session_state.option_b[:100],
        })
        st.info("Skeptical Advisor: Re-check whether your timeline, money runway, and emotional stamina all survive the same worst-case month.")


def render_bias(sim: dict[str, Any]) -> None:
    bias = sim.get("bias_profile", {})
    values = {key.replace("_", " ").title(): bias.get(key, 0) for key in [
        "risk_aversion",
        "fear_of_failure",
        "analysis_paralysis",
        "overconfidence",
        "short_term_thinking",
        "comfort_zone_bias",
    ]}
    st.plotly_chart(radar(values, "Personal Bias Detector"), use_container_width=True)
    for insight in bias.get("insights", []):
        html_card(insight)


def render_dashboard(sim: dict[str, Any]) -> None:
    dashboard = sim.get("life_dashboard", {})
    c1, c2 = st.columns([1, 1])
    with c1:
        st.plotly_chart(dashboard_bar(dashboard), use_container_width=True)
    with c2:
        st.plotly_chart(gauge(dashboard.get("future_potential_score", 0), "Future Potential", "#14b8a6"), use_container_width=True)
        st.write(sim.get("confidence_explanation", ""))
    st.subheader("Recommendations")
    for recommendation in sim.get("recommendations", []):
        st.write(f"- {recommendation}")


def render_report(sim: dict[str, Any]) -> None:
    notes = st.text_area("Decision journal notes", placeholder="What did this simulation make clear? What will you do in the next 7 days?")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Save Decision", use_container_width=True):
            row_id = save_decision(st.session_state.decision, st.session_state.option_a, st.session_state.option_b, st.session_state.profile, sim, notes)
            pendo_track("decision_saved_to_journal", properties={
                "decision_id": row_id,
                "decision_text": st.session_state.decision[:200],
                "option_a": st.session_state.option_a[:100],
                "option_b": st.session_state.option_b[:100],
                "confidence_score": sim.get("confidence_score", 0),
                "overall_regret_score": sim.get("regret_analysis", {}).get("overall", 0),
                "has_notes": bool(notes),
                "notes_length": len(notes),
            })
            st.success(f"Saved decision #{row_id}.")
    with c2:
        pdf = build_pdf_report(st.session_state.decision, st.session_state.profile, sim)
        if st.download_button(
            "Download PDF Report",
            data=pdf,
            file_name="parallel_ai_decision_report.pdf",
            mime="application/pdf",
            use_container_width=True,
        ):
            pendo_track("pdf_report_downloaded", properties={
                "decision_text": st.session_state.decision[:200],
                "option_a": st.session_state.option_a[:100],
                "option_b": st.session_state.option_b[:100],
                "confidence_score": sim.get("confidence_score", 0),
                "futures_count": len(sim.get("futures", [])),
                "profile_age": st.session_state.profile.get("age", 0),
                "profile_profession": str(st.session_state.profile.get("profession", ""))[:80],
            })
    with st.expander("Raw structured output"):
        st.json(sim)


def render_history() -> None:
    st.subheader("Decision Journal")
    rows = list_decisions()
    if not rows:
        st.caption("Saved simulations will appear here.")
        return
    table = pd.DataFrame(
        [
            {
                "ID": row["id"],
                "Date": row["created_at"],
                "Decision": row["decision"],
                "Confidence": row["simulation"].get("confidence_score", 0),
                "Regret": row["simulation"].get("regret_analysis", {}).get("overall", 0),
            }
            for row in rows
        ]
    )
    st.dataframe(table, use_container_width=True, hide_index=True)
    selected = st.selectbox("Open saved decision", rows, format_func=lambda row: f"#{row['id']} · {row['decision']}")
    if selected:
        c1, c2 = st.columns([3, 1])
        with c1:
            st.write(selected.get("notes") or "No notes saved.")
            st.json(selected["simulation"])
        with c2:
            if st.button("Load Into Workspace", use_container_width=True):
                pendo_track("saved_decision_loaded", properties={
                    "loaded_decision_id": int(selected["id"]),
                    "decision_text": selected["decision"][:200],
                    "option_a": selected["option_a"][:100],
                    "option_b": selected["option_b"][:100],
                    "original_confidence_score": selected["simulation"].get("confidence_score", 0),
                    "original_regret_score": selected["simulation"].get("regret_analysis", {}).get("overall", 0),
                })
                st.session_state.decision = selected["decision"]
                st.session_state.option_a = selected["option_a"]
                st.session_state.option_b = selected["option_b"]
                st.session_state.profile = selected["profile"]
                st.session_state.simulation = selected["simulation"]
                st.session_state.show_app = True
                st.rerun()
            if st.button("Delete", use_container_width=True):
                pendo_track("decision_deleted", properties={
                    "deleted_decision_id": int(selected["id"]),
                    "decision_text": selected["decision"][:200],
                })
                delete_decision(int(selected["id"]))
                st.rerun()


def main() -> None:
    init_state()
    sidebar()
    if not st.session_state.show_app:
        landing()
        return
    workspace, history = st.tabs(["Simulator", "Journal"])
    with workspace:
        decision_form()
        profile_wizard()
        simulate_button()
        render_results()
    with history:
        render_history()


if __name__ == "__main__":
    main()

