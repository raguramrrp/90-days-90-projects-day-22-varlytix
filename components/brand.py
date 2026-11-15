"""
Brand Components for SIGMORA.
Custom geometric SVG logo combining a measured financial trajectory,
calibrated analytical variance intervals (sigma envelope), and discreet quantitative nodes.
Designed for a high-end, modern stock market analytics workstation (Midnight Pro).
"""

from config import BRAND_NAME, BRAND_DESCRIPTOR, BRAND_TAGLINE, COLORS

# Sleek geometric SVG logo tailored for Midnight Pro stock market terminal
SIGMORA_LOGO_SVG = f"""<svg width="40" height="40" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
  <!-- Dark coordinate framing -->
  <rect x="8" y="8" width="84" height="84" rx="16" fill="{COLORS['primary_surface']}" stroke="{COLORS['border']}" stroke-width="1.5"/>
  <!-- Calibrated uncertainty envelope (variance bounds) -->
  <path d="M 22 74 C 38 68, 54 52, 70 36 C 76 30, 80 22, 82 18" stroke="{COLORS['secondary_accent']}" stroke-width="1.5" stroke-dasharray="2 3" opacity="0.6"/>
  <path d="M 22 80 C 40 76, 56 64, 72 48 C 78 42, 82 34, 82 28" stroke="{COLORS['muted_highlight']}" stroke-width="1.2" stroke-dasharray="2 3" opacity="0.5"/>
  <!-- Sigma trajectory curve -->
  <path d="M 22 77 C 38 72, 54 58, 68 44 C 74 38, 78 28, 82 22" stroke="{COLORS['primary_accent']}" stroke-width="3.5" stroke-linecap="round"/>
  <!-- Mathematical / Analytical nodes -->
  <circle cx="22" cy="77" r="3.5" fill="{COLORS['primary_surface']}" stroke="{COLORS['primary_accent']}" stroke-width="2"/>
  <circle cx="44" cy="68" r="3" fill="{COLORS['secondary_accent']}" stroke="{COLORS['primary_surface']}" stroke-width="1.5"/>
  <circle cx="62" cy="50" r="3.5" fill="{COLORS['primary_accent']}" stroke="{COLORS['primary_surface']}" stroke-width="1.5"/>
  <circle cx="82" cy="22" r="4.5" fill="{COLORS['positive']}" stroke="{COLORS['primary_surface']}" stroke-width="2"/>
  <!-- Sigma glyph accent in upper left -->
  <path d="M 26 22 L 38 22 L 32 30 L 38 38 L 26 38" stroke="{COLORS['secondary_accent']}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" opacity="0.9"/>
</svg>"""

FAVICON_SVG = f"""<svg width="32" height="32" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="100" height="100" rx="20" fill="{COLORS['primary_surface']}" stroke="{COLORS['border']}" stroke-width="2"/>
  <path d="M 20 78 C 38 72, 54 58, 70 42 L 82 22" stroke="{COLORS['primary_accent']}" stroke-width="7" stroke-linecap="round"/>
  <circle cx="82" cy="22" r="7" fill="{COLORS['positive']}"/>
</svg>"""


def get_logo_html(size: int = 36) -> str:
    """Returns SVG logo HTML formatted for embedding."""
    return SIGMORA_LOGO_SVG.replace('width="40" height="40"', f'width="{size}" height="{size}"')


def get_header_brand_html() -> str:
    """Returns the clean brand header HTML for the top navigation bar."""
    return (
        f'<div style="display:flex;align-items:center;gap:12px;">'
        f'<div style="display:flex;align-items:center;">{get_logo_html(38)}</div>'
        f'<div style="display:flex;flex-direction:column;justify-content:center;">'
        f'<span style="font-family:\'Inter\',-apple-system,sans-serif;font-size:22px;font-weight:800;letter-spacing:-0.4px;color:{COLORS["primary_text"]};line-height:1.1;">{BRAND_NAME}</span>'
        f'<span style="font-family:\'Inter\',-apple-system,sans-serif;font-size:11px;font-weight:500;color:{COLORS["secondary_text"]};letter-spacing:0.2px;margin-top:2px;">{BRAND_DESCRIPTOR}</span>'
        f'</div>'
        f'</div>'
    )


def get_demo_badge_html() -> str:
    """Displays a clean simulation mode notice for demo portfolios."""
    return (
        f'<div style="background:{COLORS["primary_surface"]};border:1px solid {COLORS["border"]};border-left:3px solid {COLORS["muted_highlight"]};border-radius:6px;padding:8px 14px;display:flex;align-items:center;gap:10px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,0.2);">'
        f'<span style="width:7px;height:7px;border-radius:50%;background:{COLORS["muted_highlight"]};display:inline-block;"></span>'
        f'<span style="font-size:11.5px;font-weight:600;color:{COLORS["primary_text"]};">Demo Portfolio Active</span>'
        f'<span style="font-size:11.5px;color:{COLORS["secondary_text"]};">— Initialized with deterministic historical simulation series for research & exploration.</span>'
        f'</div>'
    )
