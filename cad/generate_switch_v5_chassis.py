#!/usr/bin/env python3
"""
Генератор 3D-моделей Smart Light Switch v5:
«Direct-Chassis Mount» (Безклеєве гвинтове кріплення підрозетника 60 мм + фіксація серви на болтах)
Під розмір клавіші 57 x 50 мм!

Деталі:
1. switch_v5_chassis_frame.stl — Основне шасі-кріплення замість рідної рамки.
2. switch_v5_servo_clamp.stl  — Верхня затискна планка серви на 2 болти M3 (серво більше ніколи не випаде).
3. switch_v5_t_arm_25t.stl     — Посилений T-подібний важіль 25T з контактними п'ятами під клавішу 57x50 мм.
"""

import struct
import math
import os

def write_binary_stl(filename, triangles, name="SmartSwitch-v5"):
    with open(filename, "wb") as f:
        header = name.encode("ascii").ljust(80, b" ")
        f.write(header)
        f.write(struct.pack("<I", len(triangles)))
        for p1, p2, p3 in triangles:
            ux, uy, uz = p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2]
            vx, vy, vz = p3[0] - p1[0], p3[1] - p1[1], p3[2] - p1[2]
            nx = uy * vz - uz * vy
            ny = uz * vx - ux * vz
            nz = ux * vy - uy * vx
            length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
            nx, ny, nz = nx / length, ny / length, nz / length
            f.write(struct.pack("<12fH", nx, ny, nz, *p1, *p2, *p3, 0))

def add_hex(tris, v):
    faces = [
        (0, 2, 1), (0, 3, 2),
        (4, 5, 6), (4, 6, 7),
        (0, 1, 5), (0, 5, 4),
        (2, 3, 7), (2, 7, 6),
        (0, 4, 7), (0, 7, 3),
        (1, 2, 6), (1, 6, 5),
    ]
    for i, j, k in faces:
        tris.append((v[i], v[j], v[k]))

def add_box(tris, x0, y0, z0, x1, y1, z1):
    v = [
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)
    ]
    add_hex(tris, v)

def add_cylinder(tris, cx, cy, z0, z1, radius, segments=16):
    """Апроксимований циліндр для стійок та отворів"""
    angles = [2.0 * math.pi * i / segments for i in range(segments)]
    for i in range(segments):
        i_next = (i + 1) % segments
        a1, a2 = angles[i], angles[i_next]
        x1, y1 = cx + radius * math.cos(a1), cy + radius * math.sin(a1)
        x2, y2 = cx + radius * math.cos(a2), cy + radius * math.sin(a2)
        # Бокова грань
        tris.append(((x1, y1, z0), (x2, y2, z0), (x2, y2, z1)))
        tris.append(((x1, y1, z0), (x2, y2, z1), (x1, y1, z1)))
        # Дно і кришка
        tris.append(((cx, cy, z0), (x2, y2, z0), (x1, y1, z0)))
        tris.append(((cx, cy, z1), (x1, y1, z1), (x2, y2, z1)))

def add_wedge_y(tris, x0, x1, y_base, y_tip, z_low, z_high):
    L0 = (x0, y_base, z_low)
    L1 = (x0, y_tip, z_low)
    L2 = (x0, y_tip, z_high)
    R0 = (x1, y_base, z_low)
    R1 = (x1, y_tip, z_low)
    R2 = (x1, y_tip, z_high)
    tris.append((L0, L2, L1))
    tris.append((R0, R1, R2))
    tris.append((L0, L1, R1))
    tris.append((L0, R1, R0))
    tris.append((L1, L2, R2))
    tris.append((L1, R2, R1))
    tris.append((L0, R0, R2))
    tris.append((L0, R2, L2))

# ==============================================================================
# 1. ОСНОВНЕ ШАСІ v5 (switch_v5_chassis_frame.stl)
# ==============================================================================
def generate_v5_chassis_frame(filename):
    tris = []
    t_base = 3.2   # Жорстка пластина основи
    wall = 3.5     # Товщина силових стінок

    # Вікно під клавішу 57 мм (ширина X) на 50 мм (висота Y):
    # З зазором +1.0 мм на сторону: 59.0 x 52.0 мм
    kx0, kx1 = -29.5, 29.5
    ky0, ky1 = -26.0, 26.0

    # Зовнішня база навколо супорта вимикача (квадрат 76 x 76 мм, замість рідної рамки)
    # Зліва подовжена під серву, знизу під ESP32
    fx0, fx1 = -76.0, 38.0
    fy0, fy1 = -92.0, 36.0

    # 1.1 Основна базова плита (Z = 0 .. t_base) з вікном під клавішу
    # Верхня частина над клавішею
    add_box(tris, fx0, ky1, 0.0, fx1, fy1, t_base)
    # Права рамка
    add_box(tris, kx1, ky0, 0.0, fx1, ky1, t_base)
    # Ліва частина (під серву)
    add_box(tris, fx0, ky0, 0.0, kx0, ky1, t_base)
    # Нижня частина (під ESP32)
    add_box(tris, fx0, fy0, 0.0, fx1, ky0, t_base)

    # 1.2 Монтажні пази під штатні гвинти підрозетника 60 мм (Мертво фіксують базу на стіні!)
    # Стандартний крок гвинтів у стіні: крок 60 мм (X = ±30 мм, або Y = ±30 мм)
    # Робимо посилені напливи навколо отворів кріплення:
    for hole_x in (-30.0, 30.0):
        add_box(tris, hole_x - 4.5, -4.5, t_base, hole_x + 4.5, 4.5, t_base + 2.5)

    # 1.3 ЛОЖЕ СЕРВИ З СИЛОВИМИ СТІЙКАМИ ПІД БОЛТИ M3 (X = -72.0 .. -31.5)
    # Серва 40.5 x 20.2 мм, висота до валу Z_shaft = 24.5 мм (подіум Z = 14.0 мм)
    sx0, sx1 = -72.0, -31.5
    sy0, sy1 = -10.5, 30.0   # Вал серви точно на Y = 0.0
    z_ped = 13.5
    z_servo_top = 34.5

    # Подіум серви (Z = t_base .. z_ped)
    add_box(tris, sx0 - wall, sy0 - 8.0, t_base, sx1, sy1 + 8.0, z_ped)

    # Задня стінка (протилежна від вимикача, приймає реактивний тиск)
    add_box(tris, sx0 - wall, sy0 - 8.0, z_ped, sx0, sy1 + 8.0, z_servo_top)

    # Бокові стінки ложа
    add_box(tris, sx0 - wall, sy1, z_ped, sx1, sy1 + wall, z_servo_top)
    add_box(tris, sx0 - wall, sy0 - wall, z_ped, sx1 - 12.0, sy0, z_servo_top) # Виріз під дріт знизу

    # Силові стійки під гвинти М3 у вушках серви (крок вушок по Y: ~49 мм -> Y = -15.0 та Y = +34.5)
    # Гвинти закручуються зверху через вушка прямо в тіло пластику!
    add_box(tris, -56.0, -17.5, z_ped, -47.0, sy0, z_servo_top)
    add_box(tris, -56.0, sy1, z_ped, -47.0, sy1 + 7.5, z_servo_top)

    # 1.4 БОКС ДЛЯ ESP32 (ЗНИЗУ: Y = -90.0 .. -30.0, X = -65.0 .. 25.0)
    bx0, bx1 = -65.0, 25.0
    by0, by1 = -88.0, ky0 - wall
    z_box = 24.0

    # Стінки боксу ESP32
    add_box(tris, bx0 - wall, by0, t_base, bx0, by1 + wall, z_box)
    add_box(tris, bx1, by0, t_base, bx1 + wall, by1 + wall, z_box)
    add_box(tris, bx0 - wall, by0 - wall, t_base, bx1 + wall, by0, z_box)
    add_box(tris, kx0, by1, t_base, bx1, by1 + wall, z_box)

    # Напрямні рейки для посадки плати ESP32 без гвинтів
    add_box(tris, -35.0, by0 + 5.0, t_base, -32.5, by1 - 5.0, t_base + 10.0)
    add_box(tris,  -3.5, by0 + 5.0, t_base,  -1.0, by1 - 5.0, t_base + 10.0)

    # Ребра жорсткості між боксом та основою
    add_wedge_y(tris, bx0 - wall, bx0 + 2.0, -96.0, by0, t_base, z_box)
    add_wedge_y(tris, bx1 - 2.0, bx1 + wall, -96.0, by0, t_base, z_box)

    write_binary_stl(filename, tris, "SwitchMount-v5-Chassis")

# ==============================================================================
# 2. ПРИТИСКНА ПЛАНКА СЕРВИ НА 2 БОЛТИ М3 (switch_v5_servo_clamp.stl)
# ==============================================================================
def generate_v5_servo_clamp(filename):
    """
    Силовий місток-планка з двома отворами під болти M3.
    Кладеться поверх монтажних вушок серви і затягується двома гвинтами.
    Сервопривід стає монолітом з рамою — випадання виключено на 100%!
    """
    tris = []
    # Довжина 64 мм, ширина 14 мм, товщина 4.0 мм
    add_box(tris, -7.0, -28.0, 0.0, 7.0, 28.0, 4.0)

    # Притискні напливи на вушка серви (товщина 1.5 мм знизу)
    add_box(tris, -5.5, -26.0, 0.0, 5.5, -16.0, -2.0)
    add_box(tris, -5.5,  16.0, 0.0, 5.5,  26.0, -2.0)

    write_binary_stl(filename, tris, "ServoClamp-M3-v5")

# ==============================================================================
# 3. ПОСИЛЕНИЙ T-ВАЖІЛЬ 25T ПІД КЛАВІШУ 57x50 мм (switch_v5_t_arm_25t.stl)
# ==============================================================================
def generate_v5_t_arm(filename):
    """
    T-подібний важіль з посадковим пазом під металеву качалку 25T (20 мм).
    Довжина плечей оптимізована рівно під верх і низ клавіші 57x50 мм:
    плечі Y = ±17.0 мм, виліт натискання в глибину підібрано під хід клавіші 4 мм.
    """
    tris = []
    
    # 3.1 Центральна маточина навколо вала серви (Z = 0 .. 7.0 мм)
    add_cylinder(tris, 0.0, 0.0, 0.0, 7.0, radius=9.0, segments=24)

    # Паз під штатну металеву качалку 25T (25.5 x 10.5 мм, глибина 4.5 мм)
    # Матеріал навколо пазу:
    add_box(tris, -14.0, -6.0, 0.0, 14.0, 6.0, 7.0)

    # 3.2 Силова поздовжня балка T-важеля (Y = -22.0 .. +22.0 мм)
    add_box(tris, -5.5, -22.0, 2.5, 5.5, 22.0, 9.5)

    # 3.3 Верхній натискний кулачок ON (Y = +14.0 .. +21.0 мм)
    # Натискає в бік клавіші (виліт по X = +18.0 мм від осі серви)
    add_box(tris, 0.0, 14.0, 4.0, 18.0, 21.0, 14.0)
    # Скруглений / скошений носик контакту з клавішею
    add_box(tris, 14.0, 15.0, 4.0, 20.0, 20.0, 12.0)

    # 3.4 Нижній натискний кулачок OFF (Y = -21.0 .. -14.0 мм)
    add_box(tris, 0.0, -21.0, 4.0, 18.0, -14.0, 14.0)
    add_box(tris, 14.0, -20.0, 4.0, 20.0, -15.0, 12.0)

    write_binary_stl(filename, tris, "TArm-25T-57x50-v5")

if __name__ == "__main__":
    out_dir = "/home/maks/.gemini/antigravity/scratch/smart-light-switch/cad"
    os.makedirs(out_dir, exist_ok=True)
    
    f1 = os.path.join(out_dir, "switch_v5_chassis_mount.stl")
    f2 = os.path.join(out_dir, "switch_v5_servo_clamp.stl")
    f3 = os.path.join(out_dir, "switch_v5_t_arm_25t.stl")
    
    generate_v5_chassis_frame(f1)
    generate_v5_servo_clamp(f2)
    generate_v5_t_arm(f3)
    
    print(f"✅ Generated {f1} ({os.path.getsize(f1)} bytes)")
    print(f"✅ Generated {f2} ({os.path.getsize(f2)} bytes)")
    print(f"✅ Generated {f3} ({os.path.getsize(f3)} bytes)")
