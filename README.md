# LEO Industrial Factory Station — parametric CadQuery model

A robot-native, unpressurized orbital manufacturing platform, modeled
parametrically in Python with [CadQuery](https://cadquery.readthedocs.io/) 2.x.
The station is fully automated — no humans, no pressurized modules, no ECLSS —
and its architecture exists to exploit three space-native manufacturing
advantages **simultaneously**: hard vacuum, microgravity, and extreme thermal
gradients. Each advantage demands a different physical arrangement, and the
geometry of the station is the visible record of that compromise.

## Files

| File | Purpose |
|------|---------|
| `leo_factory.py` | Single parametric build script (one function per major component, one per zone). |
| `leo_factory.step` | STEP export for downstream CAD use. |
| `leo_factory.stl`  | STL export for visualization / 3D print. |
| `leo_factory_preview.png` | Isometric render of the full station. |
| `leo_factory_zones.png` | 4-up panel: full station + each manufacturing zone highlighted in its own bounded view. |

## Quick start

```bash
pip install cadquery trimesh numpy-stl matplotlib
python3 leo_factory.py
```

This regenerates all four output files in place. There are no runtime
arguments; everything is controlled by top-level parameters in
`leo_factory.py`.

## Orbital frame and conventions

The station sits in an ~800 km dawn-dusk sun-synchronous orbit, which
gives it (a) continuous solar exposure (no eclipses), (b) a stable thermal
environment, and (c) a fixed sun direction in the body frame.

| Axis | Direction | Used by |
|------|-----------|---------|
| **+Y** | sun vector (constant) | solar arrays face this; absorbers point at it |
| **+Z** | velocity vector | main truss runs along it |
| **−X** | nadir | (no major hardware; communications would face here) |
| **+X** | anti-nadir | robotic rail, primary radiator side A |
| **−Y** | anti-sun (deep cold) | vacuum pods, primary radiator side B |
| origin | geometric center of the main truss | |

In the rendered images, coordinates are remapped so the truss runs
horizontally for readability. The actual STEP / STL files are in the
station-frame above.

## Architectural thesis — three zones, three different physics

### 1. Vacuum-process zone (−Y face of main truss)

**Physical driver:** Free, hard, infinitely-pumpable vacuum is the most
valuable thing space gives a process engineer — but only if you can avoid
contaminating it. The dawn-dusk SSO −Y face is the coldest, dimmest, lowest
atomic-oxygen-flux direction available, and the truss itself shadows it from
the sun. So that is where the open-aperture processes (MBE, vapor
deposition, ultra-clean semiconductor work) live.

**Geometric expression:** Eight pods mounted on the −Y face of the main
truss, each with a 3 m circular aperture opening directly into space. Pods
are arranged in 4 longitudinal pairs spaced 15 m apart. Half are flat-aperture
deposition chambers, half are recessed-aperture MBE / source pods. Each pod
carries small ±X local radiators for its own process heat; the bulk station
load goes through the central thermal bus.

### 2. Microgravity-process zone (isolated sub-truss)

**Physical driver:** Vibration is the enemy of microgravity processing.
Reaction wheels, cryocoolers, gimbals, deposition pumps, and the robotic
servicing arm all generate broadband disturbance. To get a meaningfully
quiet platform you have to mechanically *separate* sensitive payloads from
the busy spine of the station — not just damp them in place.

**Geometric expression:** A smaller secondary triangular truss extends
from the −Z end of the main truss, offset by a visible 15 m gap and connected
only through six explicit vibration-isolation mounts (the short fat
cylinders bridging the gap). The sub-truss is intentionally simpler:
smaller cross-section, no diagonal bracing, lighter color. **The robotic rail
does not extend onto it.** The visible service access for these pods is a
much smaller arm at the sub-truss base, used only during scheduled quiet
periods. If you can read the model, you should immediately see that this
zone is "isolated and quiet" while the main truss is "active and busy."

### 3. Thermal-gradient zone (spanning the truss in Y)

**Physical driver:** Some processes need a sustained, large temperature
differential — directional solidification of alloys, cryogenic distillation,
zone-refining, certain superconductor fabrication routes. On Earth you build
this with refrigerators and resistive heaters and pay for both. In a
dawn-dusk SSO, the orbit *is* the gradient: +Y always sees the sun, −Y
always sees deep space at ~3 K background. A pod that physically bridges
those two regions can use that gradient as a free process resource.

**Geometric expression:** Four cylindrical pods, 12 m long × 2 m diameter,
spanning the truss cross-section in the Y direction with a sunward absorber
plate on +Y and a dedicated cold-end radiator on −Y. The pod body is split
into hot / mid / cold segments and color-coded so the thermal axis is
immediately legible. These pods are the architectural signature of the
station.

## Component list

| Component | Function | Notes |
|-----------|----------|-------|
| **Main truss** | Primary structural spine, hosts vacuum and thermal-gradient zones | 200 m, triangular cross-section, 5 m per side, longerons + rings + face diagonals every 5 m bay |
| **Central hub** | Avionics, power conditioning, docking | 8 m × 10 m cylinder with 4 radial Starship-class docking ports |
| **Vacuum pods (8)** | Open-aperture vacuum processing | Pairs along −Y face, gold aperture rings, ±X local radiators |
| **Microgravity sub-truss + pods (6)** | Quiet, sealed-environment processing | Isolated by 15 m gap and 6 vibration mounts; no robotic rail extension |
| **Thermal-gradient pods (4)** | Sun-to-shadow process pods | Span the truss in Y, hot absorber + cold radiator, three-segment body |
| **Solar arrays (2 × 50 × 25 m)** | Power | Face-on to +Y sun, mounted on ±X booms from the hub, in the +Y/sunlit volume |
| **Primary radiators (2 × 70 × 25 m)** | Station-level heat rejection | Edge-on to sun (normal ±X), mounted on ±X booms from the hub, in the −Y shadow |
| **Thermal bus** | Cooling fluid distribution | Copper hot supply + pale-blue cold return; routed along the −Y longerons |
| **Robotic rail + arm** | Servicing | Linear rail + 3-segment arm, +X side of main truss only |
| **ADCS cluster** | Attitude / orbit | Reaction wheel + 4 thruster pods + star trackers + antenna at +Z end |

## Color scheme

| Color | Part |
|-------|------|
| Medium grey | Main truss |
| Light grey | Microgravity sub-truss (visually distinct: "clean") |
| Dark grey | Central hub |
| Dark blue | Vacuum pods |
| Gold | Vacuum pod aperture rings |
| Off-white | Microgravity pods (cleanroom read) |
| Orange | Thermal-gradient hot end |
| Blue | Thermal-gradient cold end |
| Dark blue + gold grid | Solar arrays |
| White / silver | Primary radiators |
| Copper | Thermal bus, hot supply |
| Pale blue | Thermal bus, cold return |
| Safety yellow | Robotic arm |

## Parameters (top of `leo_factory.py`)

All dimensions in meters. The most useful knobs to twist:

```python
# Geometry
MAIN_TRUSS_LENGTH       = 200.0
MAIN_TRUSS_SIDE         = 5.0
MG_SUBTRUSS_LENGTH      = 60.0
MG_SUBTRUSS_OFFSET      = 15.0     # the visible isolation gap
HUB_DIA                 = 8.0
HUB_LENGTH              = 10.0

# Power & thermal
SA_WING_LONG            = 50.0
SA_WING_SHORT           = 25.0     # → 1250 m² per wing, 2500 m² total
RAD_LONG                = 70.0
RAD_SHORT               = 25.0     # → 1750 m² per panel, 3500 m² total

# Process zones
N_VACUUM_PODS           = 8
VAC_APERTURE_DIA        = 3.0
N_MG_PODS               = 6
N_TG_PODS               = 4
TG_POD_LENGTH           = 12.0     # spans the truss in Y
TG_POD_DIA              = 2.0
```

Change any of these and rerun the script. The assembly, STEP, STL, and
both renders will be regenerated to match.

## Modification guide

* **Add more vacuum pods** — bump `N_VACUUM_PODS` (must remain even, since
  pods are arranged in pairs) and the `vacuum_pod_positions()` function will
  automatically lay them out along the truss.
* **Make the microgravity zone larger or further isolated** — change
  `MG_SUBTRUSS_LENGTH` and `MG_SUBTRUSS_OFFSET`. The vibration-isolation
  mounts and the visible gap rescale together.
* **Change the thermal-gradient pod count or spacing** — adjust `N_TG_PODS`
  and `TG_POD_SPACING`.
* **Re-color a part** — every part is added to the assembly with an
  explicit `Color`; change the constants near the top of the file (`C_*`).
* **Add a new component** — write a `build_<thing>()` function that returns
  one or more `cq.Compound` objects, then call `assy.add(...)` in
  `build_station()`.

## Which design choices come from which physical constraint

| Geometric choice | Driving physics |
|------------------|-----------------|
| Triangular truss with apex on +Y | Maximizes structural depth in the sun-shadow direction (where the thermal load is largest) and gives a clean −Y face for the vacuum pods. |
| Vacuum pods on −Y, not +Y | Avoid solar UV soak, atomic-oxygen flux, and outgassing recapture. |
| Solar arrays face-on to +Y, perpendicular to truss in ±X | Maximize sun capture in dawn-dusk SSO; do not shadow the thermal-gradient pods that span the truss in Y. |
| Primary radiators edge-on to sun (normal ±X) | Solar absorption proportional to projected area → edge-on minimizes parasitic heating, maximizing net heat rejection. |
| Microgravity sub-truss physically separated by a gap and vibration mounts | Mechanical isolation from broadband disturbance generated by the busy main truss. Damping in place is insufficient for the µg ranges that microgravity science needs. |
| Robotic rail does NOT extend onto the microgravity sub-truss | The arm itself is one of the largest disturbance sources on the station — putting it on the µg structure would defeat the purpose of the zone. |
| Thermal-gradient pods physically span the truss cross-section in Y | The pod uses the orbit's geometry (sun on one end, deep space on the other) as a sustained dT source. Building the gradient with active hardware would cost continuous power. |
| Visible scale dominance of solar arrays + radiators over process pods | In real space facilities, power and thermal-rejection mass exceed payload mass. The model would be misleading if the pods looked larger than the radiators. |

## Suggestions for what to iterate on next

1. **Pod-level detail.** Each pod is currently a stylized envelope. The next
   level would be process-specific internals: an MBE source housing with
   source crucibles and a substrate manipulator, a directional solidification
   pod with explicit melt/growth/cooling zones and a heat-pipe bridge, an
   actual ZBLAN draw tower in one of the µg pods.
2. **Resupply logistics.** The four hub docking ports are placeholders;
   building Starship-class clearance volumes around them and a propellant
   depot interface would make the architectural argument about cargo
   throughput visible.
3. **Power and thermal budget validation.** Compute heat-rejection capacity
   from radiator area × emissivity × σ × T⁴, sanity-check it against the
   power input from the solar arrays × inverter efficiency × payload duty
   cycle. Right now the radiator and array sizes are spec'd inputs; they
   should be derived from a real budget.
4. **Vibration / disturbance modeling.** Compute the effective microgravity
   level reachable on the isolated sub-truss given the disturbance spectrum
   of the main truss (reaction wheels, robotic arm, fluid pumps) and the
   isolation mount transmissibility. This would let you defend the
   `MG_SUBTRUSS_OFFSET` parameter quantitatively.
5. **Dual-axis solar tracking.** A dawn-dusk SSO does not require dual-axis
   tracking — single-axis is enough — but adding the gimbal geometry would
   make the boom assembly look correct.
6. **Atomic-oxygen and micrometeoroid shielding.** The vacuum-pod aperture
   rings are currently decorative gold; on a real platform they would be
   shutters or sacrificial coatings. Modeling the shutter mechanism would
   be a worthwhile next pass.
7. **Multi-station fleet.** The architecture is already parametric; running
   a parameter sweep and rendering a constellation of variants (different
   process-mix priorities) would make the design space visible.
