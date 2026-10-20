# Генератор креслення з розмірами (всі числа взяті з cad/generate_stl.py)
class View:
    def __init__(self, x_min, x_max, y_min, y_max, s, pad=70):
        self.x_min, self.y_max, self.s, self.pad = x_min, y_max, s, pad
        self.w = (x_max - x_min) * s + pad * 2
        self.h = (y_max - y_min) * s + pad * 2
        self.out = []
    def X(self, x): return self.pad + (x - self.x_min) * self.s
    def Y(self, y): return self.pad + (self.y_max - y) * self.s
    def rect(self, x0, y0, x1, y1, cls="part", extra=""):
        self.out.append(f'<rect x="{self.X(x0):.1f}" y="{self.Y(y1):.1f}" width="{(x1-x0)*self.s:.1f}" height="{(y1-y0)*self.s:.1f}" class="{cls}" {extra}/>')
    def line(self, x0, y0, x1, y1, cls="axis"):
        self.out.append(f'<line x1="{self.X(x0):.1f}" y1="{self.Y(y0):.1f}" x2="{self.X(x1):.1f}" y2="{self.Y(y1):.1f}" class="{cls}"/>')
    def circle(self, x, y, r, cls="shaft"):
        self.out.append(f'<circle cx="{self.X(x):.1f}" cy="{self.Y(y):.1f}" r="{r*self.s:.1f}" class="{cls}"/>')
    def text(self, x, y, t, cls="lbl", anchor="middle"):
        self.out.append(f'<text x="{self.X(x):.1f}" y="{self.Y(y):.1f}" class="{cls}" text-anchor="{anchor}">{t}</text>')
    def ptext(self, px, py, t, cls="lbl", anchor="middle"):
        self.out.append(f'<text x="{px:.1f}" y="{py:.1f}" class="{cls}" text-anchor="{anchor}">{t}</text>')
    def dimh(self, x0, x1, y, off, label):
        """горизонтальний розмір між x0..x1 на рівні y, лінія зсунута на off px (вниз +)"""
        a, b, py = self.X(x0), self.X(x1), self.Y(y) + off
        base = self.Y(y)
        self.out.append(f'<line x1="{a:.1f}" y1="{base:.1f}" x2="{a:.1f}" y2="{py+ (6 if off>0 else -6):.1f}" class="ext"/>')
        self.out.append(f'<line x1="{b:.1f}" y1="{base:.1f}" x2="{b:.1f}" y2="{py+ (6 if off>0 else -6):.1f}" class="ext"/>')
        self.out.append(f'<line x1="{a:.1f}" y1="{py:.1f}" x2="{b:.1f}" y2="{py:.1f}" class="dim" marker-start="url(#ar)" marker-end="url(#ar)"/>')
        ty = py - 4 if off > 0 else py - 4
        self.ptext((a + b) / 2, ty, label, "dl")
    def dimv(self, x, y0, y1, off, label):
        """вертикальний розмір між y0..y1 на x, лінія зсунута на off px (вліво -, вправо +)"""
        a, b, px = self.Y(y0), self.Y(y1), self.X(x) + off
        base = self.X(x)
        sgn = 6 if off > 0 else -6
        self.out.append(f'<line x1="{base:.1f}" y1="{a:.1f}" x2="{px+sgn:.1f}" y2="{a:.1f}" class="ext"/>')
        self.out.append(f'<line x1="{base:.1f}" y1="{b:.1f}" x2="{px+sgn:.1f}" y2="{b:.1f}" class="ext"/>')
        self.out.append(f'<line x1="{px:.1f}" y1="{a:.1f}" x2="{px:.1f}" y2="{b:.1f}" class="dim" marker-start="url(#ar)" marker-end="url(#ar)"/>')
        cx, cy = px - 5, (a + b) / 2
        self.out.append(f'<text x="{cx:.1f}" y="{cy:.1f}" class="dl" text-anchor="middle" transform="rotate(-90 {cx:.1f} {cy:.1f})">{label}</text>')
    def svg(self):
        defs = '<defs><marker id="ar" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 1 L10 5 L0 9 z" fill="#fbbf24"/></marker></defs>'
        return f'<svg viewBox="0 0 {self.w:.0f} {self.h:.0f}" xmlns="http://www.w3.org/2000/svg">{defs}' + "".join(self.out) + '</svg>'

T, W = 2.8, 3.2

# ---------- ВИД 1: спереду (з кімнати на стіну), X вправо, Y вгору ----------
v1 = View(-90, 56, -126, 58, 3.6, pad=78)
# базова пластина (під скотч)
for r in [(41.5, -53.2, 51.5, 53.2), (-85.7, 41.2, 41.5, 53.2), (-85.7, -41.2, -41.5, 41.2), (-85.7, -106, 41.5, -41.2)]:
    v1.rect(*r, cls="plate")
# трикутні косинки/виступ під боксом
v1.rect(-75.2, -122, 28.2, -107.2, cls="plate")
# вимикач: вікно 83.0 x 82.4 і клавіша 57 x 50
v1.rect(-41.5, -41.2, 41.5, 41.2, cls="hole")
v1.rect(-28.5, -25, 28.5, 25, cls="rocker")
v1.text(0, 0, "КЛАВІША", "lbld2"); v1.text(0, -7, "57 × 50", "lbld3")
# бокс ESP32
v1.rect(-75.2, -107.2, 28.2, -41.2, cls="wall")
v1.rect(-72, -104, 25, -44.4, cls="inner")
v1.text(-23, -75, "БОКС ESP32", "lbl2"); v1.text(-23, -83, "внутр. 97 × 59.6", "lbl3")
# ложе серви
v1.rect(-85.7, -21, -43, 42, cls="wall")
v1.rect(-82.5, -17.8, -43, 38.8, cls="inner")
v1.rect(-82.5, -10.9, -43.5, 31.9, cls="servo")
v1.line(-90, 0, -43, 0, "axis")
v1.text(-65, 9, "СЕРВА", "lbl2"); v1.text(-65, 2.5, "вал на Y = 0", "lbl3")
# розміри
v1.dimh(-85.7, 51.5, 53.2, -40, "ширина основи 137.2")
v1.dimh(-41.5, 41.5, -41.2, 0, "") if False else None
v1.dimh(-41.5, 41.5, 41.2, -16, "83.0")
v1.dimh(41.5, 51.5, -53.2, 22, "10")
v1.dimv(51.5, -41.2, 41.2, 48, "82.4")
v1.dimv(51.5, 41.2, 53.2, 20, "12") if False else None
v1.dimv(-85.7, -122, 53.2, -58, "висота основи 175.2 (від -122 до +53.2)")
v1.dimh(-75.2, 28.2, -122, 24, "бокс зовн. 103.4")
v1.dimv(28.2, -107.2, -41.2, 30, "66 (зовн.)")
v1.dimv(28.2, -122, -107.2, 30, "14.8") if False else None
v1.dimh(-85.7, -43, 42, -12, "42.7")
v1.dimv(-43, -21, 42, 27, "63 (ложе, зовн.)")
v1.text(54, -2, "X →", "ax")
v1.ptext(v1.X(-85.7) - 4, v1.Y(53.2) - 62, "Y ↑", "ax", "end")

# ---------- ВИД 2: збоку (розріз по Y=0 через вал), X вправо, Z вгору ----------
v2 = View(-90, 56, -2, 44, 5.0, pad=120)
v2.rect(-90, -1.2, 56, 0, cls="wallline")
v2.text(-70, -5.5, "СТІНА", "lbl3")
v2.rect(-85.7, 0, -41.5, T, cls="plate")                 # пластина (ліва ділянка)
v2.rect(41.5, 0, 51.5, T, cls="plate")                   # права планка
v2.rect(-85.7, T, -43, 14, cls="wall")                   # подіум
v2.rect(-85.7, 14, -82.5, 35.2, cls="wall")              # задня стінка ложа
v2.rect(-85.7, 35.2, -58.5, 37.4, cls="wall")            # верхні защіпки
v2.rect(-82.5, 14, -43.5, 35.2, cls="servo")             # серва
v2.rect(-43.5, 23.5, -35, 25.5, cls="shaft2")            # вал вправо до вимикача
v2.rect(-41.05, 0, 41.05, 12.5, cls="swframe")           # рамка вимикача
v2.rect(-28.5, 12.5, 28.5, 18, cls="rocker")             # клавіша
v2.text(0, 6, "рамка вимикача 82.1", "lbld3"); v2.text(0, 14.4, "клавіша 57", "lbld3")
v2.text(-62, 25, "СЕРВА 39.5 × 21.2", "lbl2")
v2.line(-90, 24.5, -20, 24.5, "axis"); v2.text(-88, 26, "вісь вала", "lbl3", "start")
v2.dimv(-85.7, 0, T, -34, "2.8")
v2.dimv(-85.7, 0, 14, -58, "подіум 14.0")
v2.dimv(-85.7, 0, 35.2, -82, "верх серви 35.2")
v2.dimv(-85.7, 0, 37.4, -104, "верх защіпок 37.4")
v2.dimv(45, 0, 12.5, 46, "рамка 12.5") if False else None
v2.dimv(41.05, 0, 18, 44, "найдальша точка клавіші 18.0")
v2.dimv(-43.5, 0, 24.5, 40, "вал 24.5") if False else None
v2.dimh(-85.7, -82.5, 14, -0, "") if False else None
v2.dimh(-85.7, -43, 0, 44, "ложе 42.7")
v2.dimh(-41.05, 41.05, 0, 44, "вікно 83.0")
v2.dimh(-82.5, -43.5, 35.2, -34, "серва 39 (+0.5 запас)")
v2.dimv(-30, 18, 24.5, 0, "6.5") if False else None
v2.ptext(v2.X(-26), v2.Y(30), "запас 6.5 мм від клавіші (24.5 − 18)", "lbl3")

# ---------- ВИД 3: детальне ложе серви (спереду), крупно ----------
v3 = View(-88, -40, -24, 45, 6.2, pad=110)
v3.rect(-85.7, -21, -43, 42, cls="wall")
v3.rect(-82.5, -17.8, -43, 38.8, cls="inner")
v3.rect(-82.5, -10.9, -43.5, 31.9, cls="servo")
v3.rect(-58.5, -17.8, -45.5, -10.9, cls="ear"); v3.rect(-58.5, 31.9, -45.5, 38.8, cls="ear")
v3.rect(-67.5, -21, -58.5, -10.9, cls="wall")
v3.rect(-82.5, -21, -67.5, -17.8, cls="gap")
v3.line(-88, 0, -40, 0, "axis")
v3.circle(-47, 0, 2.2, "shaft")
v3.text(-64, 10, "корпус серви", "lbl2"); v3.text(-64, 6, "42.8 × 39.5", "lbl3")
v3.text(-52, 35.5, "вушко", "lbl3"); v3.text(-52, -14.5, "вушко", "lbl3")
v3.text(-75, -19.5, "канал дроту", "lbl3")
v3.dimv(-82.5, -10.9, 31.9, -34, "42.8 (корпус)")
v3.dimv(-85.7, -17.8, 38.8, -58, "56.6 (під вушка 55)")
v3.dimv(-85.7, -21, 42, -88, "63.0 (зовні)")
v3.dimh(-82.5, -43, -21, 62, "39.5 (довжина ложа)")
v3.dimh(-85.7, -43, 42, -26, "42.7 (зовні)")
v3.dimh(-82.5, -67.5, -21, 30, "канал дроту 15")
v3.dimv(-43, -10.9, 0, 30, "10.9") 
v3.dimv(-43, 0, 31.9, 30, "31.9 до кінця")
v3.dimh(-85.7, -82.5, 20, 0, "") if False else None
v3.ptext(v3.X(-85.7), v3.Y(-24) + 92, "стінка 3.2 • упори вушок: X = −45.5…−43 • вал на Y = 0 (10.9 від низу корпусу)", "lbl3", "start")

# ---------- ВИД 4: розріз боксу ESP32 (X–Z) ----------
v4 = View(-80, 33, -2, 34, 5.5, pad=70)
v4.rect(-80, -1.2, 33, 0, cls="wallline")
v4.rect(-75.2, 0, 28.2, T, cls="plate")
v4.rect(-75.2, T, -72, 28, cls="wall")
v4.rect(25, T, 28.2, 28, cls="wall")
v4.rect(-38, T, -35.5, T + 14, cls="inner2"); v4.rect(-6.5, T, -4, T + 14, cls="inner2")
v4.rect(-35.5, T + 0.5, -6.5, T + 1.6, cls="esp")
v4.text(-21, 17, "ESP32 (28.5 між стійками)", "lbl3")
v4.dimh(-75.2, 28.2, 0, 34, "103.4 (зовні)")
v4.dimh(-72, 25, 28, -14, "97 (всередині)")
v4.dimh(-38, -6.5, T + 14, -22, "стійки 31.5")
v4.dimv(28.2, 0, 28, 40, "висота 28")
v4.dimv(-75.2, 0, T, -26, "2.8")
v4.dimv(-35.5, T, T + 14, 0, "14") if False else None
v4.text(-50, 8, "(кришка 97 × 60 на защіпках)", "lbl3")

CSS = """
:root{--bg:#0b0e14;--card:#121722;--b:#232c3d;--t:#e8edf5;--m:#8b98ad}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--t);font-family:-apple-system,"Segoe UI",Roboto,sans-serif;padding:18px;max-width:1200px;margin:auto}
h1{font-size:20px;margin-bottom:4px} p.s{color:var(--m);font-size:13px;margin-bottom:16px;line-height:1.5}
.card{background:var(--card);border:1px solid var(--b);border-radius:14px;padding:14px;margin-bottom:18px}
.card h2{font-size:15px;margin-bottom:4px} .card p{font-size:12.5px;color:var(--m);margin-bottom:10px;line-height:1.5}
svg{width:100%;height:auto;background:#080b11;border-radius:10px;border:1px solid #1b2332}
.plate{fill:#1d4e89;stroke:#60a5fa;stroke-width:1.2;opacity:.55}
.wall{fill:#2563eb;stroke:#93c5fd;stroke-width:1.3;opacity:.85}
.inner{fill:#0a0f1a;stroke:#3b82f6;stroke-width:1;stroke-dasharray:4 3}
.inner2{fill:#3b82f6;stroke:#93c5fd;stroke-width:1}
.hole{fill:#0a0f1a;stroke:#e5e7eb;stroke-width:1.5}
.rocker{fill:#e5e7eb;stroke:#9ca3af;stroke-width:1.2}
.swframe{fill:#cbd5e1;stroke:#94a3b8;stroke-width:1.2}
.servo{fill:#475569;stroke:#cbd5e1;stroke-width:1.4}
.ear{fill:#64748b;stroke:#cbd5e1;stroke-width:1}
.shaft{fill:#ef4444;stroke:#fecaca;stroke-width:1.2}
.shaft2{fill:#ef4444;stroke:#fecaca;stroke-width:1}
.esp{fill:#16a34a;stroke:#86efac;stroke-width:1}
.gap{fill:#052e16;stroke:#22c55e;stroke-width:1;stroke-dasharray:3 3}
.wallline{fill:#374151}
.axis{stroke:#ef4444;stroke-width:1;stroke-dasharray:6 4}
.ext{stroke:#fbbf24;stroke-width:.8;opacity:.7}
.dim{stroke:#fbbf24;stroke-width:1.3}
.dl{fill:#fbbf24;font-size:11.5px;font-weight:700}
.lbl2{fill:#fff;font-size:13px;font-weight:800}
.lbl3{fill:#cbd5e1;font-size:10.5px}
.lbl{fill:#fff;font-size:12px}
.lbld2{fill:#0f172a;font-size:13px;font-weight:800}
.lbld3{fill:#1e293b;font-size:10.5px;font-weight:600}
.ax{fill:#94a3b8;font-size:12px;font-weight:700}
table{width:100%;border-collapse:collapse;font-size:13px}
td,th{padding:7px 8px;border-bottom:1px solid var(--b);text-align:left}
th{color:var(--m);font-weight:600;font-size:11.5px;text-transform:uppercase}
td.n{color:#fbbf24;font-weight:700;white-space:nowrap}
.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:var(--m);margin-bottom:10px}
.legend i{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:5px;vertical-align:-2px}
code{background:#1b2332;padding:1px 6px;border-radius:5px;color:#e8edf5}
"""

rows = [
 ("Пластина (під скотч)", "товщина", "2.8", "суцільна плита, на неї все ставиться"),
 ("Вікно під вимикач", "83.0 × 82.4", "—", "вимикач 82.1 × 81.58 + 0.9/0.8 запас; центр (0, 0)"),
 ("Права планка", "10 × 106.4", "2.8", "там 15–20 мм до дверей, тому тонка"),
 ("Верхня планка", "127.2 × 12", "2.8", "X від −85.7 до +41.5"),
 ("Подіум під серву", "42.7 × 63", "14.0", "піднімає вал на 24.5 мм над стіною (клавіша 18 мм)"),
 ("Ложе серви (внутр.)", "39.5 × 42.8", "21.2", "серва 39 × 42 × 21 + запас; вал на Y = 0"),
 ("Ніша під вушка", "56.6 (Y)", "21.2", "вушка серви 55 мм; упори X = −45.5…−43"),
 ("Стінки ложа", "3.2", "до 35.2", "+ защіпки 2.2 зверху (до 37.4)"),
 ("Канал для дроту", "15", "—", "X −82.5…−67.5, знизу ложа"),
 ("Crush ribs (ребра натягу)", "0.7 × 2.2", "—", "по боках серви, стискають без люфту"),
 ("Бокс ESP32 (внутр.)", "97 × 59.6", "28", "стінка 3.2; стійки під плату 31.5 між ними"),
 ("Кришка боксу", "97 × 60", "2.4", "4 защіпки 5.8 заввишки"),
]
tbl = "".join(f"<tr><td>{a}</td><td class='n'>{b}</td><td class='n'>{c}</td><td>{d}</td></tr>" for a, b, c, d in rows)

html = f"""<!DOCTYPE html><html lang="uk"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Smart Switch — креслення з розмірами</title><style>{CSS}</style></head><body>
<h1>Основний корпус Smart Switch — креслення з розмірами (мм)</h1>
<p class="s">Усі числа взяті прямо з <code>cad/generate_stl.py</code> (v4), тож відтворюються в CAD 1-в-1. Початок координат (0, 0) = центр вікна під вимикач на стіні. <b>X</b> вправо, <b>Y</b> вгору, <b>Z</b> — від стіни в кімнату. Жовте — розміри.</p>
<div class="legend"><span><i style="background:#1d4e89"></i>пластина 2.8</span><span><i style="background:#2563eb"></i>стінки/подіум</span><span><i style="background:#475569"></i>серва</span><span><i style="background:#e5e7eb"></i>вимикач</span><span><i style="background:#ef4444"></i>вал / вісь</span></div>

<div class="card"><h2>1. Вигляд спереду (як ти дивишся на стіну)</h2>
<p>Праворуч від вимикача тонка планка 10 мм (двері), ліворуч — ложе серви, знизу — бокс ESP32. Червона штрихова лінія — вісь вала (Y = 0) точно навпроти середини клавіші.</p>{v1.svg()}</div>

<div class="card"><h2>2. Розріз збоку через вал (Y = 0)</h2>
<p>Ключове: клавіша виступає на 18.0 мм, тому серву піднято подіумом 14.0 — вал на 24.5 мм, тобто на 6.5 мм вище найвищої точки клавіші.</p>{v2.svg()}</div>

<div class="card"><h2>3. Ложе серви — крупно</h2>
<p>Корпус серви 42.8 × 39.5, ніша під вушка 56.6, упори вушок, нижній канал для дроту 15 мм.</p>{v3.svg()}</div>

<div class="card"><h2>4. Розріз боксу ESP32</h2>
<p>Стійки тримають плату ESP32 (28.5 мм) без тіліпання; конденсатор і дроти лежать поруч.</p>{v4.svg()}</div>

<div class="card"><h2>Зведена таблиця для CAD</h2>
<table><tr><th>Елемент</th><th>Розмір, мм</th><th>Висота Z</th><th>Примітка</th></tr>{tbl}</table>
<p style="margin-top:12px">Порада для Fusion/Onshape: ескіз на площині стіни → видавити пластину 2.8 → вирізати вікно 83.0 × 82.4 → подіум 14 → ложе (стінки 3.2, до 35.2) → бокс. Для нового вимикача міняй лише розміри вікна й висоту подіуму: <code>Z_вал = подіум + 10.5</code>, і він має бути вищий за виступ клавіші.</p></div>
</body></html>"""
open("/home/maks/.gemini/antigravity/brain/96b950ce-cce2-4952-a148-51af2e00e77c/switch_dimensions.html", "w").write(html)
print("ok", len(html))
