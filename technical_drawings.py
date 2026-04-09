"""
Technical drawings for selected parts of the LEO factory station.

Generates clean, drafting-style multi-view PNGs (front / top / side) with
dimension lines, leader labels, view annotations, scale bars, and a
title block. These are 2D engineering drawings — distinct from the
3D matplotlib renders used for the marketing previews.

Outputs:
  drawings/drawing_robotic_arm.png
  drawings/drawing_vacuum_pod.png
  drawings/drawing_thermal_gradient_pod.png
  drawings/drawing_microgravity_subtruss.png
  drawings/drawing_station_overview.png
"""

import math
import os

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D


# ----- Stylized blueprint / HUD palette --------------------------------------
PAGE_BG     = "#06121f"   # deep navy
PANEL_BG    = "#0a1a2c"
GRID_COLOR  = "#163455"
EDGE_COLOR  = "#3fbcff"   # cyan frame
PRIMARY     = "#eaf6ff"   # near-white primary linework
SECONDARY   = "#7ec8ff"   # cyan secondary
DIM_COLOR   = "#79a8c9"   # dim text / dimensions
ACCENT      = "#ffb454"   # amber callouts
HIGHLIGHT   = "#ff5d7a"   # magenta accents
GLOW        = "#3fbcff"

LINE_THIN  = 0.7
LINE_MED   = 1.2
LINE_THICK = 1.9
CENTER     = (6, 2, 1, 2)
FONT_DIM   = 7
FONT_LBL   = 9
FONT_TITLE = 11

plt.rcParams["font.family"] = "monospace"
plt.rcParams["font.monospace"] = ["DejaVu Sans Mono", "Menlo", "Courier New"]

OUT_DIR = "drawings"
os.makedirs(OUT_DIR, exist_ok=True)

GLOW_FX = [pe.Stroke(linewidth=2.6, foreground=GLOW, alpha=0.20),
           pe.Normal()]


# =============================================================================
# Drafting helpers
# =============================================================================
def _grid(ax, xlim, ylim, step=None):
    """Faint cyan engineering grid with brighter major ticks every 5 lines."""
    dx = xlim[1] - xlim[0]
    dy = ylim[1] - ylim[0]
    if step is None:
        # Aim for ~30 minor lines across the larger dimension
        step = max(dx, dy) / 30.0
        # Snap to a friendly value
        for s in (0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50):
            if s >= step:
                step = s
                break
    x0 = math.floor(xlim[0] / step) * step
    y0 = math.floor(ylim[0] / step) * step
    n = 0
    x = x0
    while x <= xlim[1]:
        major = (round(x / step) % 5 == 0)
        ax.add_line(Line2D(
            [x, x], [ylim[0], ylim[1]],
            color=GRID_COLOR, linewidth=0.8 if major else 0.4,
            alpha=0.85 if major else 0.55, zorder=0,
        ))
        x += step
        n += 1
    y = y0
    while y <= ylim[1]:
        major = (round(y / step) % 5 == 0)
        ax.add_line(Line2D(
            [xlim[0], xlim[1]], [y, y],
            color=GRID_COLOR, linewidth=0.8 if major else 0.4,
            alpha=0.85 if major else 0.55, zorder=0,
        ))
        y += step


def _corner_brackets(ax, xlim, ylim, frac=0.04):
    """L-shaped HUD brackets at the four corners of a view panel."""
    dx = xlim[1] - xlim[0]
    dy = ylim[1] - ylim[0]
    L = min(dx, dy) * frac
    corners = [
        (xlim[0], ylim[0],  +1, +1),
        (xlim[1], ylim[0],  -1, +1),
        (xlim[0], ylim[1],  +1, -1),
        (xlim[1], ylim[1],  -1, -1),
    ]
    for (x, y, sx, sy) in corners:
        ax.add_line(Line2D([x, x + sx * L], [y, y],
                           color=EDGE_COLOR, linewidth=1.6, zorder=5))
        ax.add_line(Line2D([x, x], [y, y + sy * L],
                           color=EDGE_COLOR, linewidth=1.6, zorder=5))


def setup_axes(ax, xlim, ylim, title=None):
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    ax.set_facecolor(PANEL_BG)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    _grid(ax, xlim, ylim)
    _corner_brackets(ax, xlim, ylim)
    if title:
        ax.text(
            0.015, 0.965, "▌ " + title,
            transform=ax.transAxes,
            ha="left", va="top",
            fontsize=FONT_LBL, fontweight="bold",
            color=EDGE_COLOR,
            path_effects=GLOW_FX,
        )


def rect(ax, cx, cy, w, h, lw=LINE_MED, ls="solid", color=PRIMARY):
    ax.add_patch(mpatches.Rectangle(
        (cx - w / 2.0, cy - h / 2.0), w, h,
        fill=False, edgecolor=color, linewidth=lw, linestyle=ls,
        zorder=3, path_effects=GLOW_FX,
    ))


def circle(ax, cx, cy, r, lw=LINE_MED, ls="solid", color=PRIMARY):
    ax.add_patch(mpatches.Circle(
        (cx, cy), r, fill=False,
        edgecolor=color, linewidth=lw, linestyle=ls,
        zorder=3, path_effects=GLOW_FX,
    ))


def line(ax, x1, y1, x2, y2, lw=LINE_MED, ls="solid", color=PRIMARY,
         glow=True):
    ln = Line2D([x1, x2], [y1, y2],
                color=color, linewidth=lw, linestyle=ls, zorder=3)
    if glow:
        ln.set_path_effects(GLOW_FX)
    ax.add_line(ln)


def centerline(ax, x1, y1, x2, y2):
    ax.add_line(Line2D([x1, x2], [y1, y2],
                       color=SECONDARY, linewidth=LINE_THIN,
                       linestyle=(0, CENTER), alpha=0.7, zorder=2))


def hdim(ax, x1, x2, y, label, offset=0.0, tick=0.4):
    yl = y + offset
    ax.annotate(
        "", xy=(x1, yl), xytext=(x2, yl),
        arrowprops=dict(arrowstyle="<|-|>", color=DIM_COLOR,
                        lw=LINE_THIN, mutation_scale=8),
    )
    line(ax, x1, yl - tick / 2, x1, yl + tick / 2,
         lw=LINE_THIN, color=DIM_COLOR, glow=False)
    line(ax, x2, yl - tick / 2, x2, yl + tick / 2,
         lw=LINE_THIN, color=DIM_COLOR, glow=False)
    ax.text((x1 + x2) / 2.0, yl + tick * 0.6, label,
            ha="center", va="bottom",
            fontsize=FONT_DIM, color=ACCENT, fontweight="bold")


def vdim(ax, y1, y2, x, label, offset=0.0, tick=0.4):
    xl = x + offset
    ax.annotate(
        "", xy=(xl, y1), xytext=(xl, y2),
        arrowprops=dict(arrowstyle="<|-|>", color=DIM_COLOR,
                        lw=LINE_THIN, mutation_scale=8),
    )
    line(ax, xl - tick / 2, y1, xl + tick / 2, y1,
         lw=LINE_THIN, color=DIM_COLOR, glow=False)
    line(ax, xl - tick / 2, y2, xl + tick / 2, y2,
         lw=LINE_THIN, color=DIM_COLOR, glow=False)
    ax.text(xl + tick * 0.6, (y1 + y2) / 2.0, label,
            ha="left", va="center", rotation=90,
            fontsize=FONT_DIM, color=ACCENT, fontweight="bold")


def leader(ax, x, y, tx, ty, label):
    # Small filled "target" dot at the leader anchor
    ax.add_patch(mpatches.Circle(
        (x, y), max(0.06, abs(tx - x) * 0.005),
        facecolor=ACCENT, edgecolor=ACCENT, zorder=4,
    ))
    ax.annotate(
        "", xy=(x, y), xytext=(tx, ty),
        arrowprops=dict(arrowstyle="-", color=ACCENT,
                        lw=LINE_THIN, alpha=0.95),
    )
    ax.text(tx, ty, " " + label,
            ha="left", va="center",
            fontsize=FONT_DIM, color=ACCENT, fontweight="bold")


def title_block(fig, part_name, part_no, scale, units="METERS"):
    """Stylized HUD title block in the lower right corner."""
    ax = fig.add_axes([0.55, 0.015, 0.43, 0.115])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_facecolor(PANEL_BG)
    for s in ax.spines.values():
        s.set_color(EDGE_COLOR); s.set_linewidth(1.4)

    # Top accent bar
    ax.add_patch(mpatches.Rectangle((0, 0.86), 1, 0.14,
                                    facecolor=EDGE_COLOR, edgecolor="none"))
    ax.text(0.015, 0.93, "▮ ORBITAL FACTORY DIVISION   ::   "
                          "DRAWING CONTROL", fontsize=7,
            color=PAGE_BG, fontweight="bold", va="center")

    # Internal dividers
    line(ax, 0, 0.43, 1, 0.43, lw=0.8, color=EDGE_COLOR, glow=False)
    line(ax, 0.55, 0, 0.55, 0.86, lw=0.8, color=EDGE_COLOR, glow=False)
    line(ax, 0.78, 0, 0.78, 0.43, lw=0.8, color=EDGE_COLOR, glow=False)

    ax.text(0.02, 0.69, "PART", fontsize=6, color=DIM_COLOR)
    ax.text(0.02, 0.50, part_name, fontsize=FONT_TITLE,
            color=PRIMARY, fontweight="bold")
    ax.text(0.02, 0.26, "PROJECT", fontsize=6, color=DIM_COLOR)
    ax.text(0.02, 0.07, "LEO FACTORY STATION", fontsize=8, color=PRIMARY)

    ax.text(0.57, 0.69, "PART NO", fontsize=6, color=DIM_COLOR)
    ax.text(0.57, 0.50, part_no, fontsize=9, color=ACCENT, fontweight="bold")
    ax.text(0.57, 0.26, "UNITS", fontsize=6, color=DIM_COLOR)
    ax.text(0.57, 0.07, units, fontsize=8, color=PRIMARY)

    ax.text(0.80, 0.69, "SCALE", fontsize=6, color=DIM_COLOR)
    ax.text(0.80, 0.50, scale, fontsize=9, color=ACCENT, fontweight="bold")
    ax.text(0.80, 0.26, "REV", fontsize=6, color=DIM_COLOR)
    ax.text(0.80, 0.07, "A", fontsize=8, color=PRIMARY)


def page(fig_w=14, fig_h=10, sheet_title="GENERAL ARRANGEMENT"):
    fig = plt.figure(figsize=(fig_w, fig_h), facecolor=PAGE_BG)

    # Outer frame with corner brackets
    frame = fig.add_axes([0, 0, 1, 1])
    frame.set_xlim(0, 1); frame.set_ylim(0, 1)
    frame.set_xticks([]); frame.set_yticks([])
    frame.set_facecolor(PAGE_BG)
    for s in frame.spines.values():
        s.set_visible(False)
    # Inner border rectangle
    frame.add_patch(mpatches.Rectangle(
        (0.012, 0.012), 0.976, 0.976,
        fill=False, edgecolor=EDGE_COLOR, linewidth=1.2,
    ))
    # Corner brackets
    cb = 0.025
    for (x, y, sx, sy) in [
        (0.012, 0.012,  +1, +1),
        (0.988, 0.012,  -1, +1),
        (0.012, 0.988,  +1, -1),
        (0.988, 0.988,  -1, -1),
    ]:
        frame.add_line(Line2D([x, x + sx * cb], [y, y],
                              color=EDGE_COLOR, linewidth=2.4))
        frame.add_line(Line2D([x, x], [y, y + sy * cb * (fig_w / fig_h)],
                              color=EDGE_COLOR, linewidth=2.4))
    # Header strip
    frame.add_patch(mpatches.Rectangle(
        (0.012, 0.945), 0.976, 0.043,
        facecolor=PANEL_BG, edgecolor=EDGE_COLOR, linewidth=1.0,
    ))
    frame.text(0.025, 0.967, "◆ LEO FACTORY STATION   //   "
                              "ENGINEERING DRAWING SET",
               fontsize=9, color=EDGE_COLOR, fontweight="bold",
               va="center", path_effects=GLOW_FX)
    frame.text(0.975, 0.967, sheet_title + "   ◆",
               fontsize=9, color=ACCENT, fontweight="bold",
               va="center", ha="right")
    # Tick marks across the top frame
    for i in range(1, 40):
        x = 0.012 + i * (0.976 / 40)
        major = (i % 5 == 0)
        frame.add_line(Line2D(
            [x, x], [0.945, 0.945 - (0.012 if major else 0.006)],
            color=EDGE_COLOR, linewidth=0.6, alpha=0.6,
        ))
    frame.set_zorder(-10)
    return fig


# =============================================================================
# 1. Robotic arm
# =============================================================================
def draw_robotic_arm():
    HULL_R_OUT = 4.55
    rail_x = HULL_R_OUT + 0.80         # 5.35
    base_cx = rail_x + 1.10             # 6.45
    base_cy = 0.0
    base_cz = 0.0
    turret_base_z = base_cz + 1.10 + 0.20   # 1.30
    turret_top_z  = turret_base_z + 1.20    # 2.50

    shoulder = (base_cx + 0.60, base_cy + 0.00, turret_top_z)
    bicep    = (base_cx + 1.80, base_cy - 1.80, turret_top_z)
    elbow    = (base_cx + 5.80, base_cy - 4.60, turret_top_z)
    wrist    = (base_cx + 9.20, base_cy - 6.40, turret_top_z)
    wrist2   = (base_cx + 10.20, base_cy - 7.00, turret_top_z)
    tcp      = (base_cx + 10.90, base_cy - 7.60, turret_top_z)

    fig = page(16, 11)

    # ---- TOP VIEW (XY plane, looking down -Z) ----
    ax = fig.add_axes([0.05, 0.40, 0.92, 0.55])
    setup_axes(ax, (-2, 20), (-10, 4), "TOP VIEW   (looking -Z)")

    # Hull edge (centerline)
    centerline(ax, -1, 0, 19, 0)
    line(ax, -1, HULL_R_OUT, 19, HULL_R_OUT, lw=LINE_THIN, ls="dashed")
    line(ax, -1, -HULL_R_OUT, 19, -HULL_R_OUT, lw=LINE_THIN, ls="dashed")
    ax.text(18.5, HULL_R_OUT + 0.15, "HULL OD", fontsize=FONT_DIM,
            color=DIM_COLOR, ha="right")

    # Rail tubes (two)
    line(ax, -1, rail_x - 0, 19, rail_x - 0, lw=LINE_THIN, ls="dotted")
    # Actually rails run in Z, so in XY view they're points; show as the
    # thin pair at x=rail_x with ±0.45 in Y
    for dy in (-0.45, 0.45):
        circle(ax, rail_x, dy, 0.11, lw=LINE_MED)
    leader(ax, rail_x, 0.45, 14, 2.5,
           "DUAL TRANSLATION RAIL  Ø0.22")

    # Mobile base (top view: 1.80 X × 2.40 Y)
    rect(ax, base_cx, base_cy, 1.80, 2.40, lw=LINE_THICK)
    leader(ax, base_cx + 0.9, 1.2, 4.0, 3.2, "MOBILE BASE CARRIAGE")
    hdim(ax, base_cx - 0.9, base_cx + 0.9, 1.2, "1.80",
         offset=1.0, tick=0.18)
    vdim(ax, -1.2, 1.2, base_cx + 0.9, "2.40",
         offset=1.2, tick=0.18)

    # Turret
    circle(ax, base_cx + 0.60, 0, 0.70, lw=LINE_MED)
    centerline(ax, base_cx + 0.60, -1.2, base_cx + 0.60, 1.2)
    leader(ax, base_cx + 0.60 + 0.7, 0, base_cx + 2.5, 1.6,
           "YAW TURRET  Ø1.40")

    # Joint housings (top view: circles)
    joints = [
        (shoulder, 0.85, "SHOULDER PITCH  Ø1.70"),
        (bicep,    0.75, "SHOULDER ROLL  Ø1.50"),
        (elbow,    0.70, "ELBOW  Ø1.40"),
        (wrist,    0.55, "WRIST PITCH  Ø1.10"),
        (wrist2,   0.45, "WRIST YAW  Ø0.90"),
    ]
    for (jx, jy, _), r, lbl in joints:
        circle(ax, jx, jy, r, lw=LINE_MED)
        centerline(ax, jx - r - 0.2, jy, jx + r + 0.2, jy)
        centerline(ax, jx, jy - r - 0.2, jx, jy + r + 0.2)

    # Boom segments (lines connecting joint centers, drawn as thick links)
    booms = [
        (shoulder, bicep, 0.38),
        (bicep, elbow, 0.42),
        (elbow, wrist, 0.36),
        (wrist, wrist2, 0.28),
        (wrist2, tcp, 0.22),
    ]
    for (a, b, r) in booms:
        # Draw two parallel lines for tube outline
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        line(ax, a[0] + nx * r, a[1] + ny * r,
             b[0] + nx * r, b[1] + ny * r, lw=LINE_MED)
        line(ax, a[0] - nx * r, a[1] - ny * r,
             b[0] - nx * r, b[1] - ny * r, lw=LINE_MED)
        centerline(ax, a[0], a[1], b[0], b[1])

    # End-effector tool
    tdx = tcp[0] - wrist2[0]
    tdy = tcp[1] - wrist2[1]
    tlen = math.hypot(tdx, tdy)
    fwd = (tdx / tlen, tdy / tlen)
    side_v = (-fwd[1], fwd[0])
    ee_w = 0.40
    ee_L = 1.10
    p1 = (tcp[0] + side_v[0] * ee_w, tcp[1] + side_v[1] * ee_w)
    p2 = (tcp[0] - side_v[0] * ee_w, tcp[1] - side_v[1] * ee_w)
    p3 = (tcp[0] + fwd[0] * ee_L + side_v[0] * ee_w,
          tcp[1] + fwd[1] * ee_L + side_v[1] * ee_w)
    p4 = (tcp[0] + fwd[0] * ee_L - side_v[0] * ee_w,
          tcp[1] + fwd[1] * ee_L - side_v[1] * ee_w)
    line(ax, p1[0], p1[1], p3[0], p3[1])
    line(ax, p2[0], p2[1], p4[0], p4[1])
    line(ax, p3[0], p3[1], p4[0], p4[1])
    leader(ax, tcp[0] + fwd[0] * ee_L, tcp[1] + fwd[1] * ee_L,
           18, -7, "LEE GRAPPLE TOOL\nØ0.80 × 1.10")

    # Overall reach dimension shoulder->tcp
    hdim(ax, shoulder[0], tcp[0] + fwd[0] * ee_L, -9.2,
         f"X SPAN  {tcp[0] + fwd[0]*ee_L - shoulder[0]:.2f}",
         tick=0.25)
    vdim(ax, shoulder[1], tcp[1] + fwd[1] * ee_L, 19.5,
         f"Y SPAN  {abs(tcp[1] + fwd[1]*ee_L - shoulder[1]):.2f}",
         tick=0.25)

    # Coordinate triad
    ax.annotate("", xy=(-1.2, 3.2), xytext=(-1.2, 2.2),
                arrowprops=dict(arrowstyle="->", color=PRIMARY))
    ax.annotate("", xy=(-0.2, 2.2), xytext=(-1.2, 2.2),
                arrowprops=dict(arrowstyle="->", color=PRIMARY))
    ax.text(-0.05, 2.2, "+X", fontsize=FONT_DIM)
    ax.text(-1.2, 3.35, "+Y", fontsize=FONT_DIM, ha="center")

    # ---- SIDE ELEVATION (XZ plane) ----
    ax2 = fig.add_axes([0.05, 0.10, 0.92, 0.28])
    setup_axes(ax2, (-2, 20), (-2, 6), "SIDE ELEVATION   (looking -Y)")

    # Hull
    line(ax2, -1, HULL_R_OUT, 19, HULL_R_OUT, lw=LINE_THIN, ls="dashed")
    line(ax2, -1, -HULL_R_OUT, 19, -HULL_R_OUT, lw=LINE_THIN, ls="dashed")
    centerline(ax2, -1, 0, 19, 0)

    # Rail (two tubes seen edge-on; just a horizontal line)
    line(ax2, -1, rail_x - HULL_R_OUT + 0.0, 19, rail_x - HULL_R_OUT + 0.0,
         lw=LINE_THIN)
    # Actually in side view rail is at the elevation rail_x but axes are
    # X horizontal, Z vertical -- so we need different mapping. Redo.
    ax2.cla()
    setup_axes(ax2, (-2, 20), (-2, 6), "SIDE ELEVATION   (looking +Y)")
    # Mapping: horizontal = X, vertical = Z
    # Hull cross-section bounds in X don't apply here; just show base + arm
    # Ground reference (rail level z=0)
    line(ax2, -1, 0, 19, 0, lw=LINE_THIN, ls="dashed")
    ax2.text(-1, 0.1, "rail level (z=0)", fontsize=FONT_DIM, color=DIM_COLOR)

    # Carriage (X width 1.80, Z height 2.20)
    rect(ax2, base_cx, base_cz, 1.80, 2.20, lw=LINE_THICK)
    vdim(ax2, base_cz - 1.10, base_cz + 1.10, base_cx - 1.6, "2.20",
         tick=0.18)

    # Turret
    rect(ax2, base_cx + 0.60, turret_base_z + 0.60, 1.40, 1.20, lw=LINE_MED)
    centerline(ax2, base_cx + 0.60, turret_base_z - 0.4,
               base_cx + 0.60, turret_top_z + 0.6)
    vdim(ax2, turret_base_z, turret_top_z, base_cx + 2.5, "1.20",
         tick=0.18)

    # Arm shown at rail elevation (booms appear as horizontal segments at z)
    arm_z = turret_top_z
    line(ax2, shoulder[0], arm_z, tcp[0], arm_z, lw=LINE_THICK)
    for (jx, _, _), r in [
        (shoulder, 0.85), (bicep, 0.75), (elbow, 0.70),
        (wrist, 0.55), (wrist2, 0.45),
    ]:
        rect(ax2, jx, arm_z, 2 * r * 0.6, 2 * r, lw=LINE_MED)

    # Tool at tip
    rect(ax2, tcp[0] + 0.55, arm_z, 1.10, 0.80, lw=LINE_MED)

    hdim(ax2, base_cx - 0.9, tcp[0] + 1.10, -1.6,
         f"OVERALL  {tcp[0] + 1.10 - (base_cx - 0.9):.2f}", tick=0.22)
    vdim(ax2, 0, arm_z, -1.6, f"{arm_z:.2f}", tick=0.22)

    title_block(fig, "Robotic Servicing Arm",
                "LFS-RA-001", "1:50")
    fig.savefig(os.path.join(OUT_DIR, "drawing_robotic_arm.png"),
                dpi=200, facecolor=PAGE_BG)
    plt.close(fig)


# =============================================================================
# 2. Vacuum process pod
# =============================================================================
def draw_vacuum_pod():
    DX, DY, DZ = 4.0, 3.0, 5.0
    APER = 3.0
    fig = page(14, 10)

    # ---- FRONT VIEW (XZ, looking +Y) -- shows aperture circle ----
    ax = fig.add_axes([0.06, 0.45, 0.42, 0.50])
    setup_axes(ax, (-4, 4), (-4, 4), "FRONT VIEW   (looking +Y)")
    rect(ax, 0, 0, DX, DZ, lw=LINE_THICK)
    circle(ax, 0, 0, APER / 2.0, lw=LINE_MED)
    centerline(ax, -DX / 2 - 0.6, 0, DX / 2 + 0.6, 0)
    centerline(ax, 0, -DZ / 2 - 0.6, 0, DZ / 2 + 0.6)
    hdim(ax, -DX / 2, DX / 2, -DZ / 2 - 0.4, f"{DX:.1f}",
         offset=-0.4, tick=0.2)
    vdim(ax, -DZ / 2, DZ / 2, DX / 2 + 0.3, f"{DZ:.1f}",
         tick=0.2)
    leader(ax, APER / 2.0 * 0.7, APER / 2.0 * 0.7, 2.6, 2.2,
           f"APERTURE  Ø{APER:.1f}")
    # Shutter blade (covers +Z half)
    line(ax, -DX / 2, 0.05, DX / 2, 0.05, lw=LINE_THIN, ls="dashed")
    leader(ax, 0.6, 0.05, 2.6, -1.6, "SHUTTER BLADE")

    # ---- TOP VIEW (XY, looking -Z) ----
    ax2 = fig.add_axes([0.55, 0.45, 0.42, 0.50])
    setup_axes(ax2, (-4, 4), (-4, 4), "TOP VIEW   (looking -Z)")
    rect(ax2, 0, -DY / 2, DX, DY, lw=LINE_THICK)
    centerline(ax2, 0, -DY - 0.6, 0, 0.6)
    # Aperture (in -Y direction edge)
    line(ax2, -APER / 2, 0, APER / 2, 0, lw=LINE_THICK)
    leader(ax2, 0, 0, -3.0, 1.5, "PROCESS APERTURE\n(faces deep space)")
    # Cryocooler can on -X face (MBE-class)
    rect(ax2, -DX / 2 - 0.4, -DY / 2, 0.8, 1.2, lw=LINE_MED)
    leader(ax2, -DX / 2 - 0.4, -DY / 2, -3.6, -2.4, "CRYOCOOLER")
    # Load lock on +Y back
    rect(ax2, 0, -DY - 0.4, 0.55 * DX, 0.8, lw=LINE_MED)
    leader(ax2, 0.55 * DX / 2, -DY - 0.4, 2.5, -2.6, "LOAD LOCK")

    hdim(ax2, -DX / 2, DX / 2, -DY - 1.2, f"{DX:.1f}", tick=0.2)
    vdim(ax2, -DY, 0, DX / 2 + 0.3, f"{DY:.1f}", tick=0.2)

    # ---- SIDE VIEW (YZ, looking +X) ----
    ax3 = fig.add_axes([0.30, 0.06, 0.42, 0.36])
    setup_axes(ax3, (-4, 4), (-4, 4), "SIDE VIEW   (looking +X)")
    rect(ax3, -DY / 2, 0, DY, DZ, lw=LINE_THICK)
    centerline(ax3, -DY - 0.6, 0, 0.6, 0)
    # Local radiator on top (+Y) or bottom — placed alongside
    rect(ax3, -DY / 2, DZ / 2 + 0.6, 2.0, 0.4, lw=LINE_MED)
    leader(ax3, 0, DZ / 2 + 0.6, 2.5, 2.6, "LOCAL RADIATOR\n3.0 × 2.0 m")
    hdim(ax3, -DY, 0, -DZ / 2 - 0.6, f"{DY:.1f}", tick=0.2)
    vdim(ax3, -DZ / 2, DZ / 2, 0.4, f"{DZ:.1f}", tick=0.2)

    title_block(fig, "Vacuum Process Pod",
                "LFS-VP-001", "1:30")
    fig.savefig(os.path.join(OUT_DIR, "drawing_vacuum_pod.png"),
                dpi=200, facecolor=PAGE_BG)
    plt.close(fig)


# =============================================================================
# 3. Thermal-gradient pod
# =============================================================================
def draw_thermal_gradient_pod():
    L = 12.0          # along Y
    Dpod = 2.0
    HOT = 3.0         # absorber square
    COLD = 6.0        # cold radiator square
    PIPE_DIA = 0.10
    fig = page(14, 11)

    # ---- ELEVATION (YZ plane, looking +X) ----
    ax = fig.add_axes([0.07, 0.30, 0.88, 0.62])
    setup_axes(ax, (-9, 9), (-2, 4),
               "ELEVATION   (looking +X)")
    # Pod body — horizontal cylinder along Y, shown as rectangle
    rect(ax, 0, 0, L, Dpod, lw=LINE_THICK)
    centerline(ax, -L / 2 - 1, 0, L / 2 + 1, 0)
    hdim(ax, -L / 2, L / 2, -1.6, f"POD LENGTH  {L:.1f}", tick=0.22)
    vdim(ax, -Dpod / 2, Dpod / 2, L / 2 + 0.6, f"Ø{Dpod:.1f}", tick=0.22)

    # Hot absorber plate at +Y end
    rect(ax, L / 2 + 0.04, 0, 0.08, HOT, lw=LINE_THICK)
    leader(ax, L / 2 + 0.1, HOT / 2, 7, 3.0,
           f"HOT ABSORBER\n{HOT:.1f} × {HOT:.1f} m\n~11 kW IN")

    # Cold radiator plate at -Y end (much larger)
    rect(ax, -L / 2 - 0.04, 0, 0.08, COLD, lw=LINE_THICK)
    leader(ax, -L / 2 - 0.1, -COLD / 2, -7, -1.4,
           f"COLD RADIATOR\n{COLD:.1f} × {COLD:.1f} m\n~17 kW REJECT")

    # 4 external heat pipes (in the elevation we see two of them above and below)
    for dz in (-0.8, 0.8):
        line(ax, -L / 2 - 0.2, dz, L / 2 + 0.2, dz, lw=LINE_MED)
    leader(ax, -2, 0.8, -2, 2.4, f"HEAT PIPES (×4)  Ø{PIPE_DIA:.2f}")

    # MLI jacket (dashed outline around middle of pod)
    rect(ax, 0, 0, L * 0.70, Dpod + 0.36, lw=LINE_THIN, ls="dashed")
    leader(ax, 0, (Dpod + 0.36) / 2, 2, 2.4, "MLI JACKET (70% OF L)")

    # ---- HOT END FACE VIEW ----
    ax2 = fig.add_axes([0.07, 0.05, 0.40, 0.22])
    setup_axes(ax2, (-3, 3), (-3, 3), "HOT END FACE   (+Y)")
    rect(ax2, 0, 0, HOT, HOT, lw=LINE_THICK)
    circle(ax2, 0, 0, Dpod / 2, lw=LINE_THIN, ls="dashed")
    hdim(ax2, -HOT / 2, HOT / 2, -HOT / 2 - 0.5, f"{HOT:.1f}", tick=0.18)
    vdim(ax2, -HOT / 2, HOT / 2, HOT / 2 + 0.3, f"{HOT:.1f}", tick=0.18)

    # ---- COLD END FACE VIEW ----
    ax3 = fig.add_axes([0.55, 0.05, 0.40, 0.22])
    setup_axes(ax3, (-4, 4), (-4, 4), "COLD END FACE   (-Y)")
    rect(ax3, 0, 0, COLD, COLD, lw=LINE_THICK)
    circle(ax3, 0, 0, Dpod / 2, lw=LINE_THIN, ls="dashed")
    # 4 heat-pipe penetrations at 45 deg
    R_pipe = Dpod / 2 + 0.14
    for ang in (45, 135, 225, 315):
        rad = math.radians(ang)
        circle(ax3, R_pipe * math.cos(rad), R_pipe * math.sin(rad),
               PIPE_DIA / 2 + 0.04, lw=LINE_THIN)
    hdim(ax3, -COLD / 2, COLD / 2, -COLD / 2 - 0.5, f"{COLD:.1f}", tick=0.18)
    vdim(ax3, -COLD / 2, COLD / 2, COLD / 2 + 0.3, f"{COLD:.1f}", tick=0.18)

    title_block(fig, "Thermal-Gradient Pod",
                "LFS-TG-001", "1:60")
    fig.savefig(os.path.join(OUT_DIR, "drawing_thermal_gradient_pod.png"),
                dpi=200, facecolor=PAGE_BG)
    plt.close(fig)


# =============================================================================
# 4. Microgravity sub-truss
# =============================================================================
def draw_microgravity_subtruss():
    HUB_R = 4.0
    GAP = 4.0
    L = 40.0
    SIDE = 3.0
    POD = 3.0
    x_inner = -(HUB_R + GAP)             # -8
    x_outer = x_inner - L                 # -48
    x_center = (x_inner + x_outer) / 2.0  # -28
    fig = page(16, 10)

    # ---- PLAN VIEW (XY, looking -Z) ----
    ax = fig.add_axes([0.05, 0.45, 0.92, 0.50])
    setup_axes(ax, (-52, 8), (-6, 6), "PLAN VIEW   (looking -Z)")
    # Hub edge (right side)
    circle(ax, 0, 0, HUB_R, lw=LINE_THICK)
    leader(ax, HUB_R, 0, 4, 4, "CENTRAL HUB  Ø8.0")
    centerline(ax, -52, 0, 8, 0)

    # Sub-truss outline (rectangle along X)
    rect(ax, x_center, 0, L, SIDE, lw=LINE_THICK)
    hdim(ax, x_outer, x_inner, -SIDE - 1.4,
         f"SUB-TRUSS LENGTH  {L:.1f}", tick=0.3)
    vdim(ax, -SIDE / 2, SIDE / 2, x_inner + 1.5, f"{SIDE:.1f}", tick=0.2)
    hdim(ax, x_inner, 0, SIDE + 1.0, f"GAP  {GAP:.1f}", tick=0.2)

    # 6 pods (2x3 grid in X-Z, but we're in XY so show 3 along X, label "×2 in Z")
    pod_xs = [x_center - 4.0, x_center, x_center + 4.0]
    for px in pod_xs:
        rect(ax, px, -2.0, POD, POD * 0.6, lw=LINE_MED)
    leader(ax, pod_xs[1], -2.0, -22, -5,
           "MICROGRAVITY PODS  3.0³  (6 EA, 2×3 GRID IN X-Z)")

    # Tethers from hub anchors to sub-truss
    hub_anchors = []
    for k in range(6):
        ang = k * 60
        ax_pt = (HUB_R * math.cos(math.radians(ang)) - HUB_R + 0.0,
                 HUB_R * math.sin(math.radians(ang)))
        hub_anchors.append(ax_pt)
    sub_anchors = [
        (x_inner, 1.2), (x_inner, -1.2),
        (x_inner - 2, 1.2), (x_inner - 2, -1.2),
    ]
    for ha in hub_anchors[:4]:
        for sa in sub_anchors[:2]:
            line(ax, ha[0], ha[1], sa[0], sa[1],
                 lw=LINE_THIN, ls="dashed")
    leader(ax, x_inner - 1, 1.2, -10, 4.5,
           "ARIS-CLASS SOFT TETHERS\n(rod + damper puck)")

    # ---- ELEVATION (XZ) ----
    ax2 = fig.add_axes([0.05, 0.06, 0.92, 0.32])
    setup_axes(ax2, (-52, 8), (-5, 5), "ELEVATION   (looking +Y)")
    circle(ax2, 0, 0, HUB_R, lw=LINE_THICK)
    rect(ax2, x_center, 0, L, SIDE, lw=LINE_THICK)
    centerline(ax2, -52, 0, 8, 0)

    # Pods 2x3 grid: 3 along X, 2 along Z (z=±2)
    pod_zs = [-2.0, 2.0]
    for px in pod_xs:
        for pz in pod_zs:
            rect(ax2, px, pz, POD, POD, lw=LINE_MED)

    # MG hull (dashed)
    rect(ax2, x_center, 0, L + 6, SIDE + 6, lw=LINE_THIN, ls="dashed")
    leader(ax2, x_center, (SIDE + 6) / 2, -20, 4,
           "MICROGRAVITY HULL  (whipple shield, separate from spine hull)")

    title_block(fig, "Microgravity Sub-Truss & Pods",
                "LFS-MG-001", "1:200")
    fig.savefig(os.path.join(OUT_DIR, "drawing_microgravity_subtruss.png"),
                dpi=200, facecolor=PAGE_BG)
    plt.close(fig)


# =============================================================================
# 5. Station overview
# =============================================================================
def draw_station_overview():
    L = 200.0
    SIDE = 5.0
    HUB_DIA = 8.0
    HULL_L = 160.0
    HULL_OD = 9.10
    SOLAR_LEN = 35.0
    SOLAR_W = 20.0
    RAD_LONG = 70.0
    RAD_SHORT = 25.0

    fig = page(18, 11)

    # ---- PLAN VIEW (XZ, looking -Y) -- truss horizontal ----
    ax = fig.add_axes([0.04, 0.55, 0.94, 0.40])
    setup_axes(ax, (-115, 115), (-30, 30),
               "PLAN VIEW   (looking -Y, sun overhead)")
    # Main truss extents along Z (horizontal)
    rect(ax, 0, 0, L, SIDE, lw=LINE_THICK)
    centerline(ax, -110, 0, 110, 0)
    hdim(ax, -L / 2, L / 2, -SIDE - 1.5,
         f"MAIN TRUSS  {L:.0f} m", tick=0.6)

    # Hub
    rect(ax, 0, 0, 10.0, HUB_DIA, lw=LINE_MED)
    leader(ax, 0, HUB_DIA / 2, 12, 12, f"HUB  Ø{HUB_DIA:.1f}")

    # Spine hull
    rect(ax, 0, 0, HULL_L, HULL_OD, lw=LINE_THIN, ls="dashed")
    leader(ax, HULL_L / 2, HULL_OD / 2, 80, 14,
           f"SPINE HULL  L{HULL_L:.0f}  Ø{HULL_OD:.1f}")

    # Solar wings on +Z end
    for k, dy in enumerate([12, -12]):
        rect(ax, L / 2 + SOLAR_LEN / 2 + 1, dy, SOLAR_LEN, SOLAR_W * 0.6,
             lw=LINE_MED)
    leader(ax, L / 2 + SOLAR_LEN, 12, 100, 25,
           f"SOLAR ARRAYS  2 × {SOLAR_LEN:.0f} × {SOLAR_W:.0f}\n2500 m² total")

    # Radiators on -Z end
    for dy in (10, -10):
        rect(ax, -L / 2 - RAD_LONG / 2 - 1, dy, RAD_LONG, RAD_SHORT * 0.5,
             lw=LINE_MED)
    leader(ax, -L / 2 - RAD_LONG / 2, -10, -100, -22,
           f"PRIMARY RADIATORS  2 × {RAD_LONG:.0f} × {RAD_SHORT:.0f}\n3500 m² total")

    # Microgravity sub-truss off -Z end (transverse along -X)
    rect(ax, -L / 2 - 28, -28, 40, 3, lw=LINE_MED)
    leader(ax, -L / 2 - 28, -29.5, -90, -28,
           "MICROGRAVITY SUB-TRUSS  40 m")

    # ---- END VIEW (looking -Z) ----
    ax2 = fig.add_axes([0.04, 0.06, 0.44, 0.42])
    setup_axes(ax2, (-30, 30), (-25, 25), "END VIEW   (looking -Z)")
    # Triangle truss
    r_t = SIDE / math.sqrt(3.0)
    pts = [(0, r_t), (-SIDE / 2, -r_t / 2), (SIDE / 2, -r_t / 2), (0, r_t)]
    for i in range(3):
        line(ax2, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
             lw=LINE_THICK)
    # Hull circle
    circle(ax2, 0, 0, HULL_OD / 2, lw=LINE_THIN, ls="dashed")
    leader(ax2, HULL_OD / 2, 0, 12, 12, f"HULL Ø{HULL_OD:.1f}")
    # Solar arrays in end view
    for dx in (-12, 12):
        rect(ax2, dx, 0, 4, 18, lw=LINE_MED)
    # Radiators
    for dx in (-22, 22):
        rect(ax2, dx, -2, 4, 14, lw=LINE_MED)
    # +Y arrow (sun)
    ax2.annotate("", xy=(0, 22), xytext=(0, 14),
                 arrowprops=dict(arrowstyle="->", color=PRIMARY))
    ax2.text(0.6, 22, "+Y  SUN", fontsize=FONT_DIM)
    # -Y label (vacuum face)
    ax2.text(0.6, -20, "-Y  DEEP SPACE / VACUUM PODS",
             fontsize=FONT_DIM)

    # ---- KEY FACTS BLOCK ----
    ax3 = fig.add_axes([0.55, 0.16, 0.43, 0.32])
    ax3.set_xlim(0, 1); ax3.set_ylim(0, 1)
    ax3.set_xticks([]); ax3.set_yticks([])
    ax3.set_facecolor(PANEL_BG)
    for s in ax3.spines.values():
        s.set_color(EDGE_COLOR); s.set_linewidth(1.2)
    # Header bar
    ax3.add_patch(mpatches.Rectangle((0, 0.88), 1, 0.12,
                                     facecolor=EDGE_COLOR, edgecolor="none"))
    ax3.text(0.025, 0.94, "▮ KEY DIMENSIONS", fontsize=FONT_TITLE,
             color=PAGE_BG, fontweight="bold", va="center")
    facts = [
        ("Main truss",          "200 m × 5 m equilateral"),
        ("Spine hull",          "160 m × Ø9.1 m whipple"),
        ("Central hub",         "Ø8 m × 10 m"),
        ("Vacuum pods",         "8 ea  4 × 3 × 5 m"),
        ("Microgravity pods",   "6 ea  3 m cubes"),
        ("Thermal-grad pods",   "4 ea  Ø2 × 12 m"),
        ("Sub-truss",           "40 m × 3 m, transverse -X"),
        ("Solar arrays",        "2500 m²"),
        ("Primary radiators",   "3500 m²"),
        ("Orbit",               "800 km dawn-dusk SSO"),
        ("Operations",          "Robot-only, unpressurized"),
    ]
    for i, (k, v) in enumerate(facts):
        y = 0.80 - i * 0.072
        # Faint row separator
        ax3.add_line(Line2D([0.025, 0.975], [y - 0.024, y - 0.024],
                            color=GRID_COLOR, linewidth=0.5, alpha=0.7))
        ax3.text(0.04, y, "› " + k.upper(), fontsize=FONT_LBL,
                 color=SECONDARY)
        ax3.text(0.42, y, v, fontsize=FONT_LBL,
                 color=PRIMARY, fontweight="bold")

    title_block(fig, "Station General Arrangement",
                "LFS-GA-001", "1:1500")
    fig.savefig(os.path.join(OUT_DIR, "drawing_station_overview.png"),
                dpi=200, facecolor=PAGE_BG)
    plt.close(fig)


# =============================================================================
def main():
    print("Generating technical drawings...")
    draw_robotic_arm()
    print("  drawings/drawing_robotic_arm.png")
    draw_vacuum_pod()
    print("  drawings/drawing_vacuum_pod.png")
    draw_thermal_gradient_pod()
    print("  drawings/drawing_thermal_gradient_pod.png")
    draw_microgravity_subtruss()
    print("  drawings/drawing_microgravity_subtruss.png")
    draw_station_overview()
    print("  drawings/drawing_station_overview.png")
    print("Done.")


if __name__ == "__main__":
    main()
