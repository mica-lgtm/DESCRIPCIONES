#!/usr/bin/env python3
"""
Actualiza las descripciones de básicos en el CSV de Tienda Nube.
Lee el CSV original (CP1252), limpia el HTML sucio y agrega las imágenes CloudFront.
"""

import csv
import re
import io

INPUT_CSV = '/root/.claude/uploads/f65578b5-cc43-5cfd-a6c9-166cbe2a0b7b/a13d47e5-tiendanube60149617817062078882564708647375716.csv'
OUTPUT_CSV = '/home/user/DESCRIPCIONES/simona/basicos-descripciones-actualizadas.csv'
CLOUDFRONT = 'https://d1a9qnv764bsoo.cloudfront.net/stores/601/496/rte'

# Mapeo slug -> nombre de imagen CloudFront
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

# Slugs que son packs (agregan la línea extra)
PACKS = {
    'pack-x-2-camisa-clasica',
    'pack-x-3-remeras-basicas-escote-en-v',
    'pack-x2-top-mina',
    'pack-x-3-musculosa-daily1',
    'pack-x-3-musculosa-abril1',
    'pack-x-3-remeras-basicas',
}


def strip_data_attrs(html):
    """Elimina atributos data-start, data-end, data-is-only-node, data-is-last-node de todos los tags."""
    html = re.sub(r'\s+data-start="\d+"', '', html)
    html = re.sub(r'\s+data-end="\d+"', '', html)
    html = re.sub(r'\s+data-is-only-node=""', '', html)
    html = re.sub(r'\s+data-is-last-node=""', '', html)
    return html


def extract_inner_content(html):
    """
    Si el HTML tiene wrapper ChatGPT (<div class="flex max-w-full..."> o <article ...>),
    extrae solo el contenido del div interior con class="markdown...".
    Si no tiene wrapper, devuelve el HTML tal cual.
    """
    # Buscar el div con class="markdown prose..."
    m = re.search(r'<div class="markdown[^"]*"[^>]*>(.*)</div>\s*</div>\s*</div>\s*</div>',
                  html, re.DOTALL)
    if m:
        return m.group(1).strip()
    return html


def remove_measurement_table(html):
    """Elimina la tabla de medidas."""
    html = re.sub(r'<table[^>]*>.*?</table>', '', html, flags=re.DOTALL)
    return html


def remove_footer_lines(html):
    """Elimina las líneas de footer que vamos a agregar nosotros."""
    html = re.sub(r'<p[^>]*>La modelo de la foto.*?</p>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<p[^>]*>TODAS LAS MEDIDAS.*?</p>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<p[^>]*>Todas las medidas.*?</p>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<p[^>]*>TODAS LAS PRENDAS.*?</p>', '', html, flags=re.DOTALL | re.IGNORECASE)
    return html


def remove_trailing_junk(html):
    """Elimina elementos residuales del wrapper ChatGPT que queden sueltos."""
    # Eliminar <ul> que quedaron sueltos (residuos del wrapper)
    html = re.sub(r'<ul[^>]*>\s*</ul>', '', html, flags=re.DOTALL)
    # Eliminar <li> sueltos vacíos
    html = re.sub(r'<li[^>]*>\s*</li>', '', html, flags=re.DOTALL)
    # Eliminar divs residuales
    html = re.sub(r'<div[^>]*>\s*&nbsp;\s*</div>', '', html, flags=re.DOTALL)
    # Eliminar múltiples &nbsp; párrafos consecutivos
    html = re.sub(r'(<p[^>]*>&nbsp;</p>\s*){2,}', '<p>&nbsp;</p>\n', html)
    # Limpiar espacios múltiples y líneas vacías
    html = re.sub(r'\n{3,}', '\n\n', html)
    html = html.strip()
    return html


def clean_description(html):
    """Pipeline completo de limpieza del HTML."""
    html = extract_inner_content(html)
    html = strip_data_attrs(html)
    html = remove_measurement_table(html)
    html = remove_footer_lines(html)
    html = remove_trailing_junk(html)
    return html


def build_description_for_camisa_clasica(color, image_filename, is_pack=False):
    """Construye la descripción limpia para camisa clásica desde cero (el HTML original es un desastre)."""
    if is_pack:
        title = 'PACK X2 CAMISAS CL&Aacute;SICAS DE VOILE &ndash; ELEGANCIA EN BLANCO Y NEGRO'
        incluye = '<p><strong>Incluye:</strong><br />1 camisa cl&aacute;sica blanca &ndash; 1 camisa cl&aacute;sica negra. Dos b&aacute;sicos esenciales para cualquier guardarropa.</p>\n'
    else:
        color_txt = color.upper()
        title = f'CAMISA CL&Aacute;SICA DE VOILE &ndash; {color_txt}'
        incluye = ''

    html = f'''<p><strong>{title}</strong></p>
<p>? <strong>Material:</strong> Confeccionada en voile 100% algod&oacute;n, una tela liviana y suave al tacto que ofrece m&aacute;xima frescura y comodidad.<br />? <strong>Dise&ntilde;o:</strong> Corte cl&aacute;sico y atemporal, con cuello camisero y botones al frente. Su calce relajado y fluido la convierte en una prenda vers&aacute;til y elegante.<br />? <strong>Estilo:</strong> Ideal para crear looks urbanos o m&aacute;s formales, seg&uacute;n c&oacute;mo la combines. Perfecta para usar con jeans, pantalones sastreros o faldas.</p>
{incluye}<p><strong>C&oacute;mo combinarla:</strong><br />Con jeans tiro alto y mules para un look casual con elegancia.<br />Abierta sobre un top o musculosa para sumar capas con onda.<br />Con pantalones de vestir o falda midi para una propuesta m&aacute;s formal.</p>
<p>&nbsp;</p>
<p><strong>Cuidados:</strong> Lavar a mano o a m&aacute;quina con agua fr&iacute;a. No usar blanqueadores. Secar colgada a la sombra. Planchar a baja temperatura.</p>'''
    return html


def add_image_and_footer(html, image_filename, is_pack=False):
    """Agrega el tag de imagen CloudFront y el footer al final de la descripción."""
    # Eliminar párrafos &nbsp; finales antes de la imagen
    html = re.sub(r'(\s*<p[^>]*>&nbsp;</p>)+\s*$', '', html).strip()
    img_url = f'{CLOUDFRONT}/{image_filename}'
    img_tag = f'<p><img src="{img_url}" alt="" width="1000" height="550" /></p>'
    footer = '<p>La modelo de la foto usa talle S, Ale usa talle L.</p>\n<p>TODAS LAS MEDIDAS SON LINEALES Y APROXIMADAS, NO SON DE CONTORNO.</p>'
    if is_pack:
        footer += '\n<p>TODAS LAS PRENDAS DEL PACK SON DEL MISMO TALLE SELECCIONADO.</p>'
    return f'{html}\n{img_tag}\n{footer}'


def process_csv():
    with open(INPUT_CSV, encoding='cp1252') as f:
        reader = csv.reader(f, delimiter=';')
        rows = list(reader)

    header = rows[0]
    print(f'Columnas: {len(header)}')
    print(f'Filas de datos: {len(rows) - 1}')

    updated_count = 0
    already_clean = []

    processed = set()  # slugs ya procesados (para no limpiar las filas vacías)

    for i, row in enumerate(rows[1:], 1):
        if not row or not row[0]:
            continue

        slug = row[0]

        if slug not in IMAGE_MAP:
            # No es un producto básico, mantener tal cual
            continue

        # Solo procesar la primera fila del slug (la que tiene la descripción)
        desc = row[20] if len(row) > 20 else ''

        if slug in processed:
            # Filas adicionales (variantes) - no tienen descripción, dejar vacías
            continue

        processed.add(slug)

        if not desc:
            print(f'  SKIP (sin descripción): {slug}')
            continue

        image_filename = IMAGE_MAP[slug]
        is_pack = slug in PACKS

        # Caso especial: camisa clásica (HTML completamente roto)
        if slug in ('camisa-clasica-negro', 'camisa-clasica-blanco'):
            color = 'NEGRO' if 'negro' in slug else 'BLANCO'
            clean_html = build_description_for_camisa_clasica(color, image_filename, is_pack=False)
        elif slug == 'pack-x-2-camisa-clasica':
            clean_html = build_description_for_camisa_clasica('', image_filename, is_pack=True)
        else:
            clean_html = clean_description(desc)

        final_html = add_image_and_footer(clean_html, image_filename, is_pack=is_pack)
        rows[i][20] = final_html
        updated_count += 1
        print(f'  OK: {slug} -> {image_filename}')

    print(f'\nTotal actualizados: {updated_count}')

    # Escribir CSV de salida
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_ALL, lineterminator='\r\n')
    writer.writerows(rows)
    csv_content = output.getvalue()

    with open(OUTPUT_CSV, 'w', encoding='cp1252', errors='replace') as f:
        f.write(csv_content)

    print(f'CSV guardado en: {OUTPUT_CSV}')


if __name__ == '__main__':
    process_csv()
