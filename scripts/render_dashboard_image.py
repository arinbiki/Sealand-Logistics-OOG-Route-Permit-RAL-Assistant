"""
Render a high-resolution, pixel-perfect preview of the Sealand OOG Dispatcher Dashboard.
Saved to assets/dashboard_preview.png.
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)
OUT_PATH = os.path.join(ASSETS_DIR, "dashboard_preview.png")

W, H = 1600, 1000

# Color Palette
BG_DARK = (10, 15, 29)
CARD_BG = (19, 27, 46)
BORDER_COLOR = (40, 56, 88)
ACCENT_CYAN = (0, 210, 255)
ACCENT_GREEN = (0, 230, 118)
ACCENT_AMBER = (255, 171, 0)
ACCENT_RED = (255, 61, 113)
TEXT_WHITE = (240, 244, 252)
TEXT_MUTED = (142, 155, 176)

def get_font(size: int, bold: bool = False):
    font_name = "segoeuib.ttf" if bold else "segoeui.ttf"
    font_path = os.path.join(r"C:\Windows\Fonts", font_name)
    if not os.path.exists(font_path):
        font_name = "arialbd.ttf" if bold else "arial.ttf"
        font_path = os.path.join(r"C:\Windows\Fonts", font_name)
    try:
        return ImageFont.truetype(font_path, size)
    except Exception:
        return ImageFont.load_default()

def render_dashboard():
    img = Image.new("RGB", (W, H), BG_DARK)
    draw = ImageDraw.Draw(img)

    # 1. Top Header
    draw.rectangle([0, 0, W, 75], fill=(15, 23, 42))
    draw.line([(0, 75), (W, 75)], fill=BORDER_COLOR, width=2)

    draw.text((40, 18), "SEALAND LOGISTICS", font=get_font(24, bold=True), fill=ACCENT_CYAN)
    draw.text((310, 24), "• OOG ROUTE & PERMIT RAL ASSISTANT", font=get_font(16, bold=True), fill=TEXT_WHITE)

    # Header Badges
    draw.rounded_rectangle([920, 20, 1160, 54], radius=17, fill=(0, 230, 118, 40), outline=ACCENT_GREEN, width=1)
    draw.text((935, 27), "ZERO-LLM RAL ENGINE", font=get_font(12, bold=True), fill=ACCENT_GREEN)

    draw.rounded_rectangle([1180, 20, 1370, 54], radius=17, fill=(0, 210, 255, 40), outline=ACCENT_CYAN, width=1)
    draw.text((1195, 27), "IRC:SP:35 COMPLIANT", font=get_font(12, bold=True), fill=ACCENT_CYAN)

    draw.rounded_rectangle([1390, 20, 1560, 54], radius=17, fill=(255, 171, 0, 40), outline=ACCENT_AMBER, width=1)
    draw.text((1405, 27), "WINDMILL ACTIVE", font=get_font(12, bold=True), fill=ACCENT_AMBER)

    # Preset scenarios strip
    draw.rounded_rectangle([40, 90, W - 40, 140], radius=8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
    draw.text((60, 105), "⚡ PRESET SCENARIOS:", font=get_font(12, bold=True), fill=ACCENT_CYAN)

    presets = [
        "120MT Turbine (Vizag -> Raipur)",
        "85MT Transformer (Chennai -> Bangalore)",
        "95MT Fractionation Col (JNPT -> Nagpur)",
        "140MT Wind Nacelle (Mundra -> Ahmedabad)"
    ]
    px = 220
    for p in presets:
        draw.rounded_rectangle([px, 100, px + 290, 130], radius=6, fill=(30, 41, 69), outline=BORDER_COLOR, width=1)
        draw.text((px + 12, 108), p, font=get_font(11, bold=True), fill=TEXT_WHITE)
        px += 305

    # 2. Main Workspace (2 Columns)
    # LEFT PANEL: Parameters & Physics Simulator (width: 460)
    draw.rounded_rectangle([40, 155, 500, H - 40], radius=12, fill=CARD_BG, outline=BORDER_COLOR, width=1)
    draw.text((60, 175), "Cargo & Transport Physics", font=get_font(18, bold=True), fill=TEXT_WHITE)
    draw.text((370, 179), "IRC:SP:35", font=get_font(12, bold=True), fill=ACCENT_CYAN)

    # Origin & Dest
    draw.text((60, 215), "Origin Seaport", font=get_font(12, bold=True), fill=TEXT_MUTED)
    draw.rounded_rectangle([60, 235, 480, 275], radius=6, fill=(10, 15, 29), outline=BORDER_COLOR, width=1)
    draw.text((75, 246), "Visakhapatnam Port (Vizag) - AP", font=get_font(14, bold=True), fill=TEXT_WHITE)

    draw.text((60, 290), "Destination Industrial Hub", font=get_font(12, bold=True), fill=TEXT_MUTED)
    draw.rounded_rectangle([60, 310, 480, 350], radius=6, fill=(10, 15, 29), outline=BORDER_COLOR, width=1)
    draw.text((75, 321), "Raipur Logistics Hub (CG)", font=get_font(14, bold=True), fill=TEXT_WHITE)

    # Sliders
    sliders = [
        ("Net Cargo Weight", "85.0 MT", 380, 0.45, ACCENT_CYAN),
        ("Loaded Vehicle Height", "5.10 m (ROB Warning)", 440, 0.65, ACCENT_AMBER),
        ("Consignment Width", "4.20 m (Escort Mandate)", 500, 0.55, ACCENT_CYAN),
        ("Consignment Length", "24.5 m", 560, 0.40, ACCENT_CYAN),
        ("Hydraulic Axle Lines", "10 Axles", 620, 0.45, ACCENT_CYAN),
    ]
    for label, val, sy, pct, col in sliders:
        draw.text((60, sy), label, font=get_font(12, bold=True), fill=TEXT_MUTED)
        draw.text((350, sy), val, font=get_font(12, bold=True), fill=col)
        draw.rounded_rectangle([60, sy + 22, 480, sy + 30], radius=4, fill=(30, 41, 69))
        draw.rounded_rectangle([60, sy + 22, int(60 + 420 * pct), sy + 30], radius=4, fill=col)

    # Axle physics box
    draw.rounded_rectangle([60, 680, 480, 780], radius=8, fill=(15, 23, 42), outline=BORDER_COLOR, width=1)
    draw.text((75, 695), "Gross Vehicle Weight (GVW):", font=get_font(12), fill=TEXT_MUTED)
    draw.text((380, 695), "132.0 MT", font=get_font(12, bold=True), fill=TEXT_WHITE)

    draw.text((75, 722), "Axle Line Loading:", font=get_font(12), fill=TEXT_MUTED)
    draw.text((310, 722), "13.2 MT/Axle (Permissible)", font=get_font(12, bold=True), fill=ACCENT_GREEN)

    draw.text((75, 750), "IRC:SP:35 Safety Margin:", font=get_font(12), fill=TEXT_MUTED)
    draw.text((385, 750), "+2.22 %", font=get_font(12, bold=True), fill=ACCENT_CYAN)

    # Button
    draw.rounded_rectangle([60, 890, 480, 940], radius=8, fill=(0, 180, 216), outline=ACCENT_CYAN, width=1)
    draw.text((160, 905), "⚡ RUN DETERMINISTIC ROUTING", font=get_font(14, bold=True), fill=(10, 15, 29))

    # RIGHT PANEL: Top KPIs
    kpi_boxes = [
        ("TOTAL DISTANCE", "730.0 km", "~4.1 Days Transit", ACCENT_CYAN, 520),
        ("DETERMINISTIC RISK", "82 / 100", "FLAGGED FOR SURVEY", ACCENT_AMBER, 775),
        ("BYPASSES APPLIED", "5 Detours", "Bypassed 65MT Arch", ACCENT_CYAN, 1030),
        ("STATUTORY FEES", "₹57,736.66", "MoRTH + AP + OD + CG", ACCENT_GREEN, 1285)
    ]
    for title, val, sub, col, kx in kpi_boxes:
        draw.rounded_rectangle([kx, 155, kx + 235, 235], radius=10, fill=CARD_BG, outline=BORDER_COLOR, width=1)
        draw.text((kx + 16, 168), title, font=get_font(11, bold=True), fill=TEXT_MUTED)
        draw.text((kx + 16, 188), val, font=get_font(20, bold=True), fill=col)
        draw.text((kx + 16, 214), sub, font=get_font(11), fill=TEXT_MUTED)

    # Status Banner
    draw.rounded_rectangle([520, 250, W - 40, 310], radius=8, fill=(255, 171, 0, 20), outline=ACCENT_AMBER, width=2)
    draw.rounded_rectangle([535, 262, 790, 296], radius=17, fill=(255, 171, 0, 50), outline=ACCENT_AMBER, width=1)
    draw.text((548, 271), "FLAGGED_FOR_DISPATCHER_SURVEY", font=get_font(11, bold=True), fill=ACCENT_AMBER)
    draw.text((810, 271), "Survey Ref: SRV-INVTZ-RPR-2026 • Nagavali 65MT Bridge Bypassed via Sambalpur NH-53", font=get_font(12, bold=True), fill=TEXT_WHITE)

    # SVG Map Representation (Right Center)
    draw.rounded_rectangle([520, 325, W - 40, 680], radius=10, fill=(15, 23, 42), outline=BORDER_COLOR, width=1)
    draw.text((540, 340), "🗺️ SPATIAL FREIGHT CORRIDOR MAP (NATIONAL HIGHWAY NETWORK)", font=get_font(13, bold=True), fill=ACCENT_CYAN)

    # Draw India Network Lines
    net_lines = [
        ((950, 480), ((900, 520))), # Vizag to Vijayawada
        ((900, 520), (880, 620)), # Vijayawada to Chennai
        ((900, 520), (830, 510)), # Vijayawada to Hyderabad
        ((830, 510), (810, 420)), # Hyderabad to Nagpur
        ((810, 420), (890, 420)), # Nagpur to Raipur
        ((950, 480), (960, 410)), # Vizag to Sambalpur (NH-26)
        ((960, 410), (890, 420)), # Sambalpur to Raipur (NH-53)
        ((960, 410), (1020, 370)), # Sambalpur to Kolkata
        ((660, 470), (700, 490)), # JNPT to Pune
        ((700, 490), (760, 510)), # Pune to Solapur
        ((760, 510), (830, 510)), # Solapur to Hyderabad
        ((600, 360), (660, 360)), # Mundra to Ahmedabad
        ((660, 360), (700, 490)), # Ahmedabad to Pune
    ]
    for p1, p2 in net_lines:
        draw.line([p1, p2], fill=(45, 60, 90), width=2)

    # Active Feasible Route: Vizag -> Sambalpur -> Raipur (Glowing Green)
    active_path = [(950, 480), (960, 410), (890, 420)]
    for i in range(len(active_path)-1):
        draw.line([active_path[i], active_path[i+1]], fill=(0, 230, 118, 100), width=8)
        draw.line([active_path[i], active_path[i+1]], fill=ACCENT_GREEN, width=4)

    # Draw Bottleneck Pin (Nagavali Bridge)
    draw.ellipse([920 - 10, 450 - 10, 920 + 10, 450 + 10], fill=(255, 61, 113, 80), outline=ACCENT_RED, width=2)
    draw.text((935, 442), "⛔ Nagavali Arch (65MT LIMIT)", font=get_font(11, bold=True), fill=ACCENT_RED)

    # Draw Nodes
    nodes = [
        ("Vizag Port (Origin)", (950, 480), ACCENT_CYAN, True),
        ("Sambalpur Junc (Detour)", (960, 410), ACCENT_GREEN, False),
        ("Raipur Hub (Dest)", (890, 420), ACCENT_CYAN, True),
        ("Chennai Port", (880, 620), (58, 123, 213), False),
        ("JNPT Mumbai", (660, 470), (58, 123, 213), False),
        ("Kolkata Port", (1020, 370), (58, 123, 213), False),
        ("Nagpur Hub", (810, 420), ACCENT_AMBER, False),
        ("Hyderabad Hub", (830, 510), ACCENT_AMBER, False),
        ("Pune Cluster", (700, 490), ACCENT_AMBER, False),
        ("Ahmedabad Hub", (660, 360), ACCENT_AMBER, False),
        ("Mundra Port", (600, 360), (58, 123, 213), False),
    ]
    for name, pt, col, is_key in nodes:
        r = 7 if is_key else 5
        draw.ellipse([pt[0] - r, pt[1] - r, pt[0] + r, pt[1] + r], fill=col, outline=(10, 15, 29), width=2)
        draw.text((pt[0] + 10, pt[1] - 7), name, font=get_font(11, bold=is_key), fill=TEXT_WHITE if is_key else TEXT_MUTED)

    # Bottom Right: Permit Matrix Table
    draw.rounded_rectangle([520, 700, W - 40, H - 40], radius=10, fill=CARD_BG, outline=BORDER_COLOR, width=1)
    draw.text((540, 715), "📋 STATUTORY PERMIT CHECKLIST & RTO TAX SCHEDULE", font=get_font(13, bold=True), fill=ACCENT_CYAN)

    headers = [("JURISDICTION", 540), ("AUTHORITY", 690), ("FORM CODE", 970), ("STATUTORY FEE", 1190), ("SLA", 1370), ("PORTAL", 1470)]
    for h_name, hx in headers:
        draw.text((hx, 745), h_name, font=get_font(11, bold=True), fill=TEXT_MUTED)
    draw.line([(540, 765), (W - 60, 765)], fill=BORDER_COLOR, width=1)

    permits = [
        ("CENTRAL_MORTH", "Ministry of Road Transport & Highways", "MORTH-ONLINE-SPECIAL-PERMIT", "₹28,140.00", "5 Days", "Online ↗"),
        ("STATE_AP", "Andhra Pradesh Transport Department", "FORM-ODC-AP-1", "₹11,193.87", "4 Days", "Portal ↗"),
        ("STATE_OD", "State Transport Authority Odisha", "OD-RTO-PERMIT-4", "₹9,634.69", "5 Days", "Portal ↗"),
        ("STATE_CG", "Chhattisgarh Transport Department", "CG-TRANSPORT-ODC-PERMIT", "₹8,768.10", "3 Days", "Portal ↗")
    ]
    py = 775
    for jur, auth, code, fee, sla, portal in permits:
        draw.text((540, py), jur, font=get_font(12, bold=True), fill=TEXT_WHITE)
        draw.text((690, py), auth, font=get_font(12), fill=TEXT_MUTED)
        draw.text((970, py), code, font=get_font(11), fill=ACCENT_AMBER)
        draw.text((1190, py), fee, font=get_font(12, bold=True), fill=ACCENT_GREEN)
        draw.text((1370, py), sla, font=get_font(12), fill=TEXT_WHITE)
        draw.text((1470, py), portal, font=get_font(12, bold=True), fill=ACCENT_CYAN)
        py += 28

    # Escort notice
    draw.text((540, 920), "🚨 POLICE ESCORT MANDATORY: Front pilot vehicle with amber revolving strobe + rear escort required by AP, OD & CG.", font=get_font(11, bold=True), fill=ACCENT_AMBER)

    img.save(OUT_PATH, "PNG")
    print(f"[OK] Saved high-resolution dashboard preview to {OUT_PATH}")

if __name__ == "__main__":
    render_dashboard()
