import io
import base64
import numpy as np
from typing import Any, Dict
from urllib.parse import quote

try:
    import matplotlib.pyplot as plt
except ImportError:  # pragma: no cover - dependency fallback
    plt = None

def _fig_to_base64(fig):
    """Converts a matplotlib figure to a base64 string."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', transparent=True, dpi=100)
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return f"data:image/png;base64,{img_str}"


def _svg_to_data_uri(svg: str) -> str:
    return f"data:image/svg+xml;utf8,{quote(svg)}"

def generate_risk_factor_chart(factors: dict):
    """
    factors: { "Age": 2.5, "Dependents": -1.0, ... }
    """
    if plt is None:
        bars = []
        max_abs = max((abs(float(v)) for v in factors.values()), default=1.0) or 1.0
        for idx, (label, raw_value) in enumerate(factors.items()):
            value = float(raw_value)
            width = int((abs(value) / max_abs) * 180)
            color = "#4caf50" if value >= 0 else "#f44336"
            y = 30 + idx * 34
            x = 220 - width if value < 0 else 220
            bars.append(
                f'<text x="8" y="{y + 14}" font-size="12" fill="#1f2937">{label}</text>'
                f'<rect x="{x}" y="{y}" width="{width}" height="16" fill="{color}" rx="3" />'
                f'<text x="410" y="{y + 13}" font-size="11" text-anchor="end" fill="#475569">{value:+.2f}</text>'
            )
        height = max(120, 40 + len(factors) * 34)
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="420" height="{height}" viewBox="0 0 420 {height}">'
            '<rect width="100%" height="100%" fill="white"/>'
            '<text x="8" y="18" font-size="14" font-weight="bold" fill="#0f172a">Risk Factor Contributions</text>'
            '<line x1="220" y1="24" x2="220" y2="{height_minus}" stroke="#94a3b8" stroke-width="1"/>'
            f'{"".join(bars)}'
            '</svg>'
        ).replace("{height_minus}", str(height - 10))
        return _svg_to_data_uri(svg)

    labels = list(factors.keys())
    values = list(factors.values())
    
    fig, ax = plt.subplots(figsize=(6, 3))
    colors = ['#4caf50' if v >= 0 else '#f44336' for v in values]
    
    ax.barh(labels, values, color=colors)
    ax.set_xlabel('Contribution to Score')
    ax.set_title('Risk Factor Contributions')
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    
    return _fig_to_base64(fig)

def generate_sensitivity_chart(data: Any):
    """
    Generates a SIP-vs-success-probability sensitivity chart.
    Falls back to a simple horizontal gauge when detailed sensitivity inputs
    are not available.
    """
    if plt is None and isinstance(data, dict) and data.get("sips") and data.get("probabilities"):
        sips = data.get("sips", [])
        probabilities = data.get("probabilities", [])
        min_sip = min(sips)
        max_sip = max(sips)
        points = []
        for sip, prob in zip(sips, probabilities):
            x = 40 if max_sip == min_sip else 40 + ((sip - min_sip) / (max_sip - min_sip)) * 320
            y = 210 - (float(prob) / 100.0) * 160
            points.append((x, y, sip, prob))
        polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y, _, _ in points)
        current_x, current_y, _, current_prob = points[0]
        svg = [
            '<svg xmlns="http://www.w3.org/2000/svg" width="420" height="240" viewBox="0 0 420 240">',
            '<rect width="100%" height="100%" fill="white"/>',
            '<text x="12" y="18" font-size="14" font-weight="bold" fill="#0f172a">Sensitivity Analysis</text>',
            '<line x1="40" y1="210" x2="370" y2="210" stroke="#94a3b8"/>',
            '<line x1="40" y1="30" x2="40" y2="210" stroke="#94a3b8"/>',
            '<line x1="40" y1="82" x2="370" y2="82" stroke="#ef4444" stroke-dasharray="5,4"/>',
            '<text x="374" y="86" font-size="10" fill="#ef4444">80%</text>',
            f'<polyline fill="none" stroke="#1565c0" stroke-width="3" points="{polyline}"/>',
        ]
        for x, y, sip, prob in points:
            svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#1565c0"/>')
        svg.extend(
            [
                f'<circle cx="{current_x:.1f}" cy="{current_y:.1f}" r="6" fill="#16a34a"/>',
                f'<text x="{current_x + 8:.1f}" y="{current_y - 8:.1f}" font-size="10" fill="#16a34a">Current</text>',
                '<text x="160" y="232" font-size="11" fill="#475569">Monthly SIP Amount</text>',
                '<text x="6" y="30" font-size="11" fill="#475569">100%</text>',
                '<text x="12" y="210" font-size="11" fill="#475569">0%</text>',
                f'<text x="40" y="226" font-size="10" fill="#475569">₹{min_sip:,.0f}</text>',
                f'<text x="330" y="226" font-size="10" fill="#475569">₹{max_sip:,.0f}</text>',
                '</svg>',
            ]
        )
        return _svg_to_data_uri("".join(svg))

    if plt is None:
        success_prob = float(data or 0.0)
        color = "#4caf50" if success_prob >= 80 else ("#ff9800" if success_prob >= 50 else "#f44336")
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="420" height="72" viewBox="0 0 420 72">'
            '<rect width="100%" height="100%" fill="white"/>'
            '<rect x="16" y="24" width="388" height="18" rx="9" fill="#e5e7eb"/>'
            f'<rect x="16" y="24" width="{3.88 * success_prob:.1f}" height="18" rx="9" fill="{color}"/>'
            f'<text x="210" y="17" text-anchor="middle" font-size="13" fill="#0f172a">Sensitivity / Confidence: {success_prob:.0f}%</text>'
            '</svg>'
        )
        return _svg_to_data_uri(svg)

    if isinstance(data, dict) and data.get("sips") and data.get("probabilities"):
        sips = data.get("sips", [])
        probabilities = data.get("probabilities", [])
        current_probability = float(data.get("current_probability", 0.0))
        current_sip = float(sips[0]) if sips else 0.0

        fig, ax = plt.subplots(figsize=(6.5, 3.5))
        ax.plot(sips, probabilities, marker="o", color="#1565c0", linewidth=2)
        ax.axhline(80, color="#f44336", linestyle="--", linewidth=1.5)
        ax.scatter([current_sip], [current_probability], color="#2e7d32", s=70, zorder=3)
        ax.annotate(
            "Current",
            (current_sip, current_probability),
            textcoords="offset points",
            xytext=(6, 8),
            fontsize=9,
            color="#2e7d32",
        )
        ax.set_xlabel("Monthly SIP Amount (₹)")
        ax.set_ylabel("Success Probability %")
        ax.set_title("Sensitivity Analysis")
        ax.set_ylim(0, 100)
        ax.grid(alpha=0.3, linestyle="--")
        return _fig_to_base64(fig)

    success_prob = float(data or 0.0)
    fig, ax = plt.subplots(figsize=(4, 0.8))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 1)
    ax.barh([0.5], [100], color="#eee", height=0.6)
    color = "#4caf50" if success_prob >= 80 else ("#ff9800" if success_prob >= 50 else "#f44336")
    ax.barh([0.5], [success_prob], color=color, height=0.6)
    ax.text(
        success_prob / 2 if success_prob > 0 else 8,
        0.5,
        f"{success_prob:.0f}%",
        va="center",
        ha="center",
        color="white" if success_prob > 15 else "#333",
        fontweight="bold",
    )
    ax.axis("off")
    return _fig_to_base64(fig)

def generate_score_gauges(scores: Dict[str, float]):
    """
    scores: { "Risk": 6.5, "Diversification": 9.2, ... }
    Generates 5 mini-gauges (or bars) in a single row.
    """
    if plt is None:
        cells = []
        for idx, (name, val) in enumerate(scores.items()):
            scale = 10 if name not in {"AI Market", "Market Stability", "Goal Confidence"} else 100
            norm_val = (float(val) / scale) * 100 if scale else 0
            color = "#4caf50" if norm_val >= 80 else ("#ff9800" if norm_val >= 50 else "#f44336")
            x = 18 + idx * 192
            display = f"{val:.1f}" if scale == 10 else f"{val:.0f}%"
            cells.append(
                f'<circle cx="{x + 54}" cy="56" r="34" fill="none" stroke="#e5e7eb" stroke-width="12"/>'
                f'<circle cx="{x + 54}" cy="56" r="34" fill="none" stroke="{color}" stroke-width="12" '
                f'stroke-dasharray="{2.14 * norm_val:.1f} 214" transform="rotate(-90 {x + 54} 56)"/>'
                f'<text x="{x + 54}" y="60" text-anchor="middle" font-size="12" font-weight="bold" fill="#0f172a">{display}</text>'
                f'<text x="{x + 54}" y="105" text-anchor="middle" font-size="10" fill="#475569">{name}</text>'
            )
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="980" height="120" viewBox="0 0 980 120">'
            '<rect width="100%" height="100%" fill="white"/>'
            f'{"".join(cells)}'
            '</svg>'
        )
        return _svg_to_data_uri(svg)

    fig, axes = plt.subplots(1, len(scores), figsize=(10, 2.2))
    
    for i, (name, val) in enumerate(scores.items()):
        ax = axes[i]
        scale = 10 if name != "AI Market" and name != "Market Stability" and name != "Goal Confidence" else 100
        # Normalize to 100 for color logic
        norm_val = (val / scale) * 100
        
        color = '#4caf50' if norm_val >= 80 else ('#ff9800' if norm_val >= 50 else '#f44336')
        
        ax.pie([norm_val, 100 - norm_val], colors=[color, '#eee'], startangle=90, counterclock=False, wedgeprops={'width': 0.3})
        ax.text(0, 0, f"{val:.1f}" if scale == 10 else f"{val:.0f}%", ha='center', va='center', fontweight='bold', fontsize=10)
        ax.set_title(name, fontsize=9, pad=2)
    
    plt.tight_layout()
    return _fig_to_base64(fig)
