import csv
import os
import re

CDN_BASE = "https://d1a9qnv764bsoo.cloudfront.net/stores/601/496/rte/"
IMG_DIR = "/Users/mica/Desktop/simona/Imagenes"
INPUT_CSV = "/Users/mica/Downloads/tiendanube-601496-17810278847031402453559643188.csv"
OUTPUT_CSV = "/Users/mica/Downloads/tiendanube-601496-con-imagenes.csv"

# Imágenes disponibles: base_name -> filename
images = {os.path.splitext(f)[0]: f for f in os.listdir(IMG_DIR) if f.endswith('.png')}

# Mapeo manual para casos con nombre de URL distinto al de la imagen
MANUAL_MAPPING = {
    'camisa-cumbre-beige-1bcqp': 'camisa-cumbre-chocolate-con-leche.png',
}

# Regex para detectar tablas exportadas de Google Sheets (tienen data-sheets-root)
TABLE_PATTERN = re.compile(
    r'<table[^>]*data-sheets-root[^>]*>.*?</table>',
    re.DOTALL | re.IGNORECASE
)

def find_image(product_id):
    if product_id in MANUAL_MAPPING:
        return MANUAL_MAPPING[product_id]
    if product_id in images:
        return images[product_id]
    parts = product_id.rsplit('-', 1)
    if len(parts) == 2 and parts[0] in images:
        return images[parts[0]]
    return None

def make_img_html(filename):
    url = CDN_BASE + filename
    return f'<p><img src="{url}" alt="" width="300" height="156" /></p>'

matched = []
unmatched = []
tables_replaced = 0

with open(INPUT_CSV, 'r', encoding='latin-1', newline='') as infile, \
     open(OUTPUT_CSV, 'w', encoding='latin-1', newline='') as outfile:

    reader = csv.reader(infile, delimiter=';', quotechar='"')
    writer = csv.writer(outfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    for i, row in enumerate(reader):
        if i == 0:
            writer.writerow(row)
            continue

        product_id = row[0].strip()
        nombre = row[1].strip() if len(row) > 1 else ''
        descripcion_idx = 20

        # Solo modificar filas con nombre (fila principal del producto)
        if nombre and product_id and len(row) > descripcion_idx:
            img_file = find_image(product_id)
            if img_file:
                img_html = make_img_html(img_file)
                desc = row[descripcion_idx]
                new_desc, n = TABLE_PATTERN.subn(img_html, desc)
                row[descripcion_idx] = new_desc
                tables_replaced += n
                matched.append(f"  ✓ {product_id} → {img_file} ({n} tabla/s reemplazada/s)")
            else:
                unmatched.append(f"  ✗ {product_id} (sin imagen)")

        writer.writerow(row)

print(f"\n{'='*50}")
print(f"CSV generado: {OUTPUT_CSV}")
print(f"\nProductos con imagen ({len(matched)}):")
for m in matched:
    print(m)
if unmatched:
    print(f"\nProductos SIN imagen ({len(unmatched)}):")
    for u in unmatched:
        print(u)
print(f"\nTotal tablas reemplazadas: {tables_replaced}")
print(f"Total productos procesados: {len(matched) + len(unmatched)}")
