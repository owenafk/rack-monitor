"""
Rack environment monitor enclosure
ESP32-C3 Super Mini + AHT10 + LM393 rain-sensor driver board

Two parts:
  mount  - plate that sits against the side of a rack post, with an L-ear that
           bolts to the post's front rack holes. Board support rails on its face.
  cover  - snap-on shell. Holds the boards down with corner clamps, has the
           USB-C opening, a partition that isolates the AHT10 from ESP heat,
           vents, and four snap tongues that hook behind the mount plate.

Frame (as mounted): X = sideways (0 = face against the post side, + into box)
                    Y = depth   (0 = rack front face, + toward rear)
                    Z = vertical
All dimensions in mm.
"""
import cadquery as cq
from cadquery import Vector as V

# ------------------------------------------------------------------ params
PT = 3.0          # mount plate thickness
W = 2.0           # cover wall
CL = 0.25         # sliding clearance between parts
PH = 39.5         # plate height (Z). Cover outer = PH + 2*(W+CL) = 44.0 (≈1U)
XTOP = 23.0       # cover outer face (X)
XIN = XTOP - W    # cover inner ceiling

ET = 4.0          # ear thickness (Y)
EW = 23.0         # ear reach past the plate back face (-X)
U = 44.45
HOLE_DZ = 31.75   # outer two holes of one EIA-310 rack unit
SLOT_W = 6.5      # M6 clearance (also fits M5 / 10-32)
SLOT_X = (5.0, 15.0)  # hole-centre distance from plate back face (adjustable)

# Rain driver board has 90-degree headers at both ends: room for a DuPont plug on each.
# If you solder wires straight to the pins instead, set PLUG = 7.5 for a shorter box.
PLUG = 14.0       # DuPont housing length beyond the board edge
BEND = 4.0        # room for the 4-pin plug's wires to turn toward the ESP

# boards: (Y0, Z0, length_Y, width_Z, pcb_t, rail_h)
ESP = dict(y0=W + 0.2, z0=19.5, ly=22.52, wz=18.0, t=1.0, rail=2.0)
RAIN = dict(y0=W + BEND + PLUG, z0=1.5, ly=30.8, wz=15.3, t=1.6, rail=3.5)
PL = round(RAIN["y0"] + RAIN["ly"] + PLUG + 0.3, 2)   # plate length (Y)

PART_T = 1.6
AHT_BAY = 14.7                       # inner length of the AHT10 bay
YPART = PL - AHT_BAY - PART_T        # vertical partition (front of AHT bay)
ZPART = 18.4                         # horizontal partition (floor of AHT bay)
AHT = dict(ly=10.7, wz=15.3, t=1.6, rail=2.0, cl=0.15)   # measured module
AHT["y0"] = YPART + PART_T + (AHT_BAY - AHT["ly"]) / 2
AHT["z0"] = ZPART + 3.1
TONGUES_Y = (11.0, PL - 11.0)
TONGUE_W = 6.0
TONGUE_SLOT = 0.8
TONGUE_L = 16.0
BARB = 1.0        # barb inward reach past plate edge
BARB_X = 1.2      # barb height (X) - sits in recess in plate back
RECESS_X = 1.45
OV = 1.2          # clamp lip overlap onto PCB
LIP_GAP = 0.3     # clearance above nominal PCB (fits up to +0.25 thicker PCB)


def box(x0, x1, y0, y1, z0, z1):
    return (cq.Workplane("XY")
            .box(x1 - x0, y1 - y0, z1 - z0, centered=False)
            .translate((x0, y0, z0)))


def prism_xz(pts, y0, y1):
    """Polygon in the XZ plane, extruded along +Y from y0 to y1."""
    wire = cq.Wire.makePolygon([V(x, y0, z) for x, z in pts], close=True)
    solid = cq.Solid.extrudeLinear(cq.Face.makeFromWires(wire), V(0, y1 - y0, 0))
    return cq.Workplane("XY").add(solid)


def pcb_x(b):
    bot = PT + b["rail"]
    return bot, bot + b["t"]


def board_bbox(b, grow=0.0):
    return (b["y0"] - grow, b["y0"] + b["ly"] + grow,
            b["z0"] - grow, b["z0"] + b["wz"] + grow)


# ------------------------------------------------------------------ mount
def make_mount():
    plate = box(0, PT, 0, PL, 0, PH)

    # L-ear across the front face of the rack post
    zc = PH / 2
    ear = (box(-EW, PT, 0, ET, zc - U / 2 + 0.2, zc + U / 2 - 0.2)
           .edges("|Y and <X").fillet(3.0))
    m = plate.union(ear)
    for dz in (-HOLE_DZ / 2, HOLE_DZ / 2):
        slot = (cq.Workplane("XZ").workplane(offset=1)
                .center(-(SLOT_X[0] + SLOT_X[1]) / 2, zc + dz)
                .slot2D(SLOT_X[1] - SLOT_X[0] + SLOT_W, SLOT_W, 0)
                .extrude(-(ET + 2)))
        m = m.cut(slot)

    # support rails (all run along Y -> vertical when printed standing on the ear)
    def rails(b, zs, y_trim):
        y0, y1, _, _ = board_bbox(b)
        out = None
        for z in zs:
            r = box(PT - 0.01, PT + b["rail"], y0 + y_trim[0], y1 - y_trim[1], z - 0.75, z + 0.75)
            out = r if out is None else out.union(r)
        return out

    ez = ESP["z0"] + ESP["wz"] / 2
    m = m.union(rails(ESP, (ez - 5, ez + 5), (0.8, 0.5)))
    rz = RAIN["z0"] + RAIN["wz"] / 2
    m = m.union(rails(RAIN, (rz - 4, rz + 4), (4.5, 4.5)))   # clear header pin stubs
    m = m.union(rails(AHT, (AHT["z0"] + 6, AHT["z0"] + 12), (0.3, 0.3)))

    # AHT10 locating walls either side (Y-running), 0.1 mm per side: the module
    # drops in snug before the cover goes on. Stop just below the PCB top so
    # they never touch the pin pads.
    ay0, ay1, az0, az1 = board_bbox(AHT)
    _, atop = pcb_x(AHT)
    for za, zb in ((az0 - 0.1 - 1.2, az0 - 0.1), (az1 + 0.1, az1 + 0.1 + 1.2)):
        m = m.union(box(PT - 0.01, atop - 0.2, ay0 + 1.3, ay1 - 1.3, za, zb))

    # snap recesses in the back face + lead-in chamfers on the front edges
    for yc in TONGUES_Y:
        ya, yb = yc - TONGUE_W / 2 - 0.5, yc + TONGUE_W / 2 + 0.5
        m = m.cut(box(-1, RECESS_X, ya, yb, -1, BARB + 0.3))
        m = m.cut(box(-1, RECESS_X, ya, yb, PH - BARB - 0.3, PH + 1))
        m = m.cut(prism_xz([(PT - 1.0, -0.1), (PT + 0.1, -0.1), (PT + 0.1, 1.0)], ya, yb))
        m = m.cut(prism_xz([(PT - 1.0, PH + 0.1), (PT + 0.1, PH + 0.1), (PT + 0.1, PH - 1.0)], ya, yb))
    return m


# ------------------------------------------------------------------ cover
def make_cover():
    z_lo, z_hi = -CL - W, PH + CL + W
    y_back = PL + CL + W
    c = box(0, XTOP, 0, y_back, z_lo, z_hi)
    c = c.edges("(|Y and >X) or (|X and >Y) or (|Z and >X and >Y)").fillet(2.0)

    c = c.cut(box(-1, XIN, W, PL + CL, -CL, PH + CL))            # cavity
    c = c.cut(box(-1, PT + 0.1, -1, PL + CL, -CL, PH + CL))       # plate envelope
    c = c.cut(box(-1, PT + CL, -1, ET + CL, z_lo - 1, z_hi + 1))  # ear notch

    # stop ribs on the inside of the top/bottom walls: rest on the plate face
    rib_lo = box(PT, PT + 1.0, ET + CL, PL + CL, -CL - 0.1, 0.9)
    rib_hi = box(PT, PT + 1.0, ET + CL, PL + CL, PH - 0.9, PH + CL + 0.1)
    ribs = rib_lo.union(rib_hi)
    for yc in TONGUES_Y:
        ribs = ribs.cut(box(-1, PT + 2, yc - 4.2, yc + 4.2, z_lo - 1, z_hi + 1))
    c = c.union(ribs)

    # L-shaped partition boxing the AHT10 into the upper-rear corner, away from
    # ESP heat; wire notch at the plate. Rain board's rear plug runs underneath.
    part = box(PT + 0.3, XIN + 0.1, YPART, YPART + PART_T, ZPART, PH + CL + 0.1)
    part = part.union(box(PT + 0.3, XIN + 0.1, YPART, PL + CL + 0.1, ZPART, ZPART + PART_T))
    part = part.cut(box(0, PT + 6.0, YPART - 1, YPART + PART_T + 1, ZPART + PART_T, AHT["z0"] + 5.5))
    c = c.union(part)

    # corner clamps: lip over the PCB corner + stop outside the edge
    def clamp(b, corner, ov=OV, t=1.2, lip=True):
        y0, y1, z0, z1 = board_bbox(b, b.get("cl", CL))
        _, top = pcb_x(b)
        cy = y0 if corner[0] == 0 else y1
        cz = z0 if corner[1] == 0 else z1
        sy = -1 if corner[0] == 0 else 1
        sz = -1 if corner[1] == 0 else 1
        ya, yb = sorted((cy + sy * t, cy - sy * ov))
        za, zb = sorted((cz + sz * t, cz - sz * ov))
        col = box(PT + 0.8, XIN + 0.1, ya, yb, za, zb)
        keep_out = box(0, top + LIP_GAP if lip else XIN + 1, y0, y1, z0, z1)
        return col.cut(keep_out)

    for corner in ((1, 0), (1, 1)):                   # ESP rear corners (front = buttons)
        c = c.union(clamp(ESP, corner))
    for corner in ((0, 0), (0, 1), (1, 0), (1, 1)):
        c = c.union(clamp(RAIN, corner))
    for corner in ((0, 1), (1, 1)):                   # AHT10 far end
        c = c.union(clamp(AHT, corner, ov=0.8))
    for corner in ((0, 0), (1, 0)):                   # AHT10 pin end: tiny lips clear of the pads
        c = c.union(clamp(AHT, corner, ov=0.5))

    # USB-C: presser on top of the receptacle shell + opening for the plug overmold
    _, etop = pcb_x(ESP)
    ez = ESP["z0"] + ESP["wz"] / 2
    c = c.union(box(etop + 3.26 + 0.25, XIN + 0.1, 3.0, 8.0, ez - 3, ez + 3))
    usb_x = etop + 1.63
    usb = (cq.Workplane("XZ").workplane(offset=1).center(usb_x, ez)
           .rect(7.2, 12.6).extrude(-(W + 2)).edges("|Y").fillet(2.5))
    c = c.cut(usb)

    # vents ---------------------------------------------------------------
    def top_slot(y, za, zb, w=1.6):
        return box(XIN - 0.5, XTOP + 1, y - w / 2, y + w / 2, za, zb)

    def side_slot(y, lo=True, w=1.6):
        z = (z_lo - 1, -CL + 0.01) if lo else (PH + CL - 0.01, z_hi + 1)
        return box(7.0, XIN - 2.0, y - w / 2, y + w / 2, *z)

    ay = YPART + PART_T
    for y in (ay + 4.1, ay + 7.1, ay + 10.1):         # AHT bay ceiling
        c = c.cut(top_slot(y, AHT["z0"] + 1.0, AHT["z0"] + 15.5))
    for z in [ZPART + 3.6 + 3.2 * i for i in range(6)]:   # AHT bay rear wall
        c = c.cut(box(6.0, XIN - 2.0, PL + CL - 0.5, y_back + 1, z - 0.8, z + 0.8))
    for y in (PL - 5.1, PL - 2.1):                    # AHT bay top wall
        c = c.cut(side_slot(y, False))
    for y in (11.0, 14.0, 17.0, 20.0):                # over the ESP
        c = c.cut(top_slot(y, 22.0, 35.0))
    for y in range(18, int(YPART) - 2, 3):            # exhaust, top wall
        c = c.cut(side_slot(y, False))
    for y in (22, 25, 28, 31):                        # intake, bottom wall
        c = c.cut(side_slot(y, True))

    # rain probe cable: straight out the back, in line with the 2-pin plug
    _, rtop = pcb_x(RAIN)
    c = c.cut(cq.Workplane("XZ").workplane(offset=-(PL - 1))
              .center(rtop + 1.27, RAIN["z0"] + RAIN["wz"] / 2).circle(3.5).extrude(-(W + 3)))

    # snap tongues: free the wall either side, then add the barbs
    for yc in TONGUES_Y:
        for ys in (yc - TONGUE_W / 2 - TONGUE_SLOT, yc + TONGUE_W / 2):
            c = c.cut(box(-1, TONGUE_L, ys, ys + TONGUE_SLOT, z_lo - 1, -CL + 0.01))
            c = c.cut(box(-1, TONGUE_L, ys, ys + TONGUE_SLOT, PH + CL - 0.01, z_hi + 1))
        ya, yb = yc - TONGUE_W / 2 + 0.25, yc + TONGUE_W / 2 - 0.25
        c = c.union(prism_xz([(0, -CL - 0.6), (BARB_X, -CL - 0.6), (BARB_X, BARB), (0, -CL)], ya, yb))
        c = c.union(prism_xz([(0, PH + CL + 0.6), (BARB_X, PH + CL + 0.6),
                              (BARB_X, PH - BARB), (0, PH + CL)], ya, yb))
    return c


# ------------------------------------------------------------------ dummies (render/check only)
def make_boards():
    parts = {}
    # ESP32-C3 Super Mini
    b, t = pcb_x(ESP)
    y0, y1, z0, z1 = board_bbox(ESP)
    ez = (z0 + z1) / 2
    parts["esp_pcb"] = box(b, t, y0, y1, z0, z1)
    parts["esp_usb"] = box(t, t + 3.26, y0 - 0.5, y0 + 7.3, ez - 4.47, ez + 4.47)
    parts["esp_chip"] = box(t, t + 0.9, y0 + 10, y0 + 15, ez - 2.5, ez + 2.5)
    parts["esp_ant"] = box(t, t + 1.0, y1 - 3.0, y1 - 1.2, ez - 1.6, ez + 1.6)
    btn = None
    for zz in (z0 + 1.2, z1 - 4.2):
        bb = box(t, t + 1.5, y0 + 0.8, y0 + 3.8, zz, zz + 3.0)
        btn = bb if btn is None else btn.union(bb)
    parts["esp_btn"] = btn

    # LM393 rain driver board
    b, t = pcb_x(RAIN)
    y0, y1, z0, z1 = board_bbox(RAIN)
    rz = (z0 + z1) / 2
    parts["rain_pcb"] = box(b, t, y0, y1, z0, z1)
    # 90-degree headers: plastic on top at each edge, pins pointing out along Y
    hdr = box(t, t + 2.54, y0, y0 + 2.54, rz - 5.08, rz + 5.08).union(
        box(t, t + 2.54, y1 - 2.54, y1, rz - 2.54, rz + 2.54))
    parts["rain_hdr"] = hdr
    pins, plugs = None, None
    px = t + 1.27
    for n, edge, sgn in ((4, y0, -1), (2, y1, 1)):
        for i in range(n):
            zz = rz - 1.27 * (n - 1) + i * 2.54
            stub = box(b - 2.5, px + 0.32, edge - sgn * 1.27 - 0.32, edge - sgn * 1.27 + 0.32, zz - 0.32, zz + 0.32)
            ya, yb = sorted((edge - sgn * 1.27, edge + sgn * 6.0))
            arm = box(px - 0.32, px + 0.32, ya, yb, zz - 0.32, zz + 0.32)
            pg_a, pg_b = sorted((edge + sgn * 0.3, edge + sgn * (PLUG - 0.2)))
            plug = box(px - 1.25, px + 1.25, pg_a, pg_b, zz - 1.25, zz + 1.25)
            pins = stub.union(arm) if pins is None else pins.union(stub).union(arm)
            plugs = plug if plugs is None else plugs.union(plug)
    parts["rain_pins"] = pins
    parts["rain_plugs"] = plugs
    parts["rain_pot"] = box(t, t + 9.5, y0 + 18, y0 + 27.5, rz - 2.4, rz + 2.4)
    parts["rain_ic"] = box(t, t + 1.6, y0 + 9, y0 + 14, rz - 2, rz + 2)

    # AHT10 module
    b, t = pcb_x(AHT)
    y0, y1, z0, z1 = board_bbox(AHT)
    parts["aht_pcb"] = box(b, t, y0, y1, z0, z1)
    parts["aht_chip"] = box(t, t + 1.6, (y0 + y1) / 2 - 2, (y0 + y1) / 2 + 2, z1 - 8, z1 - 3)
    return parts


def make_rack_post():
    """Dummy 2 mm sheet-metal angle post for context renders only."""
    zc = PH / 2
    front = box(-24, 0, ET, ET + 2, -50, 95)
    side = box(-2, 0, ET, 60, -50, 95)
    post = front.union(side)
    # EIA-310 holes around this unit
    base = zc - U / 2
    for u in range(-1, 3):
        for off in (6.35, 22.225, 38.1):
            z = base + u * U + off
            if -45 < z < 90:
                post = post.cut(cq.Workplane("XZ").workplane(offset=-ET + 1)
                                .center(-10, z).rect(9.5, 9.5).extrude(-4))
    return post


if __name__ == "__main__":
    import os
    os.makedirs("out", exist_ok=True)
    mount = make_mount()
    cover = make_cover()
    cq.exporters.export(mount, "out/mount.step")
    cq.exporters.export(cover, "out/cover.step")
    for name, part in (("mount", mount), ("cover", cover)):
        bb = part.val().BoundingBox()
        print(name, "valid", part.val().isValid(),
              "bbox", round(bb.xlen, 2), round(bb.ylen, 2), round(bb.zlen, 2),
              "vol", round(part.val().Volume(), 1))
