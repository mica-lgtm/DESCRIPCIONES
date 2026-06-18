import csv
import re
import os
from pathlib import Path

CDN_BASE = "https://d1a9qnv764bsoo.cloudfront.net/stores/601/496/rte/"
IMG_DIR = Path("/Users/mica/Desktop/simona/Imagenes")
INPUT_CSV = "/Users/mica/Documents/Codex/2026-06-11/files-mentioned-by-the-user-skill/outputs/SWATERS-BUZOS-ORIGINAL-with-size-images.csv"
OUTPUT_CSV = "/Users/mica/Desktop/simona/Nuevas/SWATERS-BUZOS-ORIGINAL-with-size-images-plantilla.csv"

def slugify(text):
    text = (text or "").lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")

def build_image_index():
    indexed = {}
    for path in IMG_DIR.rglob("*.png"):
        rel = path.relative_to(IMG_DIR).as_posix()
        stem = path.stem.lower()
        normalized = re.sub(r"^\d+[-_ ]*", "", stem)
        for key in {stem, normalized}:
            indexed.setdefault(key, []).append(rel)
    return indexed

images = build_image_index()

MANUAL_MAPPING = {
    'camisa-cumbre-beige-1bcqp':  'camisa-cumbre-chocolate-con-leche.png',
    'camisa-lidia':               'camisa-domaine.png',
    'camisa-violeta-negro':       'camisa-pinot-negro.png',
    'camisa-andrea':              'camisa-noir.png',
    'camisa-carolina':            'camisa-huella.png',
    'camisa-catalina':            'camisa-olivo.png',
}

def find_image(product_id, nombre=''):
    if product_id in MANUAL_MAPPING:
        return MANUAL_MAPPING[product_id]

    slug = product_id.rsplit('-', 1)[0].lower().strip()
    name_slug = slugify(nombre)
    candidates = [
        slug,
        f"{slug}-talles",
        name_slug,
        f"{name_slug}-talles" if name_slug else '',
    ]

    for key in candidates:
        if key and key in images:
            return images[key][0]

    for rels in images.values():
        for rel in rels:
            stem = Path(rel).stem.lower()
            normalized = re.sub(r"^\d+[-_ ]*", "", stem)
            if normalized.endswith(slug) or normalized.startswith(slug):
                return rel
    return None

def decode_html(text):
    for k, v in {
        '&nbsp;': ' ', '&ndash;': '–', '&mdash;': '—', '&amp;': '&',
        '&lt;': '<', '&gt;': '>', '&aacute;': 'á', '&eacute;': 'é',
        '&iacute;': 'í', '&oacute;': 'ó', '&uacute;': 'ú', '&ntilde;': 'ñ',
        '&Aacute;': 'Á', '&Eacute;': 'É', '&Iacute;': 'Í', '&Oacute;': 'Ó',
        '&Uacute;': 'Ú', '&Ntilde;': 'Ñ', '&uuml;': 'ü', '&#39;': "'",
    }.items():
        text = text.replace(k, v)
    return text

def strip_tags(html):
    html = re.sub(r'<br\s*/?>', ' | ', html, flags=re.IGNORECASE)
    clean = re.sub(r'<[^>]+>', '', html)
    clean = decode_html(clean)
    clean = re.sub(r'[?✨🌿💧👗]', '', clean)  # emojis rotos
    return ' '.join(clean.split()).strip()

def is_mostly_uppercase(text):
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    return sum(1 for c in letters if c.isupper()) / len(letters) > 0.65

def parse_description(html):
    data = {
        'tagline': '', 'material': '', 'diseno': '',
        'calce': '', 'estilo': '', 'cuidados': [],
        'ale_talle': '', 'modelo_talle': '', 'modelo_nombre': '',
        'image_src': '',
        'detalles': '',
    }

    img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html, flags=re.IGNORECASE)
    if img_match:
        data['image_src'] = img_match.group(1)

    paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL | re.IGNORECASE)

    # Tagline = primer párrafo limpio, largo, no campo técnico, no mayúsculas título
    skip_words = ['material', 'diseño', 'dise&ntilde', 'calce:', 'estilo:', 'cuidados',
                  'medidas', 'talle', '&nbsp', 'cómo usar', 'como usar', 'detalles de']
    for p in paragraphs:
        text = strip_tags(p)
        if not text or len(text) < 15:
            continue
        if any(w in p.lower() for w in skip_words):
            continue
        if is_mostly_uppercase(text):   # saltar títulos en MAYÚSCULAS
            continue
        data['tagline'] = text.rstrip('?–—').strip()
        break

    # Campos de detalle — patrones flexibles
    for p in paragraphs:
        raw = strip_tags(p)
        lower = raw.lower()

        # Material / Material Premium
        if re.search(r'material\b[^:]{0,20}:', lower) and not data['material']:
            data['material'] = re.sub(r'.*?material[^:]{0,20}:\s*', '', raw, flags=re.IGNORECASE).strip()

        # Diseño / Diseño Versátil / Detalles de Puntilla
        if re.search(r'(dise[ñn]o|detalles de puntilla)\b[^:]{0,20}:', lower) and not data['diseno']:
            m = re.sub(r'.*?(?:dise[ñn]o|detalles de puntilla)[^:]{0,20}:\s*', '', raw, flags=re.IGNORECASE).strip()
            if len(m) > 10:
                data['diseno'] = m

        # Calce / Calce Cómodo
        if re.search(r'calce\b[^:]{0,15}:', lower) and not data['calce']:
            data['calce'] = re.sub(r'.*?calce[^:]{0,15}:\s*', '', raw, flags=re.IGNORECASE).strip()

        # Estilo / Cómo usarla / Diseño Versátil
        if re.search(r'(estilo|cómo usar|como usar|diseño vers)', lower) and not data['estilo']:
            m = re.sub(r'.*?(?:estilo|cómo usar[^:]*|como usar[^:]*|diseño vers[^:]*)[^:]{0,10}:\s*',
                       '', raw, flags=re.IGNORECASE).strip()
            if len(m) > 10:
                data['estilo'] = m

        # Detalles: (campo extra — capturar si existe)
        if re.search(r'^detalles\s*:', lower) and not data.get('detalles'):
            data['detalles'] = re.sub(r'.*?detalles\s*:\s*', '', raw, flags=re.IGNORECASE).strip()

    # Cuidados: buscar todo el bloque después de "Cuidados"
    cuidados_match = re.search(r'cuidados[^<]{0,5}[:;]?\s*(.*?)(?:medidas|MEDIDAS|talle s\b|$)',
                                html, re.IGNORECASE | re.DOTALL)
    if cuidados_match:
        care_raw = strip_tags(cuidados_match.group(1))
        # Separar por bullets, pipes, o puntos seguidos de mayúscula
        items = re.split(r'[•·|\n]|(?<=\.)\s+(?=[A-ZÁÉÍÓÚ])', care_raw)
        items = [i.strip().rstrip('.').strip() for i in items if len(i.strip()) > 5]
        data['cuidados'] = items[:4]

    if not data['cuidados']:
        data['cuidados'] = ['Lavar a mano o en ciclo delicado', 'Sin lavandina', 'Secar a la sombra']

    # Talle de Ale — todas las variantes
    full = strip_tags(html)
    ale = re.search(r'ale\b[^.]{0,50}talle\s+([A-Z]{1,3})', full, re.IGNORECASE)
    if ale:
        data['ale_talle'] = ale.group(1).upper()

    # Talle del modelo
    for pattern, nombre in [
        (r'la modelo de la foto\s+usa\s+talle\s+([A-Z]{1,3})', 'La modelo de la foto'),
        (r'cami\s+usa\s+talle\s+([A-Z]{1,3})', 'Cami'),
        (r'la modelo\s+usa\s+talle\s+([A-Z]{1,3})', 'La modelo'),
    ]:
        m = re.search(pattern, full, re.IGNORECASE)
        if m:
            data['modelo_nombre'] = nombre
            data['modelo_talle'] = m.group(1).upper()
            break

    return data

def get_season(categoria):
    cat = (categoria or '').upper()
    if 'OTO' in cat and 'INVIERNO' in cat:
        return 'Otoño · Invierno'
    if 'PRIMAVERA' in cat or 'VERANO' in cat:
        return 'Primavera · Verano'
    return 'Nueva Colección'

def build_html(nombre, season, data, img_file):
    img_url = data.get('image_src') or (CDN_BASE + img_file if img_file else '')
    tagline = data['tagline'] or ''
    tagline_quoted = f'"{tagline}"' if tagline else '""'

    campos = [
        ('Material', data['material']),
        ('Diseño', data['diseno']),
        ('Calce', data['calce']),
        ('Estilo', data['estilo']),
    ]
    campos = [(k, v) for k, v in campos if v]

    filas = []
    for idx, (key, value) in enumerate(campos):
        border = 'border-bottom:1px solid #f0efec;' if idx < len(campos) - 1 else ''
        filas.append(
            f'''    <tr style="{border}">
      <td style="padding:12px 0;width:100px;vertical-align:top;">
        <span style="font-size:9px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#A2897B;">{key}</span>
      </td>
      <td style="padding:12px 0;font-size:13px;color:#444;line-height:1.6;">
        {value}
      </td>
    </tr>'''
        )

    chips = [
        f'<span style="background:#fff;color:#555;font-size:11px;padding:5px 13px;letter-spacing:0.3px;">&#10022; {c}</span>'
        for c in data['cuidados']
    ]
    chips_html = '\n    '.join(chips)

    ale_block = ''
    if data['ale_talle']:
        ale_block = f'''
  <!-- Referencia Ale -->
  <div style="background:#90263A;padding:14px 20px;margin-bottom:16px;display:flex;align-items:center;gap:14px;">
    <div style="width:36px;height:36px;border-radius:50%;background:#ffffff;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
      <span style="font-size:14px;font-weight:700;color:#90263A;">A</span>
    </div>
    <div>
      <p style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:#D5C792;margin-bottom:3px;">Referencia de talle</p>
      <p style="font-size:14px;color:#ffffff;font-weight:700;letter-spacing:0.3px;">Ale usa talle {data["ale_talle"]} en este modelo</p>
    </div>
  </div>'''

    modelo_line = ''
    if data['modelo_nombre'] and data['modelo_talle']:
        modelo_line = f'\n  <!-- Cami -->\n  <p style="font-size:11px;color:#aaa;text-align:center;margin-bottom:10px;">{data["modelo_nombre"]} usa talle {data["modelo_talle"]}</p>'

    img_section = ''
    if img_url:
        img_section = f'''
<!-- GUÍA DE TALLES -->
<div style="background:#f7f4f1;padding:22px 28px 18px;margin-top:2px;border-top:1px solid #e0dbd5;">
  <p style="font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#90263A;margin-bottom:14px;">Guía de talles</p>
  <img src="{img_url}" alt="Guía de talles {nombre}" style="display:block;width:100%;height:auto;" />
</div>'''

    return f'''<!-- HERO -->
<div style="background:#e9eae5;padding:36px 32px 30px;text-align:center;position:relative;overflow:hidden;">
  <div style="position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,#90263A,#D5C792,#A2897B);"></div>
  <span style="display:inline-block;border:1px solid #A2897B;color:#A2897B;font-size:9px;font-weight:700;letter-spacing:2.5px;text-transform:uppercase;padding:4px 14px;margin-bottom:18px;font-family:'Lato',sans-serif;">{season}</span>
  <h1 style="font-family:'Playfair Display',Georgia,serif;color:#3a2a2a;font-size:26px;font-weight:600;line-height:1.2;margin-bottom:10px;">{nombre}</h1>
  <p style="color:#A2897B;font-size:13px;font-weight:300;letter-spacing:0.5px;font-style:italic;">{tagline}</p>
</div>

<!-- TAGLINE -->
<div style="background:#ffffff;padding:20px 28px;border-left:3px solid #90263A;">
  <p style="font-family:'Playfair Display',Georgia,serif;font-size:15px;color:#333;line-height:1.7;font-style:italic;">
    {tagline_quoted}
  </p>
</div>

<!-- CARACTERÍSTICAS -->
<div style="background:#ffffff;padding:24px 28px;margin-top:2px;">
  <p style="font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#90263A;margin-bottom:18px;">Detalles de la prenda</p>

  <table style="width:100%;border-collapse:collapse;">
{chr(10).join(filas)}
  </table>
</div>

<!-- CUIDADOS -->
<div style="background:#e9eae5;padding:20px 28px;margin-top:2px;display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
  <span style="font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#90263A;flex-shrink:0;">Cuidados</span>
  <div style="display:flex;gap:8px;flex-wrap:wrap;">
    {chips_html}
  </div>
</div>

{img_section}

<!-- NOTA FINAL -->
<div style="background:#ffffff;padding:20px 28px 24px;margin-top:2px;border-bottom:3px solid #90263A;">
{ale_block}
{modelo_line}
  <p style="font-size:10px;color:#000;text-align:center;font-style:italic;margin:0;">Todas las medidas son aproximadas y lineales. No son de contorno.</p>
</div>'''


# ── Procesar CSV ──────────────────────────────────────────────
processed = []
skipped = []

with open(INPUT_CSV, 'r', encoding='latin-1', newline='') as infile, \
     open(OUTPUT_CSV, 'w', encoding='utf-8-sig', newline='') as outfile:

    reader = csv.reader(infile, delimiter=';', quotechar='"')
    writer = csv.writer(outfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    for i, row in enumerate(reader):
        if i == 0:
            writer.writerow(row)
            continue

        product_id = row[0].strip()
        nombre = row[1].strip() if len(row) > 1 else ''
        categoria = row[2].strip() if len(row) > 2 else ''
        desc_idx = 20

        if nombre and product_id and len(row) > desc_idx:
            img_file = find_image(product_id, nombre)
            season = get_season(categoria)
            parsed = parse_description(row[desc_idx])
            row[desc_idx] = build_html(nombre, season, parsed, img_file)

            status = f"✓ {nombre} | talle Ale: {parsed['ale_talle'] or '?'} | img: {img_file or 'sin imagen'}"
            processed.append(status)

        writer.writerow(row)

print(f"\n{'='*55}")
print(f"CSV generado: {OUTPUT_CSV}")
print(f"\nProductos procesados ({len(processed)}):")
for p in processed:
    print(f"  {p}")
print(f"\nTotal: {len(processed)} productos")
