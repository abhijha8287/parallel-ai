from __future__ import annotations

from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_pdf_report(decision: str, profile: dict[str, Any], simulation: dict[str, Any]) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Hero", parent=styles["Title"], fontSize=24, textColor=colors.HexColor("#111827"), spaceAfter=14))
    styles.add(ParagraphStyle(name="Section", parent=styles["Heading2"], fontSize=14, textColor=colors.HexColor("#2563eb"), spaceBefore=12))
    styles.add(ParagraphStyle(name="Body", parent=styles["BodyText"], leading=14, fontSize=9.5))

    story: list[Any] = [
        Paragraph("Parallel AI Decision Report", styles["Hero"]),
        Paragraph(f"<b>Decision:</b> {decision}", styles["Body"]),
        Paragraph(simulation.get("executive_summary", ""), styles["Body"]),
        Spacer(1, 10),
        _metric_table(simulation),
    ]

    story.append(Paragraph("Future Paths", styles["Section"]))
    for future in simulation.get("futures", []):
        story.append(Paragraph(f"<b>{future.get('name')}:</b> {future.get('choice')}", styles["Body"]))
        story.append(Paragraph(future.get("summary", ""), styles["Body"]))
        scores = future.get("scores", {})
        rows = [["Wealth", "Happiness", "Stress", "Growth", "Regret", "Opportunity"]]
        rows.append([scores.get("wealth"), scores.get("happiness"), scores.get("stress"), scores.get("career_growth"), scores.get("regret"), scores.get("opportunity")])
        story.append(_table(rows))
        story.append(Spacer(1, 7))

    story.append(Paragraph("Future Letter", styles["Section"]))
    first_letter = simulation.get("futures", [{}])[0].get("future_letter", "")
    story.append(Paragraph(first_letter.replace("\n", "<br/>"), styles["Body"]))

    story.append(Paragraph("Bias Analysis", styles["Section"]))
    for insight in simulation.get("bias_profile", {}).get("insights", []):
        story.append(Paragraph(f"- {insight}", styles["Body"]))

    story.append(Paragraph("Recommendations", styles["Section"]))
    for recommendation in simulation.get("recommendations", []):
        story.append(Paragraph(f"- {recommendation}", styles["Body"]))

    doc.build(story)
    return buffer.getvalue()


def _metric_table(simulation: dict[str, Any]) -> Table:
    dashboard = simulation.get("life_dashboard", {})
    rows = [
        ["Confidence", "Potential", "Career", "Financial", "Wellness"],
        [
            simulation.get("confidence_score", 0),
            dashboard.get("future_potential_score", 0),
            dashboard.get("career_outlook", 0),
            dashboard.get("financial_outlook", 0),
            dashboard.get("mental_wellness_outlook", 0),
        ],
    ]
    return _table(rows)


def _table(rows: list[list[Any]]) -> Table:
    table = Table(rows, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eff6ff")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dbeafe")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table

