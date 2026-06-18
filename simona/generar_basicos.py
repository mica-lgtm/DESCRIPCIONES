#!/usr/bin/env python3
"""
Aplica el template rico (mismo que generar_plantilla.py) a los básicos.
Reemplaza la tabla de medidas por la imagen CloudFront correspondiente.
Deja intactos jean-nascar1 y jean-imola (ya tienen el template).
"""

import csv
import re
import io

INPUT_CSV  = '/root/.claude/uploads/f65578b5-cc43-5cfd-a6c9-166cbe2a0b7b/52a467ef-tiendanube60149617817924885958912531303063382.csv'
OUTPUT_CSV = '/home/user/DESCRIPCIONES/simona/basicos-con-template.csv'
CDN_BASE   = 'https://d1a9qnv764bsoo.cloudfront.net/stores/601/496/rte/'

IMAGE_MAP = {
    'pack-x-2-camisa-clasica':              '02-pack-x-2-camisa-clasica.png',
    'pack-x-3-remeras-basicas-escote-en-v': '03-pack-x-3-remeras-basicas-escote-en-v-blanco-negro-gris.png',
    'remera-basica-escote-en-v-gris':       '04-remera-basica-escote-en-v-gris.png',
    'remera-basica-escote-en-v-blanco':     '05-remera-basica-escote-en-v-blanco.png',
    'remera-basica-escote-en-v-negro':      '06-remera-basica-escote-en-v-negro.png',
    'musculosa-abril-negro2':               '07-musculosa-abril-negro.png',
    'musculosa-abril-blanco2':              '08-musculosa-abril-blanco.png',
    'musculosa-abril-gris2':                '09-musculosa-abril-gris.png',
    'musculosa-daily-negro3':               '10-musculosa-daily-negro.png',
    'musculosa-daily-gris1':                '11-musculosa-daily-gris.png',
    'musculosa-daily-blanco3':              '12-musculosa-daily-blanco.png',
    'pack-x2-top-mina':                     '13-pack-x2-top-mina.png',
    'pack-x-3-musculosa-daily1':            '14-pack-x-3-musculosa-daily.png',
    'pack-x-3-musculosa-abril1':            '15-pack-x-3-musculosa-abril.png',
    'pack-x-3-remeras-basicas':             '16-pack-x-3-remeras-basicas-blanco-negro-gris.png',
    'top-mina-negro':                       '17-top-mina-negro.png',
    'top-mina-blanco':                      '18-top-mina-blanco.png',
    'remera-basica-gris':                   '19-remera-basica-gris.png',
    'camisa-clasica-negro':                 '20-camisa-clasica-negro.png',
    'camisa-clasica-blanco':                '21-camisa-clasica-blanco.png',
    'remera-basica-negro':                  '22-remera-basica-negro.png',
    'remera-basica-blanco':                 '23-remera-basica-blanco.png',
}

PACKS = {
    'pack-x-2-camisa-clasica',
    'pack-x-3-remeras-basicas-escote-en-v',
    'pack-x2-top-mina',
    'pack-x-3-musculosa-daily1',
    'pack-x-3-musculosa-abril1',
    'pack-x-3-remeras-basicas',
}

# Overrides manuales para productos con HTML demasiado corrupto para parsear bien
MANUAL_OVERRIDES = {
    'camisa-clasica-negro': {
        'tagline': 'Ligereza y elegancia en voile 100% algod&oacute;n',
        'material': 'Voile 100% algod&oacute;n, liviana y suave al tacto. M&aacute;xima frescura y comodidad.',
        'diseno': 'Corte cl&aacute;sico y atemporal, cuello camisero y botones al frente. Calce relajado y fluido.',
        'detalles': '',
        'calce': '',
        'estilo': 'Ideal para looks urbanos o m&aacute;s formales. Combina con jeans, pantalones sastreros o faldas.',
        'incluye': '',
        'como': '',
        'cuidados': ['Lavar a mano o a m&aacute;quina con agua fr&iacute;a', 'Sin blanqueadores', 'Secar colgada a la sombra', 'Planchar a baja temperatura'],
        'ale_talle': 'L',
        'modelo_talle': 'S',
        'modelo_nombre': 'La modelo de la foto',
    },
    'camisa-clasica-blanco': {
        'tagline': 'Ligereza y elegancia en voile 100% algod&oacute;n',
        'material': 'Voile 100% algod&oacute;n, liviana y suave al tacto. M&aacute;xima frescura y comodidad.',
        'diseno': 'Corte cl&aacute;sico y atemporal, cuello camisero y botones al frente. Calce relajado y fluido.',
        'detalles': '',
        'calce': '',
        'estilo': 'Ideal para looks urbanos o m&aacute;s formales. Combina con jeans, pantalones sastreros o faldas.',
        'incluye': '',
        'como': '',
        'cuidados': ['Lavar a mano o a m&aacute;quina con agua fr&iacute;a', 'Sin blanqueadores', 'Secar colgada a la sombra', 'Planchar a baja temperatura'],
        'ale_talle': 'L',
        'modelo_talle': 'S',
        'modelo_nombre': 'La modelo de la foto',
    },
}

# ── Parseo de descripción existente ──────────────────────────────────────────

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
    clean = re.sub(r'[?✨🌿💧👗✦]', '', clean)
    return ' '.join(clean.split()).strip()

def is_mostly_uppercase(text):
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    return sum(1 for c in letters if c.isupper()) / len(letters) > 0.65

def extract_inner(html):
    """Saca el contenido de dentro del wrapper ChatGPT si existe."""
    m = re.search(r'<div class="markdown[^"]*"[^>]*>(.*)</div>\s*</div>\s*</div>\s*</div>',
                  html, re.DOTALL)
    if m:
        return m.group(1).strip()
    return html

def parse_description(html):
    html = extract_inner(html)

    data = {
        'tagline': '', 'material': '', 'diseno': '', 'detalles': '',
        'calce': '', 'estilo': '', 'incluye': '', 'como': '',
        'cuidados': [], 'ale_talle': '', 'modelo_talle': '', 'modelo_nombre': '',
    }

    # Obtener párrafos completos y segmentos <br>-separados dentro de cada uno
    paragraphs_full = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL | re.IGNORECASE)
    segments = []
    for p_content in paragraphs_full:
        br_parts = re.split(r'<br[^>]*/>', p_content, flags=re.IGNORECASE)
        if len(br_parts) > 1:
            # Guardar el párrafo completo primero para detección de "Características"
            segments.append(('full_p', p_content))
            for bp in br_parts:
                segments.append(('br_seg', bp))
        else:
            segments.append(('full_p', p_content))

    # Tagline: primer segmento largo que no sea un campo técnico ni mayúsculas
    skip_words = ['material', 'diseño', 'dise&ntilde', 'calce', 'estilo', 'cuidados',
                  'medidas', 'talle', '&nbsp', 'cómo', 'como usar', 'detalles', 'incluye',
                  'característica', 'caracter&iacute']
    for kind, seg in segments:
        if kind != 'full_p':
            continue
        text = strip_tags(seg)
        if not text or len(text) < 15:
            continue
        if any(w in seg.lower() for w in skip_words):
            continue
        if is_mostly_uppercase(text):
            continue
        data['tagline'] = text.rstrip('?–—').strip()
        break

    def extract_field(seg, pattern):
        raw = strip_tags(seg)
        return re.sub(pattern, '', raw, flags=re.IGNORECASE).strip()

    def map_caracteristica(text):
        """Mapea un bullet de 'Características destacadas' al campo correspondiente."""
        lower = text.lower()
        if any(w in lower for w in ['tela', 'material', 'tejido', 'algod', 'jersey', 'microfibra', 'voile', 'poplin']):
            return 'material'
        if any(w in lower for w in ['corte', 'diseño', 'silueta', 'bretel', 'escote', 'cuello']):
            return 'diseno'
        if any(w in lower for w in ['calce', 'fit', 'ajuste']):
            return 'calce'
        return 'estilo'

    caracteristicas_done = False
    for kind, seg in segments:
        raw_text = strip_tags(seg)
        lower = raw_text.lower()

        # "Características destacadas:" → parsear bullets del párrafo completo
        if kind == 'full_p' and re.search(r'caracter[ií]sticas destacadas\b', lower) and not caracteristicas_done:
            caracteristicas_done = True
            bullet_parts = re.split(r'<br[^>]*/>', seg, flags=re.IGNORECASE)
            for bp in bullet_parts[1:]:  # Saltar la cabecera "Características destacadas:"
                bp_text = strip_tags(bp).lstrip('? ').strip()
                if len(bp_text) < 8:
                    continue
                field = map_caracteristica(bp_text)
                if not data[field]:
                    data[field] = bp_text
            continue

        # Para br_seg que viene de un full_p ya procesado como "Características", saltar
        if kind == 'br_seg' and caracteristicas_done and not any([data['material'], data['diseno']]):
            continue

        # Para full_p con múltiples campos (br_segs), no extraer campos individuales
        # Solo extraer de br_seg o full_p que sea un párrafo de un solo campo
        if kind == 'full_p':
            # Detectar si este párrafo tiene múltiples br separadores de campos
            br_count = len(re.findall(r'<br[^>]*/>', seg, re.IGNORECASE))
            if br_count >= 2:
                continue  # Tiene múltiples campos → ya fueron procesados como br_seg

        if re.search(r'material\b[^:]{0,20}:', lower) and not data['material']:
            data['material'] = extract_field(seg, r'.*?material[^:]{0,20}:\s*')

        elif re.search(r'dise[ñn]o\b[^:]{0,20}:', lower) and not data['diseno']:
            m = extract_field(seg, r'.*?dise[ñn]o[^:]{0,20}:\s*')
            if len(m) > 10:
                data['diseno'] = m

        elif re.search(r'detalles\b[^:]{0,15}:', lower) and not data['detalles']:
            data['detalles'] = extract_field(seg, r'.*?detalles[^:]{0,15}:\s*')

        elif re.search(r'calce\b[^:]{0,15}:', lower) and not data['calce']:
            data['calce'] = extract_field(seg, r'.*?calce[^:]{0,15}:\s*')

        elif re.search(r'estilo\b[^:]{0,15}:', lower) and not data['estilo']:
            m = extract_field(seg, r'.*?estilo[^:]{0,15}:\s*')
            if len(m) > 10:
                data['estilo'] = m

        elif re.search(r'incluye\b[^:]{0,10}:', lower) and not data['incluye']:
            data['incluye'] = extract_field(seg, r'.*?incluye[^:]{0,10}:\s*')

        elif re.search(r'c[oó]mo combin', lower) and not data['como']:
            data['como'] = extract_field(seg, r'.*?c[oó]mo combin[^:]{0,15}:\s*')

    # Cuidados: buscar bloque después de "Cuidados:"
    cuidados_match = re.search(r'cuidados[^<]{0,5}[:;]?\s*(.*?)(?:medidas|MEDIDAS|talle s\b|la modelo|$)',
                                html, re.IGNORECASE | re.DOTALL)
    if cuidados_match:
        care_raw = strip_tags(cuidados_match.group(1))
        items = re.split(r'[•·|\n]|(?<=\.)\s+(?=[A-ZÁÉÍÓÚ])', care_raw)
        items = [i.strip().rstrip('.').strip() for i in items if len(i.strip()) > 5]
        data['cuidados'] = items[:4]
    if not data['cuidados']:
        data['cuidados'] = ['Lavar a mano o en ciclo delicado', 'Sin lavandina', 'Secar a la sombra']

    full = strip_tags(html)
    ale = re.search(r'ale\b[^.]{0,50}talle\s+([A-Z]{1,3})', full, re.IGNORECASE)
    if ale:
        data['ale_talle'] = ale.group(1).upper()

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

# ── Constructor de HTML ───────────────────────────────────────────────────────

def build_html(nombre, data, img_url, is_pack=False):
    tagline = data['tagline'] or ''
    tagline_quoted = f'"{tagline}"' if tagline else ''

    campos = [
        ('Material',  data['material']),
        ('Dise&ntilde;o', data['diseno']),
        ('Detalles',  data['detalles']),
        ('Calce',     data['calce']),
        ('Estilo',    data['estilo']),
    ]
    campos = [(k, v) for k, v in campos if v]

    filas = []
    for idx, (key, value) in enumerate(campos):
        border = 'border-bottom:1px solid #f0efec;' if idx < len(campos) - 1 else ''
        filas.append(
            f'    <tr style="{border}">\n'
            f'      <td style="padding:12px 0;width:100px;vertical-align:top;">'
            f'<span style="font-size:9px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#A2897B;">{key}</span></td>\n'
            f'      <td style="padding:12px 0;font-size:13px;color:#444;line-height:1.6;">{value}</td>\n'
            f'    </tr>'
        )

    chips = [
        f'<span style="background:#fff;color:#555;font-size:11px;padding:5px 13px;letter-spacing:0.3px;">&#10022; {c}</span>'
        for c in data['cuidados']
    ]
    chips_html = '\n    '.join(chips)

    ale_block = ''
    if data['ale_talle']:
        ale_block = (
            f'\n  <div style="background:#90263A;padding:14px 20px;margin-bottom:16px;display:flex;align-items:center;gap:14px;">'
            f'<div style="width:36px;height:36px;border-radius:50%;background:#ffffff;display:flex;align-items:center;justify-content:center;flex-shrink:0;">'
            f'<span style="font-size:14px;font-weight:700;color:#90263A;">A</span></div>'
            f'<div><p style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:#D5C792;margin-bottom:3px;">Referencia de talle</p>'
            f'<p style="font-size:14px;color:#ffffff;font-weight:700;letter-spacing:0.3px;">Ale usa talle {data["ale_talle"]} en este modelo</p></div>'
            f'</div>'
        )

    modelo_line = ''
    if data['modelo_nombre'] and data['modelo_talle']:
        modelo_line = (
            f'\n  <p style="font-size:11px;color:#aaa;text-align:center;margin-bottom:10px;">'
            f'{data["modelo_nombre"]} usa talle {data["modelo_talle"]}</p>'
        )

    pack_line = ''
    if is_pack:
        pack_line = '\n  <p style="font-size:10px;color:#000;text-align:center;font-style:italic;margin:4px 0 0;">Todas las prendas del pack son del mismo talle seleccionado.</p>'

    img_section = ''
    if img_url:
        img_section = (
            f'\n<!-- GUÍA DE TALLES -->\n'
            f'<div style="background:#f7f4f1;padding:22px 28px 18px;margin-top:2px;border-top:1px solid #e0dbd5;">\n'
            f'  <p style="font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#90263A;margin-bottom:14px;">Gu&iacute;a de talles</p>\n'
            f'  <img src="{img_url}" alt="Gu&iacute;a de talles {nombre}" style="display:block;width:100%;height:auto;" />\n'
            f'</div>'
        )

    return (
        f'<!-- HERO -->\n'
        f'<div style="background:#e9eae5;padding:36px 32px 30px;text-align:center;position:relative;overflow:hidden;">\n'
        f'  <div style="position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,#90263A,#D5C792,#A2897B);"></div>\n'
        f'  <h1 style="font-family:\'Playfair Display\',Georgia,serif;color:#3a2a2a;font-size:26px;font-weight:600;line-height:1.2;margin-bottom:10px;">{nombre}</h1>\n'
        f'  <p style="color:#A2897B;font-size:13px;font-weight:300;letter-spacing:0.5px;font-style:italic;">{tagline}</p>\n'
        f'</div>\n\n'
        f'<!-- CARACTERÍSTICAS -->\n'
        f'<div style="background:#ffffff;padding:24px 28px;margin-top:2px;">\n'
        f'  <p style="font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#90263A;margin-bottom:18px;">Detalles de la prenda</p>\n'
        f'  <table style="width:100%;border-collapse:collapse;">\n'
        f'{chr(10).join(filas)}\n'
        f'  </table>\n'
        f'</div>\n\n'
        f'<!-- CUIDADOS -->\n'
        f'<div style="background:#e9eae5;padding:20px 28px;margin-top:2px;display:flex;align-items:center;gap:16px;flex-wrap:wrap;">\n'
        f'  <span style="font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#90263A;flex-shrink:0;">Cuidados</span>\n'
        f'  <div style="display:flex;gap:8px;flex-wrap:wrap;">\n'
        f'    {chips_html}\n'
        f'  </div>\n'
        f'</div>\n'
        f'{img_section}\n\n'
        f'<!-- NOTA FINAL -->\n'
        f'<div style="background:#ffffff;padding:20px 28px 24px;margin-top:2px;border-bottom:3px solid #90263A;">\n'
        f'{ale_block}\n'
        f'{modelo_line}\n'
        f'  <p style="font-size:10px;color:#000;text-align:center;font-style:italic;margin:0;">Todas las medidas son aproximadas y lineales. No son de contorno.</p>'
        f'{pack_line}\n'
        f'</div>'
    )

# ── Procesar CSV ──────────────────────────────────────────────────────────────

def process():
    with open(INPUT_CSV, encoding='cp1252') as f:
        reader = csv.reader(f, delimiter=';')
        rows = list(reader)

    processed_slugs = set()
    results = []

    for i, row in enumerate(rows[1:], 1):
        if not row or not row[0]:
            continue

        slug = row[0]

        if slug not in IMAGE_MAP:
            continue  # jean-nascar1, jean-imola → sin cambios

        if slug in processed_slugs:
            continue  # filas de variantes sin descripción

        desc = row[20] if len(row) > 20 else ''
        if not desc:
            processed_slugs.add(slug)
            continue

        processed_slugs.add(slug)
        nombre = row[1] if len(row) > 1 else slug
        img_filename = IMAGE_MAP[slug]
        img_url = CDN_BASE + img_filename
        is_pack = slug in PACKS

        data = MANUAL_OVERRIDES.get(slug) or parse_description(desc)
        new_html = build_html(nombre, data, img_url, is_pack=is_pack)
        rows[i][20] = new_html

        results.append(f'OK  {slug} → {img_filename} | Ale={data["ale_talle"] or "?"} | modelo={data["modelo_talle"] or "?"}')

    # Escribir CSV de salida (mismo encoding que el original)
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=';', quoting=csv.QUOTE_ALL, lineterminator='\r\n')
    writer.writerows(rows)

    with open(OUTPUT_CSV, 'w', encoding='cp1252', errors='replace') as f:
        f.write(buf.getvalue())

    for r in results:
        print(r)
    print(f'\nTotal: {len(results)} productos procesados')
    print(f'Guardado en: {OUTPUT_CSV}')


if __name__ == '__main__':
    process()
