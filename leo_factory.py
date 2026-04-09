"""
leo_factory.py
==============

Parametric CadQuery model of a robot-native LEO industrial factory station.

The station is unpressurized, fully automated, and physically zoned around
three space-native manufacturing advantages: hard vacuum, microgravity, and
extreme thermal gradients. Every visible element has a function, and the
zoning of the architecture is the model's primary message.

Coordinate convention (dawn-dusk sun-synchronous orbit, ~800 km):
    +Y : sun vector (constant; the orbit never eclipses)
    +Z : velocity vector
    -X : nadir
    origin : geometric center of the main truss

Physical rationale, encoded geometrically:
    * The vacuum-process zone sits on the -Y face of the main truss so its
      open process apertures look into deep, dark space. Anti-sun + anti-ram
      minimizes UV soak, atomic-oxygen flux, and contamination from station
      outgassing.
    * The microgravity zone is mounted on a separate sub-truss, physically
      offset from the main spine and connected only through six visible
      vibration-isolation mounts. The robotic rail does not extend onto it,
      because the entire point of the zone is mechanical isolation from
      pumps, reaction wheels and arm motion.
    * The thermal-gradient pods physically span the truss cross-section in Y,
      with a sunlit absorber on +Y and a dedicated cold-end radiator on -Y.
      They use the orbit's geometry itself as a sustained dT source.
    * Solar arrays face +Y; primary radiators are edge-on to the sun
      (normals along ±X) and live on the shadowed -Y side. These are physics,
      not aesthetics.

Author: Pranav Myana + Claude
"""

import math
import os

import cadquery as cq
from cadquery import Vector, Color


# ============================================================================
# PARAMETERS  (top-level, all in meters)
# ============================================================================

# --- Main structural truss --------------------------------------------------
MAIN_TRUSS_LENGTH = 200.0    # along +Z
MAIN_TRUSS_SIDE = 5.0        # equilateral triangular cross-section
LONGERON_DIA = 0.20
BAY_LENGTH = 5.0             # cross-bracing pitch

# --- Microgravity sub-truss (RELOCATED to near station CoM) ----------------
# The original -Z end location put the µg pods ~115 m from the station
# center of mass, where the gravity-gradient acceleration is ~43 µg —
# two orders of magnitude above what microgravity science needs. The
# sub-truss now extends along -X (nadir-ish) from a point next to the
# central hub at z=0 (the station CoM), putting the pods at r ≈ 16-25 m
# from CoM and reducing gravity-gradient to ~6-9 µg. Still gravity-gradient
# limited (true sub-µg requires sitting exactly at the CoM), but the best
# a 200 m station architecture can physically achieve.
MG_SUBTRUSS_LENGTH = 40.0
MG_SUBTRUSS_GAP    = 4.0     # gap from hub face to sub-truss inner end
MG_SUBTRUSS_SIDE   = 3.0     # smaller, lighter cross-section
MG_LONGERON_DIA    = 0.15
MG_BAY_LENGTH      = 5.0
# Soft-mount geometry — long thin tethers + damper pucks, NOT rigid struts.
# Real µg isolation needs ~0.1 Hz natural frequency in 6 DOF (e.g. ARIS on
# ISS). Rigid cylinders would transmit disturbance almost perfectly.
MG_MOUNT_ROD_DIA   = 0.06
MG_MOUNT_PUCK_DIA  = 0.36
MG_MOUNT_PUCK_LEN  = 0.30

# --- Central hub ------------------------------------------------------------
HUB_DIA = 8.0
HUB_LENGTH = 10.0
DOCKING_PORTS = 4
DOCKING_DIA = 1.5

# --- Vacuum-process zone (on -Y face of main truss) -------------------------
N_VACUUM_PODS = 8
VAC_POD_DZ = 5.0             # along truss axis
VAC_POD_DX = 4.0             # transverse
VAC_POD_DY = 3.0             # depth, into -Y
VAC_APERTURE_DIA = 3.0
VAC_LOCAL_RAD_W = 3.0        # along Z
VAC_LOCAL_RAD_H = 2.0        # along Y
VAC_LOCAL_RAD_T = 0.05
VAC_PAIR_SPACING = 15.0      # spacing between consecutive pod pairs along Z

# --- Microgravity-process zone (on isolated sub-truss) ----------------------
# Now clustered tightly near the sub-truss midpoint (the point closest to
# the station CoM) instead of spread along the sub-truss length. This
# minimizes the *internal* gravity-gradient variation between pods (which
# would otherwise be ~2 µg across a 60 m span) on top of the bulk
# CoM-distance reduction.
N_MG_PODS = 6
MG_POD_SIZE = 3.0              # cube — minimizes pod-to-pod spread
MG_POD_DX = MG_POD_SIZE        # along sub-truss axis (now X)
MG_POD_DY = MG_POD_SIZE
MG_POD_DZ = MG_POD_SIZE

# --- Thermal-gradient zone --------------------------------------------------
# Hot-end absorber sized to match the solar flux it captures (~11 kW per
# pod). Cold-end radiator scaled up to actually reject absorbed solar +
# process heat (~15-17 kW at 300 K → ~36 m²). Heat transport along the
# 12 m pod is by VISIBLE external heat pipes; solid conduction through
# the pod walls would not move 11 kW that far. Mid-body wrapped in MLI
# jacket so heat doesn't radiate sideways and flatten the gradient.
N_TG_PODS = 4
TG_POD_LENGTH = 12.0           # along Y, longer than truss cross-section
TG_POD_DIA = 2.0
TG_POD_SPACING = 40.0
TG_HOT_PLATE  = 3.0            # absorber: 9 m² × 1361 W/m² × 0.9 ≈ 11 kW
TG_COLD_PLATE = 6.0            # radiator: 36 m² × 460 W/m² ≈ 17 kW reject
TG_END_PLATE_T = 0.08
TG_HEAT_PIPE_DIA = 0.10
TG_HEAT_PIPE_COUNT = 4         # 4 external pipes around the pod
TG_MLI_OVER = 0.18             # MLI jacket radial offset over pod body

# --- Solar arrays -----------------------------------------------------------
SA_WING_LONG = 50.0           # along ±X (extending outward from hub)
SA_WING_SHORT = 25.0          # along Z
SA_THICK = 0.05
SA_BOOM_LEN = 5.0
SA_BOOM_DIA = 0.4
SA_Y_OFFSET = HUB_DIA / 2.0 + 1.0   # mounted on the +Y / sunlit side

# --- Primary radiators ------------------------------------------------------
RAD_LONG = 70.0               # along Z
RAD_SHORT = 25.0              # along -Y (extending into shadow)
RAD_THICK = 0.08
RAD_BOOM_LEN = 6.0
RAD_BOOM_DIA = 0.4

# --- Robotic servicing rail -------------------------------------------------
RAIL_OFFSET = 0.6
RAIL_DIA = 0.18
ARM_BASE_LEN = 1.5
ARM_SEG_LEN = (4.0, 3.5, 2.5)

# --- ADCS cluster -----------------------------------------------------------
RW_DIA = 1.5
RW_LEN = 1.0

# --- Thermal bus piping -----------------------------------------------------
PIPE_DIA = 0.10

# --- Selective MMOD / thermal-blanket hull ----------------------------------
# Unpressurized whipple-shield wrapper around the central spine and the
# microgravity sub-truss. ~10 kg/m² (NOT 150 kg/m² of pressurized hull).
# Encloses things that need MMOD protection but do NOT need to see space:
# central hub, robotic rail/arm, thermal bus, microgravity pods. Cut with
# apertures for vacuum pods, thermal-gradient pods, and docking ports.
HULL_LENGTH = 160.0          # leaves the +Z ADCS and -Z transition exposed
HULL_R_OUT = 4.55
HULL_R_IN = 4.45
MG_HULL_R_OUT = 5.55
MG_HULL_R_IN = 5.45
MG_HULL_PAD = 6.0            # extra length over the sub-truss

# ============================================================================
# COLORS
# ============================================================================

C_TRUSS        = Color(0.55, 0.55, 0.58, 1.0)
C_SUBTRUSS     = Color(0.74, 0.74, 0.78, 1.0)   # lighter than main truss
C_HUB          = Color(0.28, 0.28, 0.30, 1.0)
C_VAC_POD      = Color(0.10, 0.18, 0.45, 1.0)   # dark blue
C_VAC_RING     = Color(0.85, 0.65, 0.20, 1.0)   # gold aperture rings
C_MG_POD       = Color(0.90, 0.90, 0.92, 1.0)   # cleanroom white-grey
C_TG_HOT       = Color(0.93, 0.45, 0.10, 1.0)   # orange hot end
C_TG_COLD      = Color(0.20, 0.45, 0.85, 1.0)   # blue cold end
C_TG_MID       = Color(0.55, 0.45, 0.45, 1.0)
C_SOLAR        = Color(0.10, 0.15, 0.40, 1.0)
C_SOLAR_GRID   = Color(0.85, 0.70, 0.20, 1.0)
C_RADIATOR     = Color(0.93, 0.93, 0.95, 1.0)
C_PIPE_HOT     = Color(0.78, 0.45, 0.18, 1.0)   # copper supply
C_PIPE_COLD    = Color(0.55, 0.78, 0.92, 1.0)   # pale blue return
C_ROBOT        = Color(0.96, 0.85, 0.10, 1.0)   # safety yellow
C_ADCS         = Color(0.42, 0.42, 0.46, 1.0)
C_BOOM         = Color(0.50, 0.50, 0.52, 1.0)
C_HULL         = Color(0.88, 0.78, 0.50, 0.30)   # MLI gold-beige, semi-transparent
C_HULL_RIB     = Color(0.70, 0.62, 0.36, 0.65)
C_HEAT_PIPE    = Color(0.85, 0.55, 0.18, 1.0)    # copper heat pipes
C_TG_MLI       = Color(0.92, 0.82, 0.42, 0.55)   # MLI jacket on TG pods
C_SHUTTER      = Color(0.65, 0.65, 0.70, 1.0)    # shutter blade (steel)
C_LOAD_LOCK    = Color(0.40, 0.42, 0.48, 1.0)    # load-lock chamber
C_CRYO         = Color(0.82, 0.85, 0.92, 1.0)    # cryocooler housing
C_BAFFLE       = Color(0.30, 0.30, 0.34, 1.0)    # ram baffle


# ============================================================================
# GEOMETRY HELPERS
# ============================================================================

def triangle_vertices(side):
    """
    Equilateral triangle in the XY plane. The +Y vertex is the sun-side
    longeron; the bottom edge (between the two -Y vertices) is the -Y face
    that hosts the vacuum-process pods.
    """
    r = side / math.sqrt(3.0)
    return [
        (0.0,  r),               # apex on +Y (sun side)
        (-side / 2.0, -r / 2.0), # -Y / -X corner
        ( side / 2.0, -r / 2.0), # -Y / +X corner
    ]


def cyl(p1, p2, dia):
    """Cylindrical strut between two 3D points."""
    a = Vector(*p1)
    b = Vector(*p2)
    v = b.sub(a)
    L = v.Length
    if L < 1e-9:
        return None
    return cq.Solid.makeCylinder(dia / 2.0, L, a, v.normalized())


def box(dx, dy, dz, center=(0, 0, 0)):
    """Axis-aligned box centered at given point."""
    return (
        cq.Workplane("XY")
        .box(dx, dy, dz)
        .translate(center)
        .val()
    )


def to_compound(parts):
    parts = [p for p in parts if p is not None]
    return cq.Compound.makeCompound(parts)


# ============================================================================
# COMPONENT BUILDERS
# ============================================================================

def build_main_truss():
    """
    Triangular space frame: three longerons at the equilateral vertices,
    transverse rings every BAY_LENGTH, and one diagonal per face per bay.
    Visually open and sparse - the truss is a scaffold, not a hull.
    """
    L = MAIN_TRUSS_LENGTH
    verts = triangle_vertices(MAIN_TRUSS_SIDE)
    parts = []

    # Longerons
    for vx, vy in verts:
        parts.append(cyl((vx, vy, -L / 2), (vx, vy, L / 2), LONGERON_DIA))

    n_bays = int(round(L / BAY_LENGTH))
    # Rings + face diagonals
    for i in range(n_bays + 1):
        z = -L / 2 + i * BAY_LENGTH
        for j in range(3):
            v1 = verts[j]
            v2 = verts[(j + 1) % 3]
            parts.append(
                cyl((v1[0], v1[1], z), (v2[0], v2[1], z), LONGERON_DIA * 0.7)
            )
        if i < n_bays:
            z2 = z + BAY_LENGTH
            # Alternate diagonal direction per bay for visual richness
            flip = (i % 2 == 0)
            for j in range(3):
                a = verts[j]
                b = verts[(j + 1) % 3]
                if flip:
                    parts.append(cyl((a[0], a[1], z), (b[0], b[1], z2), LONGERON_DIA * 0.55))
                else:
                    parts.append(cyl((b[0], b[1], z), (a[0], a[1], z2), LONGERON_DIA * 0.55))

    return to_compound(parts)


def build_central_hub():
    """
    Avionics / power / docking core at the geometric center of the main truss.
    Cylindrical, oriented along Z, with 4 radial docking ports and a coarse
    suggestion of power distribution and thermal-bus manifolds on its skin.
    """
    parts = []

    # Main pressure-vessel-shaped body (it is NOT pressurized, but the
    # cylindrical form is appropriate for an avionics / power core).
    body = (
        cq.Workplane("XY")
        .cylinder(HUB_LENGTH, HUB_DIA / 2.0)
        .val()
    )
    parts.append(body)

    # Radial docking ports (4, equally spaced around the cylinder)
    for k in range(DOCKING_PORTS):
        ang = math.radians(90.0 * k)
        nx = math.cos(ang)
        ny = math.sin(ang)
        # Port collar: short cylinder sticking radially outward
        port_len = 1.2
        center = ((HUB_DIA / 2.0 + port_len / 2.0) * nx,
                  (HUB_DIA / 2.0 + port_len / 2.0) * ny,
                  0.0)
        port = cq.Solid.makeCylinder(
            DOCKING_DIA / 2.0, port_len,
            Vector(HUB_DIA / 2.0 * nx, HUB_DIA / 2.0 * ny, 0.0),
            Vector(nx, ny, 0.0),
        )
        parts.append(port)
        # Outer flange
        flange = cq.Solid.makeCylinder(
            DOCKING_DIA / 2.0 + 0.15, 0.10,
            Vector((HUB_DIA / 2.0 + port_len) * nx,
                   (HUB_DIA / 2.0 + port_len) * ny,
                   0.0),
            Vector(nx, ny, 0.0),
        )
        parts.append(flange)

    # Surface ribs - suggest power distribution / thermal manifolds
    n_ribs = 6
    for k in range(n_ribs):
        ang = math.radians(360.0 / n_ribs * k + 22.5)
        nx, ny = math.cos(ang), math.sin(ang)
        rib = cq.Solid.makeCylinder(
            0.10, HUB_LENGTH * 0.9,
            Vector((HUB_DIA / 2.0 + 0.05) * nx,
                   (HUB_DIA / 2.0 + 0.05) * ny,
                   -HUB_LENGTH * 0.45),
            Vector(0, 0, 1),
        )
        parts.append(rib)

    return to_compound(parts)


def vacuum_pod_positions():
    """
    Eight vacuum pods arranged in 4 pairs along Z. Each pair sits at a
    common Z position, with the two pods offset slightly in X so they share
    the -Y face of the truss without colliding with the bottom longerons.
    """
    n_pairs = N_VACUUM_PODS // 2
    z_span = (n_pairs - 1) * VAC_PAIR_SPACING
    z0 = -z_span / 2.0
    positions = []
    for i in range(n_pairs):
        z = z0 + i * VAC_PAIR_SPACING
        # Two pods per pair, offset along ±X
        positions.append((+1.5, z, "deposition" if i % 2 == 0 else "mbe"))
        positions.append((-1.5, z, "deposition" if i % 2 == 0 else "mbe"))
    return positions


def build_vacuum_zone():
    """
    Vacuum-process pods on the -Y face of the main truss. Each pod has:

    - A 5 × 4 × 3 m main body with a 3 m circular aperture on its -Y face
    - A SHUTTER mechanism over the aperture (half-open in the model) that
      can close during reboosts, thruster firings, and docking approaches.
      Real apertures need shutters: a single MMOD strike or thruster plume
      contamination event can ruin a chamber permanently.
    - A LOAD LOCK chamber on the +Y back of the pod for substrate
      insertion and removal. Without this, the pod could grow exactly
      one wafer in its lifetime.
    - A small RAM BAFFLE on the +Z velocity-side that shields the
      aperture from atomic-oxygen flux and ram-direction debris.
    - Two ±X local radiators for pod-level heat rejection.

    MBE pods additionally get:
    - A CRYOCOOLER (small cylindrical compressor + cold head) for the
      cryopanels behind the source. Real MBE needs ~77 K cryopumping
      to keep the background pressure ultralow; passive radiators
      can't reach that temperature.
    - A protruding source nub inside the recessed aperture.
    """
    r = MAIN_TRUSS_SIDE / math.sqrt(3.0)
    face_y = -r / 2.0
    pod_center_y = face_y - VAC_POD_DY / 2.0

    pods = []
    rings = []
    rads = []
    shutters = []
    load_locks = []
    cryocoolers = []
    baffles = []

    for px, pz, kind in vacuum_pod_positions():
        cx = px
        cy = pod_center_y
        cz = pz

        # Main pod body
        body = box(VAC_POD_DX, VAC_POD_DY, VAC_POD_DZ, center=(cx, cy, cz))

        # Aperture cutout
        if kind == "deposition":
            hole_depth = VAC_POD_DY * 0.65
        else:
            hole_depth = VAC_POD_DY * 0.95

        hole_axis_len = hole_depth + 0.2
        hole = cq.Solid.makeCylinder(
            VAC_APERTURE_DIA / 2.0, hole_axis_len,
            Vector(cx, cy - VAC_POD_DY / 2.0 - 0.1, cz),
            Vector(0, 1, 0),
        )
        body_cut = cq.Workplane("XY").add(body).cut(cq.Workplane("XY").add(hole)).val()
        pods.append(body_cut)

        # Aperture ring (now part of the shutter housing, not decorative)
        ring = cq.Solid.makeCylinder(
            VAC_APERTURE_DIA / 2.0 + 0.18, 0.10,
            Vector(cx, cy - VAC_POD_DY / 2.0 - 0.05, cz),
            Vector(0, 1, 0),
        )
        ring_inner = cq.Solid.makeCylinder(
            VAC_APERTURE_DIA / 2.0, 0.30,
            Vector(cx, cy - VAC_POD_DY / 2.0 - 0.20, cz),
            Vector(0, 1, 0),
        )
        ring_shape = cq.Workplane("XY").add(ring).cut(
            cq.Workplane("XY").add(ring_inner)
        ).val()
        rings.append(ring_shape)

        # ----- Shutter blade (half-open) ------------------------------------
        # A thin rectangular plate covering the +Z half of the aperture,
        # plus a guide rail running along +X side suggesting the slider axis.
        front_y = cy - VAC_POD_DY / 2.0 - 0.18
        blade = box(
            VAC_APERTURE_DIA + 0.30, 0.05, VAC_APERTURE_DIA / 2.0 + 0.10,
            center=(cx, front_y, cz + VAC_APERTURE_DIA / 4.0 + 0.05),
        )
        shutters.append(blade)
        # Slider guide rails on either side
        for sz in (-VAC_APERTURE_DIA / 2.0 - 0.30, VAC_APERTURE_DIA / 2.0 + 0.30):
            rail = cyl(
                (cx - VAC_APERTURE_DIA / 2.0 - 0.20, front_y - 0.05, cz + sz),
                (cx + VAC_APERTURE_DIA / 2.0 + 0.20, front_y - 0.05, cz + sz),
                0.06,
            )
            if rail: shutters.append(rail)
        # Shutter actuator can on the +X side
        actuator = cq.Solid.makeCylinder(
            0.18, 0.6,
            Vector(cx + VAC_APERTURE_DIA / 2.0 + 0.20, front_y - 0.10, cz - 0.10),
            Vector(0, 0, 1),
        )
        shutters.append(actuator)

        # ----- Load-lock chamber on the +Y back of the pod -------------------
        # A small box with its own little circular hatch on its outer face.
        ll_size_x = VAC_POD_DX * 0.55
        ll_size_y = 1.6
        ll_size_z = VAC_POD_DZ * 0.7
        ll_cx = cx
        ll_cy = cy + VAC_POD_DY / 2.0 + ll_size_y / 2.0
        ll_cz = cz
        load_lock_body = box(ll_size_x, ll_size_y, ll_size_z,
                             center=(ll_cx, ll_cy, ll_cz))
        load_locks.append(load_lock_body)
        # Hatch flange on its +Y face
        hatch = cq.Solid.makeCylinder(
            0.55, 0.10,
            Vector(ll_cx, ll_cy + ll_size_y / 2.0, ll_cz),
            Vector(0, 1, 0),
        )
        load_locks.append(hatch)

        # ----- Ram baffle on +Z velocity side --------------------------------
        # A small flat plate sticking out from the pod's +Z face into -Y space,
        # shielding the aperture from atomic-oxygen flux and debris coming
        # from the velocity direction.
        baffle = box(
            VAC_POD_DX + 0.4, 1.4, 0.06,
            center=(cx,
                    cy - 0.30,
                    cz + VAC_POD_DZ / 2.0 + 0.04),
        )
        baffles.append(baffle)

        # ----- MBE-only: cryocooler + source nub -----------------------------
        if kind == "mbe":
            nub = cq.Solid.makeCylinder(
                0.40, 0.6,
                Vector(cx, cy - VAC_POD_DY / 2.0 + 0.3, cz),
                Vector(0, 1, 0),
            )
            pods.append(nub)
            # Cryocooler compressor on the -X side of the pod
            cryo_compressor = cq.Solid.makeCylinder(
                0.32, 1.10,
                Vector(cx - VAC_POD_DX / 2.0 - 0.45,
                       cy + 0.30,
                       cz - 1.0),
                Vector(0, 0, 1),
            )
            cryocoolers.append(cryo_compressor)
            # Cold-head finger penetrating the pod body
            cold_head = cq.Solid.makeCylinder(
                0.10, VAC_POD_DX / 2.0 + 0.45,
                Vector(cx - VAC_POD_DX / 2.0 - 0.45,
                       cy + 0.30,
                       cz - 0.40),
                Vector(1, 0, 0),
            )
            cryocoolers.append(cold_head)
            # Small flow regulator on top of the compressor
            regulator = box(
                0.40, 0.30, 0.30,
                center=(cx - VAC_POD_DX / 2.0 - 0.45,
                        cy + 0.30,
                        cz + 0.10),
            )
            cryocoolers.append(regulator)

        # Two local radiators on ±X faces of the pod
        for sx in (-1.0, +1.0):
            rad = box(
                VAC_LOCAL_RAD_T,
                VAC_LOCAL_RAD_H,
                VAC_LOCAL_RAD_W,
                center=(cx + sx * (VAC_POD_DX / 2.0 + VAC_LOCAL_RAD_T / 2.0 + 0.05),
                        cy + 0.2,
                        cz),
            )
            rads.append(rad)

    return {
        "bodies": to_compound(pods),
        "rings": to_compound(rings),
        "rads": to_compound(rads),
        "shutters": to_compound(shutters),
        "load_locks": to_compound(load_locks),
        "cryocoolers": to_compound(cryocoolers),
        "baffles": to_compound(baffles),
    }


def microgravity_subtruss_geometry():
    """
    Returns canonical placement data for the relocated microgravity zone.
    The sub-truss is now transverse to the main truss: it extends along -X
    from a point next to the central hub (z ≈ 0, the station CoM), at
    y = 0 to clear the solar booms (+Y) and primary radiators (-Y).
    Returns (x_inner, x_outer, x_center, side).
    """
    side = MG_SUBTRUSS_SIDE
    x_inner = -(HUB_DIA / 2.0 + MG_SUBTRUSS_GAP)            # near end (closest to hub)
    x_outer = x_inner - MG_SUBTRUSS_LENGTH                   # far end (most -X)
    x_center = (x_inner + x_outer) / 2.0
    return x_inner, x_outer, x_center, side


def build_microgravity_zone():
    """
    Isolated microgravity sub-truss, RELOCATED.

    The original architecture put this at the -Z end of the main truss
    (~115 m from the CoM), which is the *worst* possible location for
    microgravity science: the gravity-gradient acceleration scales linearly
    with distance from the CoM, giving ~43 µg quasi-DC bias. The fix is
    to extend the sub-truss along -X, transverse to the main truss, from
    a point right next to the central hub at z ≈ 0. The pods now sit at
    r ≈ 16-25 m from the CoM, giving ~6-9 µg — still gravity-gradient
    limited, but the best a 200 m structure can achieve.

    The connection between the sub-truss and the main truss is six
    long, thin tethers each carrying a damper-puck soft-mount stage in
    the middle. These represent ~0.1 Hz natural-frequency 6-DOF active
    isolation (e.g. ARIS-class), NOT rigid struts. The robotic rail
    intentionally does not extend onto the sub-truss.

    The six pods are clustered tightly near the sub-truss midpoint
    (the point closest to the CoM) instead of spread along its length.
    """
    parts_truss = []
    parts_pods = []
    parts_mounts = []

    side = MG_SUBTRUSS_SIDE
    x_inner, x_outer, x_center, _ = microgravity_subtruss_geometry()

    # Triangular cross-section in the YZ plane (perpendicular to the
    # sub-truss's X axis). Apex on +Y so the structural depth is on the
    # sun-side, mirroring the main truss convention.
    r = side / math.sqrt(3.0)
    cross = [
        (0.0,  r),                # +Y apex
        (-side / 2.0, -r / 2.0),  # -Y / -Z corner
        ( side / 2.0, -r / 2.0),  # -Y / +Z corner
    ]
    # Each entry is (y, z) in the cross-section plane.

    # Longerons running along X
    for cy, cz in cross:
        parts_truss.append(
            cyl((x_inner, cy, cz), (x_outer, cy, cz), MG_LONGERON_DIA)
        )

    # Cross-bracing rings every MG_BAY_LENGTH (no diagonals — keeps
    # internal disturbance low and visually distinguishes from main truss)
    n_bays = int(round(MG_SUBTRUSS_LENGTH / MG_BAY_LENGTH))
    for i in range(n_bays + 1):
        x = x_inner - i * MG_BAY_LENGTH
        for j in range(3):
            (y1, z1) = cross[j]
            (y2, z2) = cross[(j + 1) % 3]
            parts_truss.append(
                cyl((x, y1, z1), (x, y2, z2), MG_LONGERON_DIA * 0.7)
            )

    # ----- Soft-mount tether bundle (6 tethers, each with a damper puck) ----
    # Anchor points on the central hub face: 6 points hexagonally arranged
    # on the -X side of the hub at z=0. Anchor points on the sub-truss
    # inner ring: 6 points around its triangular cross-section.
    hub_anchors = []
    for k in range(6):
        ang = math.radians(60.0 * k + 30.0)
        ay = 1.6 * math.sin(ang)
        az = 1.6 * math.cos(ang)
        hub_anchors.append((-HUB_DIA / 2.0, ay, az))

    sub_anchors = []
    # Two anchors near each of the 3 triangle vertices, slightly inboard
    for (vy, vz) in cross:
        for s in (-0.30, +0.30):
            # In-plane perpendicular offset
            mag = math.sqrt(vy ** 2 + vz ** 2) or 1.0
            oy = -vz / mag * s
            oz =  vy / mag * s
            sub_anchors.append((x_inner, vy * 0.85 + oy, vz * 0.85 + oz))

    for (hx, hy, hz), (sx, sy, sz) in zip(hub_anchors, sub_anchors):
        # Tether is split into two thin rods with a damper puck in the middle.
        # The puck is a small cylinder; the rods are very thin (0.06 m dia),
        # making the joint look soft rather than structural.
        midp = ((hx + sx) / 2.0, (hy + sy) / 2.0, (hz + sz) / 2.0)
        v = Vector(sx - hx, sy - hy, sz - hz)
        L = v.Length
        if L < 1e-6:
            continue
        d = v.normalized()
        # Damper puck — short, fat cylinder centered at midp, axis along the
        # tether direction
        puck = cq.Solid.makeCylinder(
            MG_MOUNT_PUCK_DIA / 2.0,
            MG_MOUNT_PUCK_LEN,
            Vector(midp[0] - d.x * MG_MOUNT_PUCK_LEN / 2.0,
                   midp[1] - d.y * MG_MOUNT_PUCK_LEN / 2.0,
                   midp[2] - d.z * MG_MOUNT_PUCK_LEN / 2.0),
            d,
        )
        parts_mounts.append(puck)
        # Two thin rod segments hub→puck and puck→sub
        rod1_end = (midp[0] - d.x * MG_MOUNT_PUCK_LEN / 2.0,
                    midp[1] - d.y * MG_MOUNT_PUCK_LEN / 2.0,
                    midp[2] - d.z * MG_MOUNT_PUCK_LEN / 2.0)
        rod2_start = (midp[0] + d.x * MG_MOUNT_PUCK_LEN / 2.0,
                      midp[1] + d.y * MG_MOUNT_PUCK_LEN / 2.0,
                      midp[2] + d.z * MG_MOUNT_PUCK_LEN / 2.0)
        rod1 = cyl((hx, hy, hz), rod1_end, MG_MOUNT_ROD_DIA)
        rod2 = cyl(rod2_start, (sx, sy, sz), MG_MOUNT_ROD_DIA)
        if rod1: parts_mounts.append(rod1)
        if rod2: parts_mounts.append(rod2)

    # ----- Six µg pods clustered tightly near the sub-truss midpoint --------
    # 2 rows × 3 columns. The whole cluster is centered at x = x_center,
    # spans only ±5 m in X, and sits just below the sub-truss (-Y face).
    # Each pod is a 3 m cube. With pods at z = ±2 and y = -2.0, the
    # bounding extent fits inside an R = 5 m cylindrical hull.
    pod_xs = [x_center - 4.0, x_center, x_center + 4.0]
    pod_zs = [-2.0, +2.0]
    pod_y = -2.0   # well below the sub-truss

    for px in pod_xs:
        for pz in pod_zs:
            pod = box(MG_POD_DX, MG_POD_DY, MG_POD_DZ, center=(px, pod_y, pz))
            parts_pods.append(pod)
            # Tiny mounting interface stub back up to the sub-truss bottom
            stub = cyl(
                (px, pod_y + MG_POD_DY / 2.0, pz),
                (px, -r / 2.0, pz),
                0.16,
            )
            if stub:
                parts_pods.append(stub)

    # Lightweight servicing arm parked at the sub-truss outer end
    arm_base = cq.Solid.makeCylinder(
        0.30, 0.9,
        Vector(x_outer - 0.5, r, 0.0),
        Vector(-1, 0, 0),
    )
    parts_truss.append(arm_base)
    arm_seg1 = cyl(
        (x_outer - 1.5, r, 0.0),
        (x_outer - 3.0, r + 1.0, 0.8),
        0.16,
    )
    arm_seg2 = cyl(
        (x_outer - 3.0, r + 1.0, 0.8),
        (x_outer - 4.0, r + 2.0, 0.0),
        0.13,
    )
    if arm_seg1: parts_truss.append(arm_seg1)
    if arm_seg2: parts_truss.append(arm_seg2)

    return {
        "truss": to_compound(parts_truss),
        "pods": to_compound(parts_pods),
        "mounts": to_compound(parts_mounts),
    }


def build_thermal_gradient_zone():
    """
    Four cylindrical pods spanning the truss cross-section in Y. Each pod:

    - +Y end has a 3 × 3 m solar absorber plate sized to capture ~11 kW
      of solar flux (1361 W/m² × 9 m² × ~0.9 absorptivity).
    - -Y end has a 6 × 6 m dedicated cold-end radiator sized to actually
      reject the absorbed solar power plus process heat (~17 kW at 300 K).
      The original 3 × 3 m radiator was undersized by ~4× and would have
      overheated within minutes.
    - Four external HEAT PIPES run the full length of the pod, transporting
      heat from the hot end to the cold end. Solid conduction through
      the pod walls cannot move 11 kW over 12 m — heat pipes (or loop
      heat pipes with a working fluid) are the only realistic option.
    - The mid segment is wrapped in a visible MLI jacket so heat
      doesn't radiate sideways and flatten the axial gradient.
    - Body is still split into hot/mid/cold segments so the gradient is
      color-legible at any camera angle.
    """
    hot_parts, mid_parts, cold_parts = [], [], []
    plate_hot, plate_cold = [], []
    pipe_parts, mli_parts = [], []

    z_span = (N_TG_PODS - 1) * TG_POD_SPACING
    z0 = -z_span / 2.0

    L = TG_POD_LENGTH
    seg_len = L / 3.0
    R_pod = TG_POD_DIA / 2.0
    R_pipe_orbit = R_pod + TG_HEAT_PIPE_DIA + 0.04  # heat-pipe offset radius
    R_mli_out = R_pod + TG_MLI_OVER
    R_mli_in  = R_pod + TG_MLI_OVER * 0.55

    for i in range(N_TG_PODS):
        z = z0 + i * TG_POD_SPACING

        # Hot segment (+Y)
        y_hot_center = (L / 2.0 - seg_len / 2.0)
        hot = cq.Solid.makeCylinder(
            R_pod, seg_len,
            Vector(0, y_hot_center - seg_len / 2.0, z),
            Vector(0, 1, 0),
        )
        hot_parts.append(hot)

        # Mid segment (slightly smaller for visual differentiation)
        mid = cq.Solid.makeCylinder(
            R_pod * 0.95, seg_len,
            Vector(0, -seg_len / 2.0, z),
            Vector(0, 1, 0),
        )
        mid_parts.append(mid)

        # Cold segment (-Y)
        cold = cq.Solid.makeCylinder(
            R_pod, seg_len,
            Vector(0, -L / 2.0, z),
            Vector(0, 1, 0),
        )
        cold_parts.append(cold)

        # Process-zone detail bands (melt / growth / cooling)
        for k, frac in enumerate((0.15, 0.50, 0.85)):
            y_band = -L / 2.0 + frac * L
            band = cq.Solid.makeCylinder(
                R_pod + 0.06, 0.20,
                Vector(0, y_band - 0.10, z),
                Vector(0, 1, 0),
            )
            if k == 0:
                cold_parts.append(band)
            elif k == 1:
                mid_parts.append(band)
            else:
                hot_parts.append(band)

        # Hot-end absorber plate (+Y, sun-facing, 3 × 3 m)
        absorber = box(
            TG_HOT_PLATE, TG_END_PLATE_T, TG_HOT_PLATE,
            center=(0, L / 2.0 + 0.05, z),
        )
        plate_hot.append(absorber)
        # Strut from absorber to pod end (visual)
        strut = cyl(
            (0, L / 2.0, z),
            (0, L / 2.0 + 0.10, z),
            R_pod * 0.4,
        )
        if strut: hot_parts.append(strut)

        # Cold-end dedicated radiator (-Y, edge-on to sun, 6 × 6 m)
        cold_rad = box(
            TG_END_PLATE_T, TG_COLD_PLATE, TG_COLD_PLATE,
            center=(0, -L / 2.0 - TG_COLD_PLATE / 2.0 - 0.10, z),
        )
        plate_cold.append(cold_rad)
        # Stiffener cross on the cold radiator face
        for s in (-1, +1):
            rib = box(
                TG_END_PLATE_T + 0.02, TG_COLD_PLATE - 0.5, 0.06,
                center=(0, -L / 2.0 - TG_COLD_PLATE / 2.0 - 0.10, z + s * TG_COLD_PLATE / 4.0),
            )
            plate_cold.append(rib)

        # ----- External heat pipes running hot → cold along the pod -----
        # Four pipes around the pod circumference at 45°/135°/225°/315°,
        # each spanning from the absorber end to the radiator end.
        for k in range(TG_HEAT_PIPE_COUNT):
            ang = math.radians(45.0 + k * (360.0 / TG_HEAT_PIPE_COUNT))
            ox = R_pipe_orbit * math.cos(ang)
            oz = R_pipe_orbit * math.sin(ang)
            y_top = L / 2.0 + 0.05
            y_bot = -L / 2.0 - TG_COLD_PLATE / 2.0 - 0.10
            pipe = cyl(
                (ox, y_top, z + oz),
                (ox, y_bot, z + oz),
                TG_HEAT_PIPE_DIA,
            )
            if pipe: pipe_parts.append(pipe)

        # ----- MLI insulation jacket around the mid segment -----
        # Larger cylinder minus inner cylinder to make a thin shell. The
        # jacket covers the middle ~70% of the pod, keeping the thermal
        # gradient axial.
        jacket_len = L * 0.70
        jacket_y_start = -jacket_len / 2.0
        jacket_outer = cq.Solid.makeCylinder(
            R_mli_out, jacket_len,
            Vector(0, jacket_y_start, z),
            Vector(0, 1, 0),
        )
        jacket_inner = cq.Solid.makeCylinder(
            R_mli_in, jacket_len + 0.4,
            Vector(0, jacket_y_start - 0.20, z),
            Vector(0, 1, 0),
        )
        jacket = jacket_outer.cut(jacket_inner)
        mli_parts.append(jacket)

    return {
        "hot":  to_compound(hot_parts + plate_hot),
        "mid":  to_compound(mid_parts),
        "cold": to_compound(cold_parts + plate_cold),
        "heat_pipes": to_compound(pipe_parts),
        "mli": to_compound(mli_parts),
    }


def build_solar_arrays():
    """
    Two large rectangular wings on the +Y / sunlit side, mounted via short
    booms extending along ±X from the central hub. Wings are face-on to the
    sun (normal +Y) so power capture is maximal at all orbital phases of a
    dawn-dusk SSO. The wings extend along ±X so they never shadow the
    thermal-gradient pods that span the truss in Y.
    """
    parts_panel = []
    parts_grid = []
    parts_boom = []

    half_long = SA_WING_LONG / 2.0
    half_short = SA_WING_SHORT / 2.0

    for sx in (-1.0, +1.0):
        # Boom from hub edge to wing inboard edge
        x_hub = sx * HUB_DIA / 2.0
        x_wing_in = sx * (HUB_DIA / 2.0 + SA_BOOM_LEN)
        x_wing_center = sx * (HUB_DIA / 2.0 + SA_BOOM_LEN + half_long)

        boom = cyl(
            (x_hub, SA_Y_OFFSET, 0.0),
            (x_wing_in, SA_Y_OFFSET, 0.0),
            SA_BOOM_DIA,
        )
        if boom: parts_boom.append(boom)

        # Wing plate (thin in Y, face normal +Y)
        wing = box(
            SA_WING_LONG, SA_THICK, SA_WING_SHORT,
            center=(x_wing_center, SA_Y_OFFSET, 0.0),
        )
        parts_panel.append(wing)

        # Photovoltaic cell grid: subtle ribs on the +Y face
        n_x = 10
        n_z = 5
        for i in range(1, n_x):
            xr = x_wing_center - half_long + (i / n_x) * SA_WING_LONG
            rib = box(
                0.05, 0.02, SA_WING_SHORT - 0.2,
                center=(xr, SA_Y_OFFSET + SA_THICK / 2.0 + 0.01, 0.0),
            )
            parts_grid.append(rib)
        for i in range(1, n_z):
            zr = -half_short + (i / n_z) * SA_WING_SHORT
            rib = box(
                SA_WING_LONG - 0.2, 0.02, 0.05,
                center=(x_wing_center, SA_Y_OFFSET + SA_THICK / 2.0 + 0.01, zr),
            )
            parts_grid.append(rib)

    return {
        "panels": to_compound(parts_panel),
        "grid": to_compound(parts_grid),
        "booms": to_compound(parts_boom),
    }


def build_primary_radiators():
    """
    Two large heat-rejection panels on the shadowed -Y side. The panel
    plane lies in XZ, normal in +Y / -Y, but the panel itself is positioned
    well into the -Y shadow region and shielded by the hub and the truss
    above it. They handle station-level avionics, power-conversion, and
    process-pod waste heat. Thermal-gradient pods have their own dedicated
    cold-end radiators and do not load these.
    """
    parts_panel = []
    parts_boom = []

    # Panels are placed at +X and -X of the hub, in the shadow zone (-Y).
    # Each panel: 70m along Z, 25m along (-Y direction), thin in X
    # to be edge-on to the sun (normal ±X). Booms extend from the hub
    # outward along ±X to the panel inboard edge.
    for sx in (-1.0, +1.0):
        x_hub = sx * HUB_DIA / 2.0
        x_panel = sx * (HUB_DIA / 2.0 + RAD_BOOM_LEN + RAD_THICK / 2.0)

        boom = cyl(
            (x_hub, -HUB_DIA / 2.0 - 0.5, 0.0),
            (x_panel, -HUB_DIA / 2.0 - 0.5, 0.0),
            RAD_BOOM_DIA,
        )
        if boom: parts_boom.append(boom)

        # Panel: thin in X, RAD_LONG along Z, RAD_SHORT along Y (extending
        # from -1 m to -(1 + RAD_SHORT) m, well into the shadow side)
        y_top = -HUB_DIA / 2.0 - 0.5
        y_center = y_top - RAD_SHORT / 2.0
        panel = box(
            RAD_THICK, RAD_SHORT, RAD_LONG,
            center=(x_panel, y_center, 0.0),
        )
        parts_panel.append(panel)

        # A few stiffener ribs on the panel face
        for i in range(1, 6):
            zr = -RAD_LONG / 2.0 + i * RAD_LONG / 6.0
            rib = box(
                RAD_THICK + 0.04, RAD_SHORT - 0.4, 0.05,
                center=(x_panel, y_center, zr),
            )
            parts_panel.append(rib)

    return {
        "panels": to_compound(parts_panel),
        "booms": to_compound(parts_boom),
    }


def build_thermal_bus():
    """
    Curved-feeling pipe runs (made of straight segments) connecting the
    pods to the central hub and the hub to the primary radiators. Two
    colors: copper hot-supply, pale-blue cold-return. Routed along truss
    longerons rather than through empty space.
    """
    hot, cold = [], []

    # Choose a longeron path on the +X / -Y bottom of the truss for hot,
    # and the -X / -Y bottom longeron for cold.
    main_verts = triangle_vertices(MAIN_TRUSS_SIDE)
    bot_pos = main_verts[2]   # +X corner of -Y edge
    bot_neg = main_verts[1]   # -X corner of -Y edge

    # Long axial pipes running the truss length, slightly offset outboard
    # so they hug the longerons and are visible.
    z_min, z_max = -MAIN_TRUSS_LENGTH / 2.0, MAIN_TRUSS_LENGTH / 2.0
    hot.append(cyl(
        (bot_pos[0] + 0.20, bot_pos[1] - 0.20, z_min),
        (bot_pos[0] + 0.20, bot_pos[1] - 0.20, z_max),
        PIPE_DIA,
    ))
    cold.append(cyl(
        (bot_neg[0] - 0.20, bot_neg[1] - 0.20, z_min),
        (bot_neg[0] - 0.20, bot_neg[1] - 0.20, z_max),
        PIPE_DIA,
    ))

    # Drops from the longeron pipes down to each vacuum-pod pair (cosmetic).
    for px, pz, _ in vacuum_pod_positions():
        hot.append(cyl(
            (bot_pos[0] + 0.20, bot_pos[1] - 0.20, pz),
            (px + 1.0, bot_pos[1] - 1.0, pz),
            PIPE_DIA,
        ))
        cold.append(cyl(
            (bot_neg[0] - 0.20, bot_neg[1] - 0.20, pz),
            (px - 1.0, bot_neg[1] - 1.0, pz),
            PIPE_DIA,
        ))

    # Hub-to-radiator manifolds
    for sx in (-1.0, +1.0):
        x_hub = sx * HUB_DIA / 2.0
        x_panel = sx * (HUB_DIA / 2.0 + RAD_BOOM_LEN)
        # Hot supply
        hot.append(cyl(
            (x_hub, -1.5, 1.0),
            (x_panel, -3.0, 1.0),
            PIPE_DIA,
        ))
        # Cold return
        cold.append(cyl(
            (x_hub, -1.5, -1.0),
            (x_panel, -3.0, -1.0),
            PIPE_DIA,
        ))

    return {
        "hot": to_compound(hot),
        "cold": to_compound(cold),
    }


def build_robotic_system():
    """
    Linear servicing rail running the length of the main truss, offset
    0.6 m outboard on the +X face. Mobile base + 3 articulated segments +
    end effector positioned at the truss midpoint. Does NOT extend onto
    the microgravity sub-truss.
    """
    parts = []

    main_verts = triangle_vertices(MAIN_TRUSS_SIDE)
    # +X corner of the bottom edge
    rx_corner = main_verts[2][0]
    ry_corner = main_verts[2][1]
    # Rail offset 0.6 m outboard (further +X) of the longeron
    rail_x = rx_corner + RAIL_OFFSET
    rail_y = ry_corner

    # Two parallel rail tubes
    for dy in (-0.18, 0.18):
        parts.append(cyl(
            (rail_x, rail_y + dy, -MAIN_TRUSS_LENGTH / 2.0),
            (rail_x, rail_y + dy,  MAIN_TRUSS_LENGTH / 2.0),
            RAIL_DIA,
        ))

    # ----- Mobile base carriage on the rail -----
    base_x = rail_x + 0.70
    base_y = rail_y
    base_z = 0.0
    parts.append(box(1.6, 1.2, 1.2, center=(base_x, base_y, base_z)))

    # ----- Turret (yaw) — short vertical cylinder on top of the base -----
    turret_top_z = base_z + 0.60 + 0.40
    parts.append(cq.Solid.makeCylinder(
        0.35, 0.80,
        Vector(base_x, base_y, base_z + 0.60),
        Vector(0, 0, 1),
    ))

    # ----- Shoulder pivot (hinge axis along Y, perpendicular to arm plane) -----
    # The arm lives in the XZ plane so each joint is a horizontal pin along Y.
    shoulder = (base_x + 0.00, base_y, turret_top_z)
    elbow    = (base_x + 3.00, base_y, turret_top_z + 2.20)
    wrist    = (base_x + 5.80, base_y, turret_top_z + 0.40)
    tcp      = (base_x + 6.80, base_y, turret_top_z - 0.40)

    def hinge(center, radius, length):
        # Hinge cylinder centered on `center`, axis along +Y
        return cq.Solid.makeCylinder(
            radius, length,
            Vector(center[0], center[1] - length / 2.0, center[2]),
            Vector(0, 1, 0),
        )

    parts.append(hinge(shoulder, 0.28, 0.70))
    parts.append(hinge(elbow,    0.24, 0.60))
    parts.append(hinge(wrist,    0.20, 0.50))

    # ----- Arm links (upper arm, forearm, end-effector boom) -----
    parts.append(cyl(shoulder, elbow, 0.22))
    parts.append(cyl(elbow,    wrist, 0.18))
    parts.append(cyl(wrist,    tcp,   0.14))

    # ----- Grapple end effector (cylindrical tool + fingers) -----
    # Tool body
    tool_dir = Vector(tcp[0] - wrist[0], tcp[1] - wrist[1], tcp[2] - wrist[2])
    parts.append(cq.Solid.makeCylinder(
        0.18, 0.40,
        Vector(tcp[0], tcp[1], tcp[2]),
        tool_dir,
    ))
    # Two grapple fingers extending past the tool tip
    finger_tip1 = (tcp[0] + 0.55, tcp[1] + 0.12, tcp[2] - 0.25)
    finger_tip2 = (tcp[0] + 0.55, tcp[1] - 0.12, tcp[2] - 0.25)
    parts.append(cyl(tcp, finger_tip1, 0.05))
    parts.append(cyl(tcp, finger_tip2, 0.05))

    return to_compound(parts)


def build_hull():
    """
    Selective MMOD / thermal-blanket hull. Two pieces:

    1. Spine hull - cylindrical shell along the central section of the
       main truss. Encloses the central hub, the robotic rail and arm,
       the thermal bus piping, and the truss interior. Cut with circular
       apertures on its -Y face (for the eight vacuum-pod openings),
       cylindrical penetrations top and bottom (for the four thermal-
       gradient pods that span Y), and four radial penetrations at the
       hub level (for the docking ports). Stops well short of the truss
       ends so the +Z ADCS cluster and the -Z transition to the
       microgravity sub-truss remain exposed.

    2. Microgravity hull - separate cylindrical shell wrapping the
       isolated microgravity sub-truss and its six sealed pods. No
       cutouts: those pods are sealed-environment processes that don't
       need to see space, so they live entirely inside the hull and
       enjoy MMOD + thermal stability for free. The hull is mechanically
       separate from the spine hull (they share no structure), so the
       µg zone's vibration isolation is preserved.

    Both hulls are unpressurized whipple-shield assemblies, NOT pressure
    vessels - this is a robot-only platform. Mass density is ~10 kg/m²
    (vs ~150 for ISS-class pressurized aluminum).
    """
    main_parts = []
    mg_parts = []

    # ===== MAIN SPINE HULL ===================================================
    L = HULL_LENGTH
    R_out = HULL_R_OUT
    R_in = HULL_R_IN

    outer = cq.Solid.makeCylinder(
        R_out, L, Vector(0, 0, -L / 2), Vector(0, 0, 1),
    )
    inner = cq.Solid.makeCylinder(
        R_in, L + 0.5, Vector(0, 0, -L / 2 - 0.25), Vector(0, 0, 1),
    )
    spine = outer.cut(inner)

    # --- Cut circular apertures on the -Y face for vacuum pods ---
    # The vacuum pods sit just inside the hull on its bottom -Y face.
    # We open a 3.2 m circular hole in front of each pod's 3.0 m process
    # aperture so it can see deep space directly.
    for px, pz, _ in vacuum_pod_positions():
        cut = cq.Solid.makeCylinder(
            VAC_APERTURE_DIA / 2.0 + 0.20, 3.0,
            Vector(px, -R_out - 0.5, pz),
            Vector(0, 1, 0),
        )
        spine = spine.cut(cut)

    # --- Cut top and bottom holes for thermal-gradient pods ---
    z_span = (N_TG_PODS - 1) * TG_POD_SPACING
    z0 = -z_span / 2.0
    for i in range(N_TG_PODS):
        z = z0 + i * TG_POD_SPACING
        # Top exit (+Y, hot end)
        cut_top = cq.Solid.makeCylinder(
            TG_POD_DIA / 2.0 + 0.30, 3.0,
            Vector(0, R_in - 0.5, z),
            Vector(0, 1, 0),
        )
        spine = spine.cut(cut_top)
        # Bottom exit (-Y, cold end)
        cut_bot = cq.Solid.makeCylinder(
            TG_POD_DIA / 2.0 + 0.30, 3.0,
            Vector(0, -R_out - 0.5, z),
            Vector(0, 1, 0),
        )
        spine = spine.cut(cut_bot)

    # --- Cut four radial penetrations for docking ports ---
    for k in range(DOCKING_PORTS):
        ang = math.radians(90.0 * k)
        nx, ny = math.cos(ang), math.sin(ang)
        cut_port = cq.Solid.makeCylinder(
            DOCKING_DIA / 2.0 + 0.30, 1.6,
            Vector(nx * (R_in - 0.4), ny * (R_in - 0.4), 0),
            Vector(nx, ny, 0),
        )
        spine = spine.cut(cut_port)

    main_parts.append(spine)

    # --- Longitudinal stiffener / MLI seam ribs on the outside ---
    n_ribs = 8
    for i in range(n_ribs):
        ang = math.radians(360.0 / n_ribs * i + 22.5)
        nx, ny = math.cos(ang), math.sin(ang)
        rib = cq.Solid.makeCylinder(
            0.06, L * 0.96,
            Vector(nx * (R_out + 0.04), ny * (R_out + 0.04), -L * 0.48),
            Vector(0, 0, 1),
        )
        main_parts.append(rib)

    # --- Circumferential bands at each end ---
    for z_band in (-L / 2.0 + 0.05, L / 2.0 - 0.20):
        band_outer = cq.Solid.makeCylinder(
            R_out + 0.10, 0.20,
            Vector(0, 0, z_band), Vector(0, 0, 1),
        )
        band_inner = cq.Solid.makeCylinder(
            R_out, 0.40,
            Vector(0, 0, z_band - 0.10), Vector(0, 0, 1),
        )
        main_parts.append(band_outer.cut(band_inner))

    # ===== MICROGRAVITY HULL (now along X axis, transverse to main spine) ==
    # The relocated µg sub-truss runs along -X from x_inner to x_outer at
    # y ≈ 0, z ≈ 0. The hull is a cylindrical shell along the X axis,
    # mechanically separate from the spine hull (the only links across
    # the gap are the six soft tethers, which are not load-bearing).
    x_inner, x_outer, x_center, _ = microgravity_subtruss_geometry()
    L_mg = MG_SUBTRUSS_LENGTH + MG_HULL_PAD
    R_mg_out = MG_HULL_R_OUT
    R_mg_in = MG_HULL_R_IN

    # Cylinder along X centered at (x_center, 0, 0)
    outer_mg = cq.Solid.makeCylinder(
        R_mg_out, L_mg,
        Vector(x_center + L_mg / 2.0, 0, 0),
        Vector(-1, 0, 0),
    )
    inner_mg = cq.Solid.makeCylinder(
        R_mg_in, L_mg + 0.5,
        Vector(x_center + L_mg / 2.0 + 0.25, 0, 0),
        Vector(-1, 0, 0),
    )
    mg_shell = outer_mg.cut(inner_mg)
    mg_parts.append(mg_shell)

    # MG hull stiffener ribs running along X
    for i in range(6):
        ang = math.radians(360.0 / 6 * i + 30.0)
        ny = math.cos(ang)
        nz = math.sin(ang)
        rib = cq.Solid.makeCylinder(
            0.06, L_mg * 0.95,
            Vector(x_center + L_mg * 0.475,
                   ny * (R_mg_out + 0.04),
                   nz * (R_mg_out + 0.04)),
            Vector(-1, 0, 0),
        )
        mg_parts.append(rib)

    # ----- Spine hull penetration for the soft-tether bundle -----
    # The 6 tethers cross the gap from the hub (-X face) to the µg
    # sub-truss inner ring. Cut a single round opening on the -X side of
    # the spine hull at z=0 to let them pass through.
    tether_hole = cq.Solid.makeCylinder(
        2.2, 3.0,
        Vector(-R_out - 0.5, 0, 0),
        Vector(1, 0, 0),
    )
    spine = main_parts[0].cut(tether_hole)
    main_parts[0] = spine

    return {
        "spine": to_compound(main_parts),
        "microgravity": to_compound(mg_parts),
    }


def build_adcs_cluster():
    """
    Attitude / orbit determination cluster at the +Z end of the main truss.
    Reaction-wheel housing, 4 corner thruster pods, star trackers, and a
    couple of small antennas - all schematic.
    """
    parts = []
    z_top = MAIN_TRUSS_LENGTH / 2.0 + 0.5

    # Reaction wheel housing
    rw = cq.Solid.makeCylinder(
        RW_DIA / 2.0, RW_LEN,
        Vector(0, 0, z_top), Vector(0, 0, 1),
    )
    parts.append(rw)

    # 4 corner thruster pods
    half = MAIN_TRUSS_SIDE / 2.0
    for sx, sy in ((+half, +half), (-half, +half), (+half, -half), (-half, -half)):
        thr = box(0.5, 0.5, 0.6, center=(sx, sy, z_top + 0.5))
        parts.append(thr)
        nozzle = cq.Solid.makeCone(
            0.05, 0.18, 0.30,
            Vector(sx, sy, z_top + 0.95), Vector(0, 0, 1),
        )
        parts.append(nozzle)

    # Star trackers
    for sx in (-0.7, 0.7):
        st = box(0.30, 0.40, 0.30, center=(sx, 0.5, z_top + 1.6))
        parts.append(st)

    # Antenna stalks
    parts.append(cyl((0, -0.8, z_top + 0.5), (0, -2.5, z_top + 1.5), 0.06))
    parts.append(cq.Solid.makeCylinder(
        0.7, 0.05, Vector(0, -2.5, z_top + 1.5), Vector(0, -1, 1).normalized(),
    ))

    return to_compound(parts)


# ============================================================================
# ASSEMBLY
# ============================================================================

def build_station():
    """Compose every named, colored part into a single assembly."""
    assy = cq.Assembly(name="leo_factory")

    # 1. Main structural truss
    assy.add(build_main_truss(), name="main_truss", color=C_TRUSS)

    # 2. Central hub
    assy.add(build_central_hub(), name="central_hub", color=C_HUB)

    # 3. Vacuum-process zone
    vac = build_vacuum_zone()
    assy.add(vac["bodies"], name="vacuum_pods", color=C_VAC_POD)
    assy.add(vac["rings"], name="vacuum_aperture_rings", color=C_VAC_RING)
    assy.add(vac["rads"], name="vacuum_local_radiators", color=C_RADIATOR)
    assy.add(vac["shutters"], name="vacuum_shutters", color=C_SHUTTER)
    assy.add(vac["load_locks"], name="vacuum_load_locks", color=C_LOAD_LOCK)
    assy.add(vac["cryocoolers"], name="vacuum_cryocoolers", color=C_CRYO)
    assy.add(vac["baffles"], name="vacuum_ram_baffles", color=C_BAFFLE)

    # 4. Microgravity-process zone
    mg = build_microgravity_zone()
    assy.add(mg["truss"], name="microgravity_subtruss", color=C_SUBTRUSS)
    assy.add(mg["pods"], name="microgravity_pods", color=C_MG_POD)
    assy.add(mg["mounts"], name="microgravity_isolation_mounts", color=C_BOOM)

    # 5. Thermal-gradient zone
    tg = build_thermal_gradient_zone()
    assy.add(tg["hot"], name="thermal_gradient_hot", color=C_TG_HOT)
    assy.add(tg["mid"], name="thermal_gradient_mid", color=C_TG_MID)
    assy.add(tg["cold"], name="thermal_gradient_cold", color=C_TG_COLD)
    assy.add(tg["heat_pipes"], name="thermal_gradient_heat_pipes", color=C_HEAT_PIPE)
    assy.add(tg["mli"], name="thermal_gradient_mli", color=C_TG_MLI)

    # 6. Solar arrays
    sa = build_solar_arrays()
    assy.add(sa["panels"], name="solar_panels", color=C_SOLAR)
    assy.add(sa["grid"], name="solar_cell_grid", color=C_SOLAR_GRID)
    assy.add(sa["booms"], name="solar_booms", color=C_BOOM)

    # 7. Primary radiators
    rad = build_primary_radiators()
    assy.add(rad["panels"], name="primary_radiators", color=C_RADIATOR)
    assy.add(rad["booms"], name="radiator_booms", color=C_BOOM)

    # 8. Thermal bus
    bus = build_thermal_bus()
    assy.add(bus["hot"], name="thermal_bus_hot", color=C_PIPE_HOT)
    assy.add(bus["cold"], name="thermal_bus_cold", color=C_PIPE_COLD)

    # 9. Robotic servicing rail + arm
    assy.add(build_robotic_system(), name="robotic_arm", color=C_ROBOT)

    # 10. ADCS cluster
    assy.add(build_adcs_cluster(), name="adcs_cluster", color=C_ADCS)

    # 11. Selective MMOD / thermal-blanket hull
    hull = build_hull()
    assy.add(hull["spine"], name="spine_hull", color=C_HULL)
    assy.add(hull["microgravity"], name="microgravity_hull", color=C_HULL)

    return assy


# ============================================================================
# RENDERING (matplotlib 3D, no GUI required)
# ============================================================================

def _tessellate_assembly(assy):
    """
    Walk the top-level assembly children and tessellate each into
    (verts, tris, color) triples for matplotlib rendering.

    Coordinates are remapped from station-frame (X right, Y sun-up,
    Z velocity-along-truss) to plot-frame (truss along plot X horizontal,
    cross-X along plot Y, sun along plot Z). This puts the long truss
    horizontally in landscape renders, which is far more readable.
    """
    import numpy as np
    out = []
    for child in assy.children:
        obj = child.obj
        if obj is None:
            continue
        if isinstance(obj, cq.Workplane):
            shape = obj.val()
        else:
            shape = obj
        try:
            verts, tris = shape.tessellate(1.5, 0.6)
        except Exception:
            continue
        if not verts or not tris:
            continue
        # Remap (x, y, z) -> (z, x, y) so truss runs along plot X
        verts_np = np.array([(v.z, v.x, v.y) for v in verts])
        tris_np = np.array(tris)
        col = child.color
        if col is not None:
            rgba = col.toTuple()
        else:
            rgba = (0.7, 0.7, 0.7, 1.0)
        out.append((verts_np, tris_np, rgba, child.name))
    return out


def render(assy, out_path, view="iso", highlight=None):
    """
    Render the assembly to a PNG via matplotlib's mpl_toolkits.mplot3d.
    `view` selects camera; `highlight` is an optional set of part names
    that should be drawn at full opacity while others fade.
    """
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    pieces = _tessellate_assembly(assy)

    # Compute data extents up front so we can size the figure / box aspect.
    all_verts = np.concatenate([p[0] for p in pieces], axis=0)
    cmin = all_verts.min(0)
    cmax = all_verts.max(0)
    center = (cmin + cmax) / 2.0
    extents = (cmax - cmin) * 1.04
    dx, dy, dz = extents

    # Landscape figure - truss now runs horizontally after coordinate remap.
    fig = plt.figure(figsize=(22, 12), facecolor="#0a0a14")
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0], projection="3d")
    ax.set_facecolor("#0a0a14")
    try:
        ax.set_proj_type("ortho")
    except Exception:
        pass

    for verts, tris, rgba, name in pieces:
        triangles = verts[tris]
        if highlight is not None and name not in highlight:
            r, g, b, _ = rgba
            face = (r * 0.30 + 0.05, g * 0.30 + 0.05, b * 0.30 + 0.05, 0.10)
        else:
            face = rgba
        coll = Poly3DCollection(
            triangles,
            facecolor=face,
            edgecolor=(1, 1, 1, 0.10),
            linewidths=0.05,
        )
        ax.add_collection3d(coll)

    ax.set_xlim(center[0] - dx / 2.0, center[0] + dx / 2.0)
    ax.set_ylim(center[1] - dy / 2.0, center[1] + dy / 2.0)
    ax.set_zlim(center[2] - dz / 2.0, center[2] + dz / 2.0)
    try:
        ax.set_box_aspect((dx, dy, dz), zoom=2.4)
    except TypeError:
        try:
            ax.set_box_aspect((dx, dy, dz))
        except Exception:
            pass

    if view == "iso":
        ax.view_init(elev=22, azim=35)
    elif view == "front":
        ax.view_init(elev=0, azim=0)
    elif view == "top":
        ax.view_init(elev=88, azim=-90)
    elif view == "side":
        ax.view_init(elev=5, azim=90)
    elif view == "iso2":
        ax.view_init(elev=28, azim=125)

    ax.set_axis_off()
    plt.savefig(out_path, dpi=130, facecolor="#0a0a14")
    plt.close(fig)


def render_zones_panel(assy, out_path):
    """
    4-panel figure: full station, vacuum zone, microgravity zone,
    thermal-gradient zone. Each subpanel highlights one zone.
    """
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    pieces = _tessellate_assembly(assy)

    zones = {
        "Full station": None,
        "Vacuum-process zone": {
            "vacuum_pods", "vacuum_aperture_rings", "vacuum_local_radiators"
        },
        "Microgravity-process zone": {
            "microgravity_subtruss", "microgravity_pods",
            "microgravity_isolation_mounts",
        },
        "Thermal-gradient zone": {
            "thermal_gradient_hot", "thermal_gradient_mid", "thermal_gradient_cold",
        },
    }

    all_v_full = np.concatenate([p[0] for p in pieces], axis=0)
    full_cmin, full_cmax = all_v_full.min(0), all_v_full.max(0)
    full_center = (full_cmin + full_cmax) / 2.0
    full_ext = (full_cmax - full_cmin) * 1.04

    fig = plt.figure(figsize=(26, 18), facecolor="#0a0a14")

    for idx, (title, hl) in enumerate(zones.items()):
        ax = fig.add_subplot(2, 2, idx + 1, projection="3d")
        ax.set_facecolor("#0a0a14")
        try:
            ax.set_proj_type("ortho")
        except Exception:
            pass

        # If highlighting a zone, frame the view on that zone's bounding box
        if hl is not None:
            zone_v = np.concatenate(
                [p[0] for p in pieces if p[3] in hl], axis=0
            )
            zmin, zmax = zone_v.min(0), zone_v.max(0)
            center = (zmin + zmax) / 2.0
            # Pad with at least 25 m on each side so context is visible
            pad = max((zmax - zmin).max() * 0.15, 25.0)
            ext = (zmax - zmin) + 2 * pad
            # Force a minimum cube so very small zones still get a sensible box
            min_side = 50.0
            ext = np.maximum(ext, min_side)
        else:
            center = full_center
            ext = full_ext.copy()

        dx, dy, dz = ext

        for verts, tris, rgba, name in pieces:
            triangles = verts[tris]
            if hl is not None and name not in hl:
                r, g, b, _ = rgba
                face = (r * 0.20 + 0.03, g * 0.20 + 0.03, b * 0.20 + 0.03, 0.18)
            else:
                face = rgba
            coll = Poly3DCollection(
                triangles, facecolor=face,
                edgecolor=(1, 1, 1, 0.10), linewidths=0.05,
            )
            ax.add_collection3d(coll)

        ax.set_xlim(center[0] - dx / 2.0, center[0] + dx / 2.0)
        ax.set_ylim(center[1] - dy / 2.0, center[1] + dy / 2.0)
        ax.set_zlim(center[2] - dz / 2.0, center[2] + dz / 2.0)
        try:
            ax.set_box_aspect((dx, dy, dz), zoom=2.4)
        except TypeError:
            try:
                ax.set_box_aspect((dx, dy, dz))
            except Exception:
                pass
        ax.view_init(elev=22, azim=35 + idx * 5)
        ax.set_axis_off()
        ax.set_title(title, color="white", fontsize=18, pad=4)

    plt.subplots_adjust(left=0.0, right=1.0, top=0.97, bottom=0.0,
                        wspace=0.0, hspace=0.04)
    plt.savefig(out_path, dpi=120, facecolor="#0a0a14")
    plt.close(fig)


# ============================================================================
# MAIN
# ============================================================================

PART_DESCRIPTIONS = {
    "main_truss":
        "Main triangular truss — the 200 m primary structural spine. "
        "Three longerons, transverse rings every 5 m, face diagonals.",
    "central_hub":
        "Central hub — avionics, power conditioning, propellant interfaces, "
        "and 4 radial Starship-class docking ports.",
    "vacuum_pods":
        "Vacuum-process pods (8). Open-aperture MBE / vapor deposition / "
        "ultra-clean semiconductor work. Mounted on the -Y (anti-sun) face "
        "to minimize UV soak, atomic-oxygen flux, and outgassing recapture.",
    "vacuum_aperture_rings":
        "Gold aperture rings — 3 m circular openings on each vacuum pod's "
        "-Y face, the process chamber looking directly into deep space.",
    "vacuum_local_radiators":
        "Vacuum-pod local radiators — small ±X panels per pod for dumping "
        "process heat without loading the station-level thermal bus.",
    "vacuum_shutters":
        "Aperture shutters (8) — half-open in the model. Each vacuum pod "
        "has a sliding shutter blade with rails and an actuator can. The "
        "shutter closes during reboosts, thruster firings, and docking "
        "approaches to protect the chamber from debris and thruster-plume "
        "contamination. A single contamination event without a shutter "
        "can ruin a chamber permanently.",
    "vacuum_load_locks":
        "Load-lock chambers (8) — small boxes on the +Y back of each "
        "vacuum pod with their own circular hatch flange. Substrates "
        "enter and leave via the load lock so the main process chamber "
        "never has to be re-vented to vacuum. Without a load lock the "
        "pod could grow exactly one wafer in its lifetime.",
    "vacuum_cryocoolers":
        "Cryocoolers (4, on MBE pods only) — compressor + cold-head + "
        "regulator on each MBE pod's -X face. Real MBE needs ~77 K "
        "cryopumping behind the source to keep background pressure "
        "ultralow. Passive radiators cannot reach 77 K — this is an "
        "active Stirling- or pulse-tube refrigerator.",
    "vacuum_ram_baffles":
        "Ram baffles (8) — small flat plates on the +Z (velocity) side of "
        "each pod. They shadow the aperture from atomic-oxygen flux and "
        "ram-direction debris. At 800 km AO is already four orders of "
        "magnitude below ISS, so these are a small refinement, but they "
        "would matter at lower altitudes.",
    "microgravity_subtruss":
        "Microgravity sub-truss — RELOCATED. The original architecture "
        "put this at the -Z end of the main truss (~115 m from CoM, "
        "where gravity-gradient acceleration is ~43 µg, two orders of "
        "magnitude above what microgravity science needs). It now extends "
        "along -X from a point next to the central hub at z ≈ 0 (the "
        "station CoM), putting the pods at r ≈ 16-25 m from CoM and "
        "reducing gravity-gradient acceleration to ~6-9 µg.",
    "microgravity_pods":
        "Microgravity-process pods (6) — sealed, controlled-environment "
        "payloads. Protein crystallization, ZBLAN fiber draw, alloy "
        "solidification. Now clustered tightly near the sub-truss "
        "midpoint (the point closest to the CoM), instead of spread "
        "along its length, to minimize internal gravity-gradient "
        "variation between pods.",
    "microgravity_isolation_mounts":
        "Soft-mount tether bundle (6 tethers + 6 damper pucks) — the only "
        "mechanical link between the main truss and the µg sub-truss. "
        "Each tether is a long thin rod with a damper-puck soft-mount "
        "stage in the middle, representing ~0.1 Hz natural-frequency "
        "6-DOF active isolation (e.g. ARIS-class). Rigid struts would "
        "transmit disturbance almost perfectly and defeat the entire "
        "purpose of the zone.",
    "thermal_gradient_hot":
        "Thermal-gradient pods, HOT segment (+Y / sunward). Each pod has a "
        "3 × 3 m sunward absorber plate sized to capture ~11 kW of solar "
        "flux (1361 W/m² × 9 m² × ~0.9 absorptivity). The dawn-dusk SSO "
        "sun direction is essentially constant in the body frame, so no "
        "tracking gimbal is needed.",
    "thermal_gradient_mid":
        "Thermal-gradient pods, MID segment — transition zone between hot "
        "and cold ends. Direction-of-growth zone for directional "
        "solidification, melt-zone for zone refining. Wrapped in the MLI "
        "jacket so heat doesn't radiate sideways.",
    "thermal_gradient_cold":
        "Thermal-gradient pods, COLD segment + 6 × 6 m radiator (-Y / "
        "anti-sun). The radiator was scaled up 4× from the original 3 × 3 "
        "to actually be able to reject the absorbed solar input plus "
        "process heat (~17 kW at 300 K). Edge-on to the sun (normal ±X) "
        "so it sees only deep space.",
    "thermal_gradient_heat_pipes":
        "Heat pipes (4 per pod, 16 total) — copper external tubes running "
        "the full length of each thermal-gradient pod, transporting heat "
        "from the hot absorber to the cold-end radiator. Solid conduction "
        "through the pod walls cannot move 11 kW over 12 m by orders of "
        "magnitude — heat pipes (or loop heat pipes with a working fluid) "
        "are the only realistic option for this geometry.",
    "thermal_gradient_mli":
        "MLI insulation jacket — multi-layer insulation wrap covering the "
        "middle ~70 % of each thermal-gradient pod. Without it, heat "
        "would radiate sideways from the pod walls and the axial gradient "
        "would flatten before reaching the cold end. Real directional-"
        "solidification furnaces are heavily wrapped in MLI for the same "
        "reason.",
    "solar_panels":
        "Solar arrays — 2 × 50 × 25 m wings, face-on to +Y sun. In a "
        "dawn-dusk SSO they're illuminated continuously and never need "
        "battery support beyond reaction-wheel buffering.",
    "solar_cell_grid":
        "Photovoltaic cell grid — schematic ribs indicating cell layout.",
    "solar_booms":
        "Solar array deployment booms — short booms that hold each wing "
        "outboard of the central hub along ±X so the wings cannot shadow "
        "the thermal-gradient pods.",
    "primary_radiators":
        "Primary radiators — 2 × 70 × 25 m panels, edge-on to the sun "
        "(normal ±X). Edge-on orientation minimizes parasitic solar "
        "absorption, maximizing net heat rejection.",
    "radiator_booms":
        "Radiator deployment booms — short ±X booms holding each radiator "
        "panel outboard of the hub in the -Y shadow region.",
    "thermal_bus_hot":
        "Thermal bus, hot supply (copper). Routes warm coolant from the "
        "process pods to the central manifold and out to the radiators. "
        "Visually traced along the +X / -Y bottom longeron.",
    "thermal_bus_cold":
        "Thermal bus, cold return (pale blue). Returns cold coolant from "
        "the radiators back to the pods. Routed along the -X / -Y bottom "
        "longeron, opposite the hot supply.",
    "robotic_arm":
        "Robotic servicing rail + 3-segment arm. Linear rail along the "
        "+X face of the main truss. Does NOT extend onto the microgravity "
        "sub-truss — the arm itself is one of the loudest disturbance "
        "sources on the station.",
    "adcs_cluster":
        "ADCS cluster — reaction wheel housing, four corner thruster "
        "pods, star trackers, and antennas at the +Z end of the main truss.",
    "spine_hull":
        "Spine hull — unpressurized whipple-shield wrapper around the "
        "central section of the main truss. Encloses the central hub, the "
        "robotic rail and arm, the thermal bus piping, and the truss "
        "interior, giving them MMOD protection without the mass of a "
        "pressurized hull (~10 kg/m² vs ~150). Cut with circular apertures "
        "on the -Y face for vacuum-pod openings, top + bottom holes for "
        "the thermal-gradient pods that span Y, and four radial holes for "
        "the docking ports. Stops short of the truss ends so the ADCS "
        "cluster and the microgravity transition stay exposed.",
    "microgravity_hull":
        "Microgravity hull — separate cylindrical whipple shield around "
        "the isolated microgravity sub-truss and its six sealed pods. "
        "Mechanically separate from the spine hull so the µg zone's "
        "vibration isolation is preserved. No cutouts: the µg pods are "
        "controlled-environment processes that don't need to see space, "
        "so they live entirely inside.",
}


def export_viewer_data(here, manifest):
    """
    Bundle all per-part STLs as base64 into a single JS file the
    interactive viewer loads via a plain <script> tag. This avoids the
    CORS / sandbox restrictions of fetch() under file:// and removes the
    need for a running HTTP server entirely.
    """
    import base64
    parts_payload = []
    for part in manifest["parts"]:
        stl_path = os.path.join(here, part["file"])
        with open(stl_path, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode("ascii")
        parts_payload.append({
            "name": part["name"],
            "color": part["color"],
            "opacity": part["opacity"],
            "description": part["description"],
            "stl_b64": b64,
        })

    out_path = os.path.join(here, "viewer_data.js")
    import json
    with open(out_path, "w") as f:
        f.write("// Auto-generated by leo_factory.py — do not edit by hand.\n")
        f.write("window.STATION_DATA = ")
        json.dump({"parts": parts_payload}, f)
        f.write(";\n")
    return out_path


def export_parts(assy, parts_dir):
    """
    Export each top-level assembly child to its own STL file inside
    `parts_dir`, plus a manifest.json that lists name, color, and a
    short human-readable description for the interactive viewer.
    """
    import json
    os.makedirs(parts_dir, exist_ok=True)

    manifest = {"parts": []}
    for child in assy.children:
        obj = child.obj
        if obj is None:
            continue
        name = child.name
        if isinstance(obj, cq.Workplane):
            wp = obj
        else:
            wp = cq.Workplane("XY").add(obj)
        out_path = os.path.join(parts_dir, f"{name}.stl")
        cq.exporters.export(
            wp, out_path,
            tolerance=0.5, angularTolerance=0.5,
        )
        col = child.color
        if col is not None:
            r, g, b, a = col.toTuple()
        else:
            r, g, b, a = 0.7, 0.7, 0.7, 1.0
        manifest["parts"].append({
            "name": name,
            "file": f"parts/{name}.stl",
            "color": [r, g, b],
            "opacity": a,
            "description": PART_DESCRIPTIONS.get(name, name.replace("_", " ")),
        })

    with open(os.path.join(parts_dir, "..", "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    return manifest


def main():
    here = os.path.dirname(os.path.abspath(__file__))

    print("Building station assembly...")
    assy = build_station()

    print("Exporting STEP...")
    step_path = os.path.join(here, "leo_factory.step")
    assy.save(step_path)

    print("Exporting STL...")
    stl_path = os.path.join(here, "leo_factory.stl")
    compound = assy.toCompound()
    cq.exporters.export(
        cq.Workplane("XY").add(compound),
        stl_path,
        tolerance=0.5,
        angularTolerance=0.5,
    )

    print("Exporting per-part STLs for interactive viewer...")
    manifest = export_parts(assy, os.path.join(here, "parts"))

    print("Bundling embedded STL data for the offline viewer...")
    export_viewer_data(here, manifest)

    print("Rendering preview...")
    render(assy, os.path.join(here, "leo_factory_preview.png"), view="iso")

    print("Rendering zones panel...")
    render_zones_panel(assy, os.path.join(here, "leo_factory_zones.png"))

    print("Done.")
    print(f"  STEP    -> {step_path}")
    print(f"  STL     -> {stl_path}")
    print(f"  Preview -> leo_factory_preview.png")
    print(f"  Zones   -> leo_factory_zones.png")


if __name__ == "__main__":
    main()
