from PIL import Image, ImageDraw, ImageFont
import os

OUTPUT_DIR = "/Users/mica/Desktop/simona/Imagenes"

# Fuentes
def get_font(name, size):
    for base in ["/Library/Fonts", "/System/Library/Fonts"]:
        p = f"{base}/{name}"
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

font_title  = get_font("Georgia Bold.ttf", 36)
font_header = get_font("Arial Bold.ttf",   15)
font_talle  = get_font("Arial Bold.ttf",   16)
font_medida = get_font("Arial.ttf",        16)
font_label  = get_font("Arial.ttf",        11)
font_label_b= get_font("Arial Bold.ttf",   11)

BG         = (245, 237, 230)
WHITE      = (255, 255, 255)
HEADER_ROW = (210, 186, 176)
BORDO      = (144, 38,  58)
DARK       = (55,  45,  42)
GRAY       = (120, 110, 105)
LINE_COLOR = (224, 214, 208)

W, H = 1100, 580

def draw_shirt(draw, ox, oy, sw=200, sh=260):
    """
    Camisa de manga corta vista de frente.
    Polígono único en forma de T con cuello y V-neck.
    """
    # ── Puntos clave (relativos a ox, oy) ──────────────────
    # Cuello (banda estrecha arriba del centro)
    nc_l = ox + sw*0.38;  nc_r = ox + sw*0.62
    nc_top = oy + sh*0.02; nc_bot = oy + sh*0.14

    # Hombros → arranque de manga (diagonal suave)
    sh_l = ox + sw*0.10;  sh_r = ox + sw*0.90
    sh_y  = oy + sh*0.20   # línea de hombro donde empieza la manga

    # Mangas cortas (termina ≈ 35% del alto)
    sl_top_l = ox + sw*0.02
    sl_top_r = ox + sw*0.98
    sl_bot_y = oy + sh*0.38

    # Cuerpo
    bd_l = ox + sw*0.20;  bd_r = ox + sw*0.80
    hem_y = oy + sh*0.92

    # V-neck tip
    v_tip_y = oy + sh*0.46

    # ── Contorno completo (CW) ──────────────────────────────
    outline = [
        (nc_l,    nc_top),       # 0: cuello izq top
        (nc_r,    nc_top),       # 1: cuello der top
        (nc_r,    nc_bot),       # 2: hombro der interno
        (sl_top_r, sh_y),        # 3: manga der top (diagonal hombro→manga)
        (sl_top_r, sl_bot_y),    # 4: manga der bot (extremo)
        (bd_r,    sl_bot_y),     # 5: axila der
        (bd_r,    hem_y),        # 6: ruedo der
        (bd_l,    hem_y),        # 7: ruedo izq
        (bd_l,    sl_bot_y),     # 8: axila izq
        (sl_top_l, sl_bot_y),    # 9: manga izq bot
        (sl_top_l, sh_y),        # 10: manga izq top
        (nc_l,    nc_bot),       # 11: hombro izq interno
    ]
    draw.polygon(outline, fill=WHITE, outline=DARK)

    # Línea de cuello (separa banda del cuerpo)
    draw.line([(nc_l, nc_bot), (nc_r, nc_bot)], fill=DARK, width=1)

    # V-neck
    cx = ox + sw * 0.50
    draw.line([(nc_l, nc_bot), (cx, v_tip_y)], fill=DARK, width=1)
    draw.line([(nc_r, nc_bot), (cx, v_tip_y)], fill=DARK, width=1)

    # ── Líneas de medida ───────────────────────────────────
    DOT = 5

    def dot(x, y):
        draw.ellipse([(x-DOT, y-DOT), (x+DOT, y+DOT)], fill=BORDO)

    # A = HOMBROS: de extremo a extremo de mangas en la parte superior
    ay = sh_y - 8
    draw.line([(sl_top_l, ay), (sl_top_r, ay)], fill=BORDO, width=2)
    dot(sl_top_l, ay); dot(sl_top_r, ay)
    draw.text((ox, ay - 18), 'A', font=font_label_b, fill=BORDO)

    # B = SISA: costado izq desde hombro hasta axila
    bx = bd_l - 14
    draw.line([(bx, sh_y), (bx, sl_bot_y)], fill=BORDO, width=2)
    dot(bx, sh_y); dot(bx, sl_bot_y)
    draw.text((bx - 16, (sh_y + sl_bot_y)//2 - 8), 'B', font=font_label_b, fill=BORDO)

    # C = LARGO: costado der desde hombro al ruedo
    cx2 = int(bd_r + 14)
    draw.line([(cx2, sh_y), (cx2, hem_y)], fill=BORDO, width=2)
    dot(cx2, sh_y); dot(cx2, hem_y)
    draw.text((cx2 + 5, int((sh_y + hem_y)//2) - 8), 'C', font=font_label_b, fill=BORDO)

    # Leyendas al pie
    for i, txt in enumerate(["A - Medida de hombros", "B - Medida de sisa", "C - Largo"]):
        draw.text((ox, int(hem_y) + 18 + i*18), txt, font=font_label, fill=GRAY)

# ── Genera la imagen de guía de talles ──────────────────────
def make_guide(filename, title, columns, rows):
    img  = Image.new('RGB', (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Tarjeta sketch
    card_x, card_y, card_w, card_h = 38, 45, 295, 460
    draw.rounded_rectangle([card_x, card_y, card_x+card_w, card_y+card_h],
                            radius=18, fill=WHITE)

    # Sketch camisa
    sk_x = card_x + 28
    sk_y = card_y + 28
    draw_shirt(draw, sk_x, sk_y, sw=230, sh=280)

    # ── Tabla ──────────────────────────────────────────────
    tx     = 368
    ty0    = 55
    ncols  = len(columns) + 1
    col_w  = min(158, (W - tx - 20) // ncols)
    row_h  = 54
    tbl_w  = col_w * ncols

    # Título
    draw.text((tx, ty0), title, font=font_title, fill=DARK)

    # Header
    hdr_y = ty0 + 58
    draw.rounded_rectangle([tx, hdr_y, tx+tbl_w, hdr_y+row_h],
                            radius=6, fill=HEADER_ROW)
    headers = ['MEDIDAS'] + columns
    for i, hdr in enumerate(headers):
        hw  = draw.textlength(hdr, font=font_header)
        hx  = tx + i*col_w + (10 if i == 0 else (col_w-hw)//2)
        draw.text((hx, hdr_y+18), hdr, font=font_header, fill=DARK)

    # Filas
    for ri, (talle, vals) in enumerate(rows):
        ry     = hdr_y + row_h + ri * row_h
        row_bg = WHITE if ri % 2 == 0 else (250, 244, 240)
        draw.rectangle([tx, ry, tx+tbl_w, ry+row_h], fill=row_bg)
        draw.line([(tx, ry), (tx+tbl_w, ry)], fill=LINE_COLOR, width=1)
        draw.text((tx+12, ry+17), talle, font=font_talle, fill=DARK)
        for vi, val in enumerate(vals):
            vw = draw.textlength(val, font=font_medida)
            vx = tx + (vi+1)*col_w + (col_w-vw)//2
            draw.text((vx, ry+17), val, font=font_medida, fill=DARK)

    # Borde inferior tabla
    bot_y = hdr_y + row_h + len(rows) * row_h
    draw.line([(tx, bot_y), (tx+tbl_w, bot_y)], fill=LINE_COLOR, width=1)

    # Línea decorativa superior
    draw.rectangle([0, 0, W, 4], fill=BORDO)

    out = os.path.join(OUTPUT_DIR, filename)
    img.save(out, 'PNG')
    print(f"  ✓ {filename}")

# ── Datos de los 5 productos ────────────────────────────────
productos = [
    dict(filename='camisa-domaine.png',    title='Camisa Domaine',
         columns=['HOMBROS','SISA','LARGO'],
         rows=[('TALLE S',['38 CM','46 CM','65 CM']),
               ('TALLE M',['40 CM','49 CM','66 CM']),
               ('TALLE L',['42 CM','52 CM','67 CM'])]),

    dict(filename='camisa-pinot-negro.png', title='Camisa Pinot Negro',
         columns=['SISA','LARGO'],
         rows=[('TALLE S',['57 CM','65 CM']),
               ('TALLE M',['59 CM','67 CM']),
               ('TALLE L',['61 CM','69 CM'])]),

    dict(filename='camisa-noir.png',        title='Camisa Noir',
         columns=['HOMBROS','SISA','LARGO'],
         rows=[('TALLE S',['35 CM','48 CM','59 CM']),
               ('TALLE M',['37 CM','50 CM','61 CM']),
               ('TALLE L',['39 CM','52 CM','63 CM'])]),

    dict(filename='camisa-huella.png',      title='Camisa Huella',
         columns=['HOMBROS','SISA','LARGO AD.','LARGO AT.'],
         rows=[('TALLE S',['34 CM','47 CM','64 CM','68 CM']),
               ('TALLE M',['36 CM','49 CM','66 CM','70 CM']),
               ('TALLE L',['38 CM','52 CM','68 CM','72 CM'])]),

    dict(filename='camisa-olivo.png',       title='Camisa Olivo',
         columns=['HOMBROS','SISA','LARGO'],
         rows=[('TALLE S',['35 CM','51 CM','62 CM']),
               ('TALLE M',['37 CM','53 CM','64 CM']),
               ('TALLE L',['39 CM','55 CM','66 CM'])]),
]

print("Generando guías de talle...")
for p in productos:
    make_guide(p['filename'], p['title'], p['columns'], p['rows'])
print(f"\nListo → {OUTPUT_DIR}")
