from PIL import Image, ImageDraw
import os

def draw(size):
    S = size * 4
    im = Image.new("RGB", (S, S), "#0b1020")
    d = ImageDraw.Draw(im)
    # soft radial-ish glow
    for i in range(30):
        r = int(S * (0.62 - i * 0.012))
        c = 11 + i * 2, 16 + i * 3, 32 + i * 4
        d.ellipse((S/2 - r, S*0.30 - r, S/2 + r, S*0.30 + r), fill=c)
    # switch plate
    pad = S * 0.20
    d.rounded_rectangle((pad, pad, S - pad, S - pad), radius=S * 0.12, fill="#f3f6fb")
    # rocker
    p2 = S * 0.31
    d.rounded_rectangle((p2, p2 * 0.95, S - p2, S - p2 * 0.95), radius=S * 0.06, fill="#dfe6f1", outline="#b8c3d6", width=int(S*0.008))
    # lightning bolt
    pts = [(0.54,0.27),(0.40,0.52),(0.50,0.52),(0.46,0.73),(0.62,0.46),(0.52,0.46),(0.58,0.27)]
    d.polygon([(x*S, y*S) for x, y in pts], fill="#10b981")
    return im.resize((size, size), Image.LANCZOS)

img = draw(180)
img.save("assets/icon180_full.png", optimize=True)
q = img.quantize(colors=32, method=Image.MEDIANCUT, dither=Image.NONE)
q.save("assets/icon180.png", optimize=True)
draw(512).save("assets/icon512.png", optimize=True)
data = open("assets/icon180.png", "rb").read()
print("png bytes:", len(data))
with open("src/icon_data.h", "w") as f:
    f.write("#pragma once\n#include <Arduino.h>\nconst uint8_t ICON_PNG[] PROGMEM = {\n")
    for i in range(0, len(data), 16):
        f.write("  " + ", ".join(f"0x{b:02x}" for b in data[i:i+16]) + ",\n")
    f.write("};\nconst size_t ICON_PNG_LEN = sizeof(ICON_PNG);\n")
