#!/usr/bin/env python3
"""Export the figures in the format the submission system accepts.

Frontiers asks for TIFF or JPG at 300 dpi, 8.5 to 20 cm wide. The working files
are PNG at 300 dpi, and one of them (fig2) is 20.3 cm wide, just over the limit,
so a naive conversion would be rejected. Each figure is flattened onto white (no
alpha channel), scaled down only if it exceeds 20 cm, and written with the dpi
recorded in the file so the receiving system can check it.

Both formats are produced: JPG for the upload, TIFF as a fallback if the system
re-encodes JPG too aggressively.
"""
import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "out", "figures")
DST = os.path.join(SRC, "upload")
DPI = 300
MAX_PX = int(20.0 / 2.54 * DPI)     # 20 cm at 300 dpi
MIN_PX = int(8.5 / 2.54 * DPI)      # 8.5 cm at 300 dpi

FIGS = ["fig1_evidence_map", "fig2_toolchain", "fig3_reporting",
        "fig4_loop", "fig5_fulltext_lift", "figS1_prisma"]


def main():
    os.makedirs(DST, exist_ok=True)
    for name in FIGS:
        p = os.path.join(SRC, name + ".png")
        if not os.path.exists(p):
            print("missing:", p)
            continue
        im = Image.open(p)
        if im.mode in ("RGBA", "LA", "P"):
            bg = Image.new("RGB", im.size, (255, 255, 255))
            rgba = im.convert("RGBA")
            bg.paste(rgba, mask=rgba.split()[-1])
            im = bg
        else:
            im = im.convert("RGB")
        w, h = im.size
        scaled = False
        if w > MAX_PX:
            nh = round(h * MAX_PX / w)
            im = im.resize((MAX_PX, nh), Image.LANCZOS)
            scaled = True
        w2, h2 = im.size
        cm = w2 / DPI * 2.54
        status = "OK" if MIN_PX <= w2 <= MAX_PX else "OUT OF RANGE"
        jpg = os.path.join(DST, name + ".jpg")
        tif = os.path.join(DST, name + ".tif")
        im.save(jpg, "JPEG", quality=95, dpi=(DPI, DPI), optimize=True)
        im.save(tif, "TIFF", compression="tiff_lzw", dpi=(DPI, DPI))
        print("%-22s %4dx%-4d %5.2f cm  %s%s  jpg %.2f MB" % (
            name, w2, h2, cm, status, " (rescaled)" if scaled else "",
            os.path.getsize(jpg) / 1e6))


if __name__ == "__main__":
    main()
