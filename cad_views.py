"""
Multi-angle CAD renders of the LEO factory station and its key parts.

Builds the full assembly via leo_factory and produces:
  - Five whole-station views: isometric, alt-isometric, front, top, side
  - Per-part isometric + front + side renders for the most interesting
    components (robotic arm, vacuum-pod cluster, thermal-gradient pod
    cluster, microgravity sub-truss)

Each PNG is wrapped in the same blueprint/HUD frame used by the
technical drawings (cyan border, header strip, title block).
"""

import math
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import cadquery as cq

import leo_factory as lf

# ----- Style (matches technical_drawings.py blueprint look) -----------------
PAGE_BG    = "#06121f"
PANEL_BG   = "#0a1a2c"
EDGE_COLOR = "#3fbcff"
PRIMARY    = "#eaf6ff"
SECONDARY  = "#7ec8ff"
ACCENT     = "#ffb454"
DIM_COLOR  = "#79a8c9"
GRID_COLOR = "#163455"

plt.rcParams["font.family"] = "monospace"
plt.rcParams["font.monospace"] = ["DejaVu Sans Mono", "Menlo", "Courier New"]

GLOW_FX = [pe.Stroke(linewidth=2.6, foreground=EDGE_COLOR, alpha=0.20),
           pe.Normal()]

OUT_DIR = "drawings/views"
os.makedirs(OUT_DIR, exist_ok=True)

# Camera presets (elev, azim) -- station is rendered with truss along plot X
VIEWS = {
    "iso":     (22,  35),
    "iso_alt": (28, 145),
    "iso_low": (10,  60),
    "front":   (0,    0),    # looking along truss axis
    "top":     (89, -90),    # plan view
    "side":    (4,   90),    # side elevation
    "rear":    (8,  180),
}


# =============================================================================
# Tessellation
# =============================================================================
def tessellate(assy):
    """(verts, tris, rgba, name) tuples in plot-frame coords."""
    out = []
    for child in assy.children:
        obj = child.obj
        if obj is None:
            continue
        shape = obj.val() if isinstance(obj, cq.Workplane) else obj
        try:
            verts, tris = shape.tessellate(1.0, 0.4)
        except Exception:
            continue
        if not verts or not tris:
            continue
        # Same coordinate remap leo_factory uses: (x,y,z) -> (z,x,y)
        v = np.array([(p.z, p.x, p.y) for p in verts])
        t = np.array(tris)
        col = child.color.toTuple() if child.color is not None else (0.7, 0.7, 0.7, 1.0)
        out.append((v, t, col, child.name))
    return out


# =============================================================================
# Frame around the figure (blueprint border)
# =============================================================================
def add_frame(fig, sheet_title, part_name, part_no, view_label,
              fig_w, fig_h):
    frame = fig.add_axes([0, 0, 1, 1], zorder=10)
    frame.set_xlim(0, 1); frame.set_ylim(0, 1)
    frame.set_xticks([]); frame.set_yticks([])
    frame.patch.set_alpha(0)
    for s in frame.spines.values():
        s.set_visible(False)

    # Outer rectangle
    frame.add_patch(mpatches.Rectangle(
        (0.008, 0.008), 0.984, 0.984,
        fill=False, edgecolor=EDGE_COLOR, linewidth=1.2,
    ))
    # Corner brackets
    cb = 0.022
    asp = fig_w / fig_h
    for (x, y, sx, sy) in [
        (0.008, 0.008,  +1, +1),
        (0.992, 0.008,  -1, +1),
        (0.008, 0.992,  +1, -1),
        (0.992, 0.992,  -1, -1),
    ]:
        frame.add_line(Line2D([x, x + sx * cb], [y, y],
                              color=EDGE_COLOR, linewidth=2.6))
        frame.add_line(Line2D([x, x], [y, y + sy * cb * asp],
                              color=EDGE_COLOR, linewidth=2.6))

    # Header strip
    frame.add_patch(mpatches.Rectangle(
        (0.008, 0.955), 0.984, 0.037,
        facecolor=PANEL_BG, edgecolor=EDGE_COLOR, linewidth=1.0,
    ))
    frame.text(0.020, 0.974, "◆ LEO FACTORY STATION   //   "
                              "CAD VIEW SET",
               fontsize=9, color=EDGE_COLOR, fontweight="bold",
               va="center", path_effects=GLOW_FX)
    frame.text(0.980, 0.974, sheet_title + "   ◆",
               fontsize=9, color=ACCENT, fontweight="bold",
               va="center", ha="right")

    # Header tick marks
    for i in range(1, 40):
        x = 0.008 + i * (0.984 / 40)
        major = (i % 5 == 0)
        frame.add_line(Line2D(
            [x, x], [0.955, 0.955 - (0.010 if major else 0.005)],
            color=EDGE_COLOR, linewidth=0.6, alpha=0.6,
        ))

    # View label (top-left of plot area)
    frame.text(0.022, 0.93, "▌ " + view_label,
               fontsize=10, color=EDGE_COLOR, fontweight="bold",
               va="top", path_effects=GLOW_FX)

    # Title block (lower-right)
    bx0, by0, bw, bh = 0.62, 0.018, 0.37, 0.085
    frame.add_patch(mpatches.Rectangle(
        (bx0, by0), bw, bh,
        facecolor=PANEL_BG, edgecolor=EDGE_COLOR, linewidth=1.2,
    ))
    # Cyan accent bar
    frame.add_patch(mpatches.Rectangle(
        (bx0, by0 + bh - bh * 0.22), bw, bh * 0.22,
        facecolor=EDGE_COLOR, edgecolor="none",
    ))
    frame.text(bx0 + 0.008, by0 + bh - bh * 0.11,
               "▮ ORBITAL FACTORY DIVISION",
               fontsize=7, color=PAGE_BG, fontweight="bold", va="center")

    frame.text(bx0 + 0.008, by0 + bh * 0.55, "PART",
               fontsize=6, color=DIM_COLOR)
    frame.text(bx0 + 0.008, by0 + bh * 0.30, part_name,
               fontsize=10, color=PRIMARY, fontweight="bold")
    frame.text(bx0 + 0.008, by0 + bh * 0.08, "LEO FACTORY STATION",
               fontsize=7, color=DIM_COLOR)

    frame.text(bx0 + bw * 0.62, by0 + bh * 0.55, "PART NO",
               fontsize=6, color=DIM_COLOR)
    frame.text(bx0 + bw * 0.62, by0 + bh * 0.30, part_no,
               fontsize=8, color=ACCENT, fontweight="bold")

    frame.text(bx0 + bw * 0.85, by0 + bh * 0.55, "VIEW",
               fontsize=6, color=DIM_COLOR)
    frame.text(bx0 + bw * 0.85, by0 + bh * 0.30, view_label.split()[0],
               fontsize=8, color=ACCENT, fontweight="bold")


# =============================================================================
# Render a tessellated assembly to a styled PNG
# =============================================================================
def render_view(pieces, view, out_path, sheet_title,
                part_name, part_no, view_label, focus_only=None,
                fig_w=14, fig_h=10):
    if focus_only is not None:
        pieces = [p for p in pieces if p[3] in focus_only]
    if not pieces:
        return

    all_verts = np.concatenate([p[0] for p in pieces], axis=0)
    cmin = all_verts.min(0)
    cmax = all_verts.max(0)
    center = (cmin + cmax) / 2.0
    extents = (cmax - cmin) * 1.08
    dx, dy, dz = [max(e, 1e-3) for e in extents]

    fig = plt.figure(figsize=(fig_w, fig_h), facecolor=PAGE_BG)
    ax = fig.add_axes([0.04, 0.11, 0.92, 0.80], projection="3d")
    ax.set_facecolor(PANEL_BG)
    try:
        ax.set_proj_type("ortho")
    except Exception:
        pass

    # Subtle grid panes
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.set_facecolor(PANEL_BG)
        axis.pane.set_edgecolor(GRID_COLOR)
        axis.pane.set_alpha(0.55)
        axis._axinfo["grid"]["color"] = GRID_COLOR
        axis._axinfo["grid"]["linewidth"] = 0.4

    for verts, tris, rgba, _name in pieces:
        triangles = verts[tris]
        r, g, b, a = rgba
        # Brighten cool, slightly desaturate, and add glowing edges
        face = (
            min(1.0, r * 0.85 + 0.10),
            min(1.0, g * 0.90 + 0.13),
            min(1.0, b * 0.95 + 0.18),
            max(0.55, a),
        )
        coll = Poly3DCollection(
            triangles,
            facecolor=face,
            edgecolor=(0.62, 0.84, 1.0, 0.30),
            linewidths=0.18,
        )
        ax.add_collection3d(coll)

    ax.set_xlim(center[0] - dx / 2.0, center[0] + dx / 2.0)
    ax.set_ylim(center[1] - dy / 2.0, center[1] + dy / 2.0)
    ax.set_zlim(center[2] - dz / 2.0, center[2] + dz / 2.0)
    try:
        ax.set_box_aspect((dx, dy, dz), zoom=2.0)
    except TypeError:
        ax.set_box_aspect((dx, dy, dz))

    elev, azim = VIEWS[view]
    ax.view_init(elev=elev, azim=azim)
    ax.set_xticks([]); ax.set_yticks([]); ax.set_zticks([])

    add_frame(fig, sheet_title, part_name, part_no, view_label,
              fig_w, fig_h)
    fig.savefig(out_path, dpi=160, facecolor=PAGE_BG)
    plt.close(fig)


# =============================================================================
# Per-part filter sets (names from build_station)
# =============================================================================
PART_GROUPS = {
    "robotic_arm": {
        "name": "Robotic Servicing Arm",
        "no":   "LFS-RA-001",
        "parts": {"robotic_arm"},
    },
    "vacuum_zone": {
        "name": "Vacuum Process Pods",
        "no":   "LFS-VP-001",
        "parts": {
            "vacuum_pods", "vacuum_aperture_rings", "vacuum_local_radiators",
            "vacuum_shutters", "vacuum_load_locks", "vacuum_cryocoolers",
            "vacuum_ram_baffles",
        },
    },
    "thermal_gradient": {
        "name": "Thermal-Gradient Pods",
        "no":   "LFS-TG-001",
        "parts": {
            "thermal_gradient_hot", "thermal_gradient_mid",
            "thermal_gradient_cold", "thermal_gradient_heat_pipes",
            "thermal_gradient_mli",
        },
    },
    "microgravity": {
        "name": "Microgravity Sub-Truss",
        "no":   "LFS-MG-001",
        "parts": {
            "microgravity_subtruss", "microgravity_pods",
            "microgravity_isolation_mounts", "microgravity_hull",
        },
    },
}


# =============================================================================
def main():
    print("Building station assembly...")
    assy = lf.build_station()
    print("Tessellating...")
    pieces = tessellate(assy)
    print(f"  {len(pieces)} parts")

    # ---- Whole-station views ----
    station_views = ["iso", "iso_alt", "iso_low", "front", "top", "side"]
    for v in station_views:
        path = os.path.join(OUT_DIR, f"station_{v}.png")
        render_view(
            pieces, v, path,
            sheet_title=f"STATION {v.upper().replace('_', ' ')}",
            part_name="Station General Arrangement",
            part_no="LFS-GA-001",
            view_label=f"{v.upper().replace('_', ' ')} VIEW",
            fig_w=18, fig_h=11,
        )
        print(f"  {path}")

    # ---- Per-part views ----
    per_part_views = ["iso", "iso_alt", "front", "top", "side"]
    for key, group in PART_GROUPS.items():
        for v in per_part_views:
            path = os.path.join(OUT_DIR, f"{key}_{v}.png")
            render_view(
                pieces, v, path,
                sheet_title=f"{group['name'].upper()} :: {v.upper()}",
                part_name=group["name"],
                part_no=group["no"],
                view_label=f"{v.upper().replace('_', ' ')} VIEW",
                focus_only=group["parts"],
                fig_w=14, fig_h=10,
            )
            print(f"  {path}")

    print("Done.")


if __name__ == "__main__":
    main()
