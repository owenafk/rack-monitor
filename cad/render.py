import os, cadquery as cq, pyvista as pv, numpy as np
from case import *
pv.OFF_SCREEN = True
os.makedirs("out/tmp", exist_ok=True)

def to_pv(wp, name):
    p = f"out/tmp/{name}.stl"
    cq.exporters.export(wp, p, tolerance=0.02, angularTolerance=0.1)
    return pv.read(p)

mount_wp, cover_wp = make_mount(), make_cover()
mount, cover = to_pv(mount_wp, "mount"), to_pv(cover_wp, "cover")
post = to_pv(make_rack_post(), "post")
bw = make_boards()
boards = {k: to_pv(v, k) for k, v in bw.items()}
BCOL = dict(esp_pcb="#1b1b1b", esp_usb="#c8c8c8", esp_chip="#333333", esp_ant="#e0d4b0",
            esp_btn="#f0f0f0", rain_pcb="#1f5fbf", rain_hdr="#111111", rain_pins="#d4af37",
            rain_pot="#2a6fe0", rain_plugs="#151515", rain_ic="#222222", aht_pcb="#6a3fb5", aht_chip="#dddddd")
MCOL, CCOL = "#3a3f47", "#e8e4dc"

def plotter(size=(1600, 1200)):
    p = pv.Plotter(off_screen=True, window_size=size)
    p.set_background("white")
    p.enable_anti_aliasing("ssaa")
    p.enable_shadows() if False else None
    return p

def add(p, mesh, color, opacity=1.0, shift=(0,0,0)):
    m = mesh.copy(); m.translate(shift, inplace=True)
    p.add_mesh(m, color=color, smooth_shading=False, specular=0.25, opacity=opacity,
               show_edges=False)

def add_boards(p, shift=(0,0,0)):
    for k, m in boards.items():
        add(p, m, BCOL[k], shift=shift)

def cam(p, pos, focal, up=(0,0,1), zoom=1.0):
    p.camera_position = [pos, focal, up]
    p.camera.zoom(zoom)

C = (10, 27, 20)
# 1 hero: mounted on a rack post
p = plotter()
add(p, post, "#9aa0a6"); add(p, mount, MCOL); add(p, cover, CCOL); add_boards(p)
cam(p, (150, -150, 110), (0, 32, 20), zoom=1.15)
p.add_text("Mounted on a 10\" rack post (post shown for scale)", position="lower_left", font_size=11, color="#444444")
p.screenshot("out/render_1_mounted.png"); p.close()

# 2 exploded
p = plotter()
add(p, mount, MCOL); add_boards(p, (12,0,0)); add(p, cover, CCOL, shift=(45,0,0))
cam(p, (170, -120, 120), (30, 33, 20), zoom=1.05)
p.add_text("Exploded: mount plate  /  boards  /  snap cover", font_size=11, color="#444444")
p.screenshot("out/render_2_exploded.png"); p.close()

# 3 open, face-on with labels
p = plotter()
add(p, mount, MCOL); add_boards(p)
cam(p, (170, 33, 20), (0, 33, 20), up=(0,0,1), zoom=1.45)
lab = np.array([[12, 13, 30], [12, 35, 9], [12, 57.5, 31], [12, 3, 28.5], [12, 58, 9]])
p.add_point_labels(lab, ["ESP32-C3 Super Mini", "LM393 rain driver", "AHT10 (own bay)", "USB-C", "probe plug -> out the back"],
                   font_size=22, point_size=1, shape_opacity=0.75, text_color="black",
                   always_visible=True)
p.add_text("Cover removed - front of rack is at left", font_size=11, color="#444444")
p.screenshot("out/render_3_layout.png"); p.close()

# 4 cover interior
p = plotter()
add(p, cover, CCOL)
cam(p, (-130, -60, 90), (11, 34, 20), zoom=1.2)
p.add_text("Cover interior: clamps, USB presser, AHT10 partition, snap tongues", font_size=11, color="#444444")
p.screenshot("out/render_4_cover_inside.png"); p.close()

# 5 rear / back of mount (snap recesses, ear slots)
p = plotter()
add(p, mount, MCOL); add(p, cover, CCOL)
cam(p, (-140, 150, 60), (0, 33, 20), zoom=1.1)
p.add_text("Back: sits flat on the post side; ear slots take M6 / M5 / 10-32", font_size=11, color="#444444")
p.screenshot("out/render_5_back.png"); p.close()

# 6 section through a snap tongue (XZ plane at y=11)
p = plotter()
for m, col in ((mount, MCOL), (cover, CCOL)):
    s = m.clip(normal=(0, 1, 0), origin=(0, 11.0, 0), invert=False)
    add(p, s, col)
add_boards(p)
cam(p, (10, -160, 20), (10, 11, 20), zoom=1.9)
p.add_text("Section at a snap tongue: barbs hook into recesses in the plate back", font_size=11, color="#444444")
p.screenshot("out/render_6_snap_section.png"); p.close()

# 7 print orientation + STL export
def rot_mount(wp):  # stand on the ear face
    return wp.rotate((0,0,0), (1,0,0), 90).translate((0,0,0))
def rot_cover(wp):  # top face down
    return wp.rotate((0,0,0), (0,1,0), 90)
pm, pc = rot_mount(mount_wp), rot_cover(cover_wp)
def drop(wp, dx):
    bb = wp.val().BoundingBox()
    return wp.translate((dx - bb.xmin, -bb.center.y, -bb.zmin))
pm, pc = drop(pm, 0), drop(pc, 45)
import trimesh
for wp, fn in ((pm, "out/rack_env_mount.stl"), (pc, "out/rack_env_cover.stl")):
    cq.exporters.export(wp, fn, tolerance=0.01, angularTolerance=0.1)
    tm = trimesh.load(fn); tm.merge_vertices()
    tm.update_faces(tm.nondegenerate_faces()); tm.update_faces(tm.unique_faces())
    tm.remove_unreferenced_vertices(); trimesh.repair.fix_normals(tm)
    assert tm.is_watertight, fn
    tm.export(fn)
p = plotter()
bed = pv.Plane(center=(35, 0, -0.3), direction=(0,0,1), i_size=140, j_size=110)
p.add_mesh(bed, color="#d9d9d9")
add(p, pv.read("out/rack_env_mount.stl"), MCOL); add(p, pv.read("out/rack_env_cover.stl"), CCOL)
cam(p, (150, -170, 150), (40, 0, 15), zoom=1.2)
p.add_text("Print orientation - no supports needed", font_size=11, color="#444444")
p.screenshot("out/render_7_print_layout.png"); p.close()
print("done")
