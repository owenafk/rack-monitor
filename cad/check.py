from case import *
mount, cover = make_mount(), make_cover()
boards = make_boards()
def iv(a, b):
    try:
        r = a.intersect(b).val()
        return round(r.Volume(), 3)
    except Exception as e:
        return f"err {e}"
print("mount∩cover", iv(mount, cover))
for k, v in boards.items():
    print(f"{k:10s} ∩mount {iv(v, mount):>8}  ∩cover {iv(v, cover):>8}")
