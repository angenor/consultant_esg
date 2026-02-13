"""
Génération de graphiques matplotlib pour les rapports PDF.
Chaque fonction retourne une image encodée en base64 (PNG).
"""

import base64
import io
import math

import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# ── Style global ──────────────────────────────────────────
_COLORS = {
    "primary": "#059669",
    "primary_light": "#10b981",
    "secondary": "#0d9488",
    "accent": "#d97706",
    "danger": "#dc2626",
    "gray": "#94a3b8",
    "bg": "#f8fafc",
    "E": "#059669",
    "S": "#0ea5e9",
    "G": "#8b5cf6",
}

_PIE_PALETTE = ["#059669", "#0ea5e9", "#8b5cf6", "#d97706", "#ec4899", "#f43f5e", "#64748b"]


def _fig_to_base64(fig: plt.Figure) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def generate_radar_chart(
    scores_piliers: dict[str, float],
    title: str = "Profil ESG",
) -> str:
    """
    Radar chart pour les piliers ESG.
    scores_piliers: {"Environnement": 72, "Social": 65, "Gouvernance": 80}
    """
    labels = list(scores_piliers.keys())
    values = list(scores_piliers.values())
    n = len(labels)

    if n < 3:
        # Need at least 3 axes for radar
        while len(labels) < 3:
            labels.append("")
            values.append(0)
        n = len(labels)

    angles = [i * 2 * math.pi / n for i in range(n)]
    values_closed = values + [values[0]]
    angles_closed = angles + [angles[0]]

    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
    ax.set_theta_offset(math.pi / 2)
    ax.set_theta_direction(-1)

    ax.set_xticks(angles)
    ax.set_xticklabels(labels, fontsize=10, fontweight="bold")
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=7, color=_COLORS["gray"])
    ax.yaxis.grid(True, color="#e2e8f0", linewidth=0.5)
    ax.xaxis.grid(True, color="#e2e8f0", linewidth=0.5)

    ax.plot(angles_closed, values_closed, "o-", color=_COLORS["primary"], linewidth=2, markersize=6)
    ax.fill(angles_closed, values_closed, alpha=0.15, color=_COLORS["primary_light"])

    ax.set_title(title, fontsize=13, fontweight="bold", color="#1e293b", pad=20)
    fig.patch.set_facecolor("white")

    return _fig_to_base64(fig)


def generate_bar_chart(
    data: dict[str, float],
    title: str = "",
    ylabel: str = "Score",
    horizontal: bool = False,
    color: str | None = None,
) -> str:
    """
    Bar chart simple.
    data: {"Label1": value1, "Label2": value2, ...}
    """
    labels = list(data.keys())
    values = list(data.values())
    colors = [color or _COLORS["primary"]] * len(labels)

    fig, ax = plt.subplots(figsize=(7, 4))

    if horizontal:
        bars = ax.barh(labels, values, color=colors, height=0.5, edgecolor="white")
        ax.set_xlabel(ylabel, fontsize=9, color=_COLORS["gray"])
        ax.invert_yaxis()
        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                    f"{val:.0f}", va="center", fontsize=9, color="#1e293b")
    else:
        bars = ax.bar(labels, values, color=colors, width=0.5, edgecolor="white")
        ax.set_ylabel(ylabel, fontsize=9, color=_COLORS["gray"])
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                    f"{val:.0f}", ha="center", fontsize=9, color="#1e293b")

    if title:
        ax.set_title(title, fontsize=12, fontweight="bold", color="#1e293b")

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(colors=_COLORS["gray"], labelsize=9)
    fig.patch.set_facecolor("white")
    fig.tight_layout()

    return _fig_to_base64(fig)


def generate_pie_chart(
    data: dict[str, float],
    title: str = "",
) -> str:
    """
    Pie chart.
    data: {"Énergie": 45, "Transport": 30, "Déchets": 25}
    """
    labels = list(data.keys())
    values = list(data.values())
    colors = _PIE_PALETTE[: len(labels)]

    fig, ax = plt.subplots(figsize=(6, 5))
    wedges, texts, autotexts = ax.pie(
        values,
        labels=labels,
        colors=colors,
        autopct="%1.1f%%",
        startangle=90,
        pctdistance=0.75,
        wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2),
    )
    for text in texts:
        text.set_fontsize(9)
    for autotext in autotexts:
        autotext.set_fontsize(8)
        autotext.set_color("white")
        autotext.set_fontweight("bold")

    if title:
        ax.set_title(title, fontsize=12, fontweight="bold", color="#1e293b", pad=15)

    fig.patch.set_facecolor("white")
    fig.tight_layout()

    return _fig_to_base64(fig)


def generate_evolution_chart(
    dates: list[str],
    scores: dict[str, list[float]],
    title: str = "Évolution des Scores",
    ylabel: str = "Score",
) -> str:
    """
    Line chart pour l'évolution temporelle.
    dates: ["2024-01", "2024-06", "2025-01"]
    scores: {"Global": [55, 62, 71], "E": [50, 60, 70], ...}
    """
    fig, ax = plt.subplots(figsize=(7, 4))

    line_colors = {
        "Global": _COLORS["primary"],
        "E": _COLORS["E"],
        "S": _COLORS["S"],
        "G": _COLORS["G"],
    }

    for label, vals in scores.items():
        color = line_colors.get(label, _COLORS["gray"])
        ax.plot(dates, vals, "o-", label=label, color=color, linewidth=2, markersize=5)

    ax.set_ylabel(ylabel, fontsize=9, color=_COLORS["gray"])
    ax.set_title(title, fontsize=12, fontweight="bold", color="#1e293b")
    ax.legend(loc="lower right", fontsize=8, framealpha=0.9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(colors=_COLORS["gray"], labelsize=8)
    ax.yaxis.grid(True, color="#e2e8f0", linewidth=0.5, alpha=0.7)

    plt.xticks(rotation=30, ha="right")
    fig.patch.set_facecolor("white")
    fig.tight_layout()

    return _fig_to_base64(fig)
