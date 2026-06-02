from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


PALETTE = ["#2563eb", "#14b8a6", "#f59e0b", "#ef4444", "#8b5cf6", "#22c55e"]


def gauge(value: int, title: str, color: str = "#2563eb") -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            title={"text": title},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": color},
                "bgcolor": "rgba(255,255,255,0.08)",
                "steps": [
                    {"range": [0, 35], "color": "#fee2e2"},
                    {"range": [35, 70], "color": "#fef3c7"},
                    {"range": [70, 100], "color": "#dcfce7"},
                ],
            },
        )
    )
    fig.update_layout(height=260, margin=dict(l=20, r=20, t=35, b=15), paper_bgcolor="rgba(0,0,0,0)")
    return fig


def radar(values: dict[str, int], title: str) -> go.Figure:
    categories = list(values.keys())
    data = list(values.values())
    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=data + data[:1],
            theta=categories + categories[:1],
            fill="toself",
            line_color="#2563eb",
            fillcolor="rgba(37, 99, 235, 0.25)",
        )
    )
    fig.update_layout(
        title=title,
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        height=330,
        margin=dict(l=25, r=25, t=55, b=25),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def comparison_bar(futures: list[dict]) -> go.Figure:
    metrics = ["wealth", "happiness", "regret", "career_growth", "opportunity"]
    fig = go.Figure()
    for index, future in enumerate(futures):
        fig.add_trace(
            go.Bar(
                name=future.get("name", f"Future {index + 1}"),
                x=[metric.replace("_", " ").title() for metric in metrics],
                y=[future.get("scores", {}).get(metric, 0) for metric in metrics],
                marker_color=PALETTE[index],
            )
        )
    fig.update_layout(
        barmode="group",
        height=360,
        margin=dict(l=20, r=20, t=30, b=30),
        yaxis=dict(range=[0, 100]),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def dashboard_bar(dashboard: dict[str, int]) -> go.Figure:
    labels = [key.replace("_", " ").title() for key in dashboard.keys()]
    values = list(dashboard.values())
    fig = go.Figure(go.Bar(x=values, y=labels, orientation="h", marker_color=PALETTE))
    fig.update_layout(
        height=330,
        xaxis=dict(range=[0, 100]),
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def opportunity_cost_chart(futures: list[dict]) -> go.Figure:
    frame = pd.DataFrame(
        {
            "Future": [future.get("name") for future in futures],
            "Costs": [len(future.get("opportunity_costs", [])) * 25 for future in futures],
            "Regret": [future.get("scores", {}).get("regret", 0) for future in futures],
        }
    )
    fig = go.Figure()
    fig.add_trace(go.Bar(x=frame["Future"], y=frame["Costs"], name="Sacrifices", marker_color="#f59e0b"))
    fig.add_trace(go.Scatter(x=frame["Future"], y=frame["Regret"], name="Regret", mode="lines+markers", line=dict(color="#ef4444", width=3)))
    fig.update_layout(
        height=320,
        yaxis=dict(range=[0, 100]),
        margin=dict(l=20, r=20, t=35, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig

