"""Wiring diagram for the rack monitor -> wiring.svg / wiring.png"""
import cairosvg

W, H = 1600, 1040
FONT = "font-family='Helvetica, Arial, sans-serif'"
C = dict(v33="#d62828", gnd="#222222", sda="#1d6fd6", scl="#e0a100",
         ao="#2a9d4b", pwr="#e76f00", probe="#7a5c3a")
out = []


def a(s):
    out.append(s)


def rect(x, y, w, h, fill, stroke="#333", r=14, sw=3):
    a(f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='{r}' fill='{fill}' stroke='{stroke}' stroke-width='{sw}'/>")


def text(x, y, s, size=24, fill="#222", anchor="middle", weight="normal"):
    a(f"<text x='{x}' y='{y}' {FONT} font-size='{size}' fill='{fill}' text-anchor='{anchor}' font-weight='{weight}'>{s}</text>")


def pin(x, y, label, side, fill="#f2f2f2"):
    # small pad + label inside the board
    a(f"<circle cx='{x}' cy='{y}' r='9' fill='#d4af37' stroke='#7a6420' stroke-width='2'/>")
    dx = 22 if side == "left" else -22
    text(x + dx, y + 8, label, 22, fill, "start" if side == "left" else "end", "bold")


def wire(points, color, width=7):
    d = " ".join(f"{'M' if i == 0 else 'L'}{x},{y}" for i, (x, y) in enumerate(points))
    a(f"<path d='{d}' fill='none' stroke='{color}' stroke-width='{width}' stroke-linejoin='round' stroke-linecap='round'/>")


def dot(x, y, color):
    a(f"<circle cx='{x}' cy='{y}' r='11' fill='{color}'/>")


a(f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{H}' viewBox='0 0 {W} {H}'>")
a(f"<rect width='{W}' height='{H}' fill='white'/>")
text(W / 2, 62, "Rack Monitor wiring", 40, weight="bold")
text(W / 2, 100, "All 3.3 V. Wires soldered straight to the ESP pads. Match pins by the labels printed on your boards.", 22, "#555")

ROWS = [300, 370, 440, 510]

# ---- AHT10
ax, aw = 90, 250
rect(ax, 160, aw, 410, "#6a3fb5", "#3d2370")
text(ax + aw / 2 - 20, 205, "AHT10", 30, "white", weight="bold")
for y, lab in zip(ROWS, ("VIN", "GND", "SCL", "SDA")):
    pin(ax + aw, y, lab, "right", "white")
text(ax + aw / 2, 605, "temperature + humidity", 20, "#555")

# ---- ESP32-C3 Super Mini
ex, ew = 610, 380
rect(ex, 140, ew, 600, "#1b1b1b", "#000")
rect(ex + ew / 2 - 55, 118, 110, 48, "#bdbdbd", "#777", r=8)
text(ex + ew / 2, 150, "USB-C", 20, "#222", weight="bold")
text(ex + ew / 2, 215, "ESP32-C3", 32, "white", weight="bold")
text(ex + ew / 2, 250, "Super Mini", 24, "#cccccc")
left = dict(v33=(ROWS[0], "3.3 (3V3)"), gnd=(ROWS[1], "G (GND)"), scl=(ROWS[2], "7 (GPIO7)"), sda=(ROWS[3], "6 (GPIO6)"))
for k, (y, lab) in left.items():
    pin(ex, y, lab, "left", "white")
right = dict(pwr=(ROWS[0], "10 (GPIO10)"), ao=(ROWS[3], "0 (GPIO0)"))
for k, (y, lab) in right.items():
    pin(ex + ew, y, lab, "right", "white")
text(ex + ew / 2, 700, "USB-C 5 V powers everything", 20, "#bbbbbb")

# ---- LM393 rain board
rx, rw = 1240, 270
rect(rx, 160, rw, 410, "#1f5fbf", "#123a75")
text(rx + rw / 2 + 20, 205, "LM393", 30, "white", weight="bold")
text(rx + rw / 2 + 20, 236, "rain board", 22, "#dde8ff")
for y, lab in zip(ROWS, ("VCC", "GND", "DO", "AO")):
    pin(rx, y, lab, "left", "white")
text(rx + 150, ROWS[2] + 8, "not used", 18, "#bcd0f5", "start")
# 2-pin to probe
for x in (rx + rw / 2 - 25, rx + rw / 2 + 25):
    a(f"<circle cx='{x}' cy='570' r='9' fill='#d4af37' stroke='#7a6420' stroke-width='2'/>")

# ---- probe plate
px, py = 1200, 720
rect(px, py, 350, 190, "#c9a46a", "#7a5c3a", r=8)
for i in range(7):
    y = py + 25 + i * 23
    x0 = px + 30 if i % 2 == 0 else px + 70
    a(f"<line x1='{x0}' y1='{y}' x2='{x0 + 250}' y2='{y}' stroke='#e8e0c8' stroke-width='6'/>")
text(px + 175, py + 222, "sensing plate (on the rack floor = leak detector)", 19, "#555")
text(px + 175, py + 248, "2-wire cable, either way round, exits the back", 19, "#7a5c3a")
wire([(rx + rw / 2 - 25, 570), (rx + rw / 2 - 25, 640), (px + 120, 640), (px + 120, py)], C["probe"], 6)
wire([(rx + rw / 2 + 25, 570), (rx + rw / 2 + 25, 660), (px + 230, 660), (px + 230, py)], C["probe"], 6)

# shared ground first (underneath): ESP GND pad -> down under the ESP -> rain GND
gx, gy = ex - 70, 800
wire([(gx, ROWS[1]), (gx, gy), (1160, gy), (1160, ROWS[1]), (rx, ROWS[1])], C["gnd"])
text(gx + 20, gy + 34, "both GNDs share the ESP's single G pad", 19, "#444", "start")

def halo_wire(pts, color):
    wire(pts, "white", 17)
    wire(pts, color)

# ---- wires AHT <-> ESP
for k, y in (("v33", ROWS[0]), ("gnd", ROWS[1]), ("scl", ROWS[2]), ("sda", ROWS[3])):
    halo_wire([(ax + aw, y), (ex, y)], C[k])
dot(gx, ROWS[1], C["gnd"])

# ---- wires ESP <-> rain
halo_wire([(ex + ew, ROWS[0]), (rx, ROWS[0])], C["pwr"])
halo_wire([(ex + ew, ROWS[3]), (rx, ROWS[3])], C["ao"])

# ---- legend
lx, ly = 90, 900
items = [("3.3 V", "v33"), ("GND", "gnd"), ("SDA", "sda"), ("SCL", "scl"), ("rain power (GPIO10)", "pwr"), ("analog signal", "ao")]
x = lx
for lab, k in items:
    a(f"<line x1='{x}' y1='{ly}' x2='{x + 40}' y2='{ly}' stroke='{C[k]}' stroke-width='8' stroke-linecap='round'/>")
    text(x + 52, ly + 8, lab, 20, "#333", "start")
    x += 90 + len(lab) * 11
text(lx, ly + 60, "The rain board is powered from GPIO10 so it is only switched on for each reading — this stops the plate corroding.", 19, "#555", "start")
text(lx, ly + 88, "Don't power the rain board from 5 V: its output would be more than the ESP can read.", 19, "#555", "start")
a("</svg>")

svg = "\n".join(out)
open("out/wiring.svg", "w").write(svg)
cairosvg.svg2png(bytestring=svg.encode(), write_to="out/wiring.png", output_width=W * 2)
print("ok")
