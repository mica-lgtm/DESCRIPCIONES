# Instrucciones: Generador de Imágenes de Medidas

## Objetivo
Leer el archivo `Nuevas/CAMISAS-BLUSAS-NUEVAS.md` y generar una imagen por cada producto, con el estilo de la guía de talles de Simona (ilustración de prenda a la izquierda + tabla de medidas a la derecha). Guardar todas las imágenes en la carpeta `Imagenes/`.

---

## Diseño de referencia

- **Fondo general:** beige cálido `#f5efe8`
- **Card izquierda:** blanco `#ffffff`, bordes redondeados, sombra suave — contiene ilustración de la prenda con flechas de medidas
- **Título:** derecha arriba, fuente serif grande, color oscuro `#1a1a1a`
- **Tabla:** derecha abajo, encabezado con fondo rosa `#e8c4b8`, filas blancas con separadores, esquinas redondeadas
- **Flechas de medidas en ilustración:** línea punteada color rosa `#c4726a`, con etiquetas en la misma tipografía

---

## Paso 1 — Instalar dependencias

```bash
pip install playwright pillow
playwright install chromium
```

---

## Paso 2 — Script Python

Crear el archivo `generar_imagenes.py` en la raíz del proyecto (`/Users/mica/Desktop/simona/`) con el siguiente contenido:

```python
import re
import os
import asyncio
from playwright.async_api import async_playwright

MD_PATH = "Nuevas/CAMISAS-BLUSAS-NUEVAS.md"
OUTPUT_DIR = "Imagenes"

# ── Parser del markdown ──────────────────────────────────────────────────────

def parse_markdown(md_path):
    products = {}
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    sections = re.split(r"^## (.+)$", content, flags=re.MULTILINE)
    i = 1
    while i < len(sections) - 1:
        name = sections[i].strip()
        body = sections[i + 1].strip()
        lines = [l for l in body.split("\n") if l.startswith("|")]
        if len(lines) >= 3:
            headers = [h.strip() for h in lines[0].split("|")[1:-1]]
            rows = []
            for line in lines[2:]:
                row = [c.strip() for c in line.split("|")[1:-1]]
                if any(row):
                    rows.append(row)
            products[name] = {"headers": headers, "rows": rows}
        i += 2
    return products

# ── SVG de la prenda con flechas dinámicas ───────────────────────────────────

def build_illustration_svg(headers):
    """
    Genera SVG de ilustración de prenda con las flechas que correspondan
    según los encabezados presentes en la tabla (HOMBROS, SISA, LARGO, BUSTO, etc.)
    """
    cols = [h.upper() for h in headers[1:]]  # saltar columna MEDIDAS

    arrow_color = "#c4726a"
    label_style = f'font-family: Georgia, serif; font-size: 13px; fill: {arrow_color};'

    # Ilustración base de blusa/camisa (path SVG)
    shirt_path = """
      M 95,45 C 110,20 170,20 185,45
      L 235,85 L 210,100 L 205,300 L 75,300 L 70,100 L 45,85 Z
    """
    # Cuello
    collar_path = "M 95,45 C 120,75 160,75 185,45"
    # Costura manga izquierda
    sleeve_l = "M 45,85 L 70,100"
    # Costura manga derecha
    sleeve_r = "M 235,85 L 210,100"

    arrows = []

    # HOMBROS — flecha horizontal en la parte superior del hombro
    if "HOMBROS" in cols:
        arrows.append(f"""
          <!-- HOMBROS -->
          <line x1="50" y1="72" x2="230" y2="72"
                stroke="{arrow_color}" stroke-width="1.5" stroke-dasharray="5,3"
                marker-start="url(#arrow)" marker-end="url(#arrow)"/>
          <text x="140" y="64" text-anchor="middle" style="{label_style}">Hombros</text>
        """)

    # SISA — flecha horizontal a la altura del pecho/sisa
    if "SISA" in cols:
        y_sisa = 140 if "HOMBROS" in cols else 120
        arrows.append(f"""
          <!-- SISA -->
          <line x1="73" y1="{y_sisa}" x2="207" y2="{y_sisa}"
                stroke="{arrow_color}" stroke-width="1.5" stroke-dasharray="5,3"
                marker-start="url(#arrow)" marker-end="url(#arrow)"/>
          <text x="140" y="{y_sisa - 8}" text-anchor="middle" style="{label_style}">Sisa</text>
        """)

    # BUSTO — flecha horizontal en zona de busto
    if "BUSTO" in cols:
        arrows.append(f"""
          <!-- BUSTO -->
          <line x1="73" y1="160" x2="207" y2="160"
                stroke="{arrow_color}" stroke-width="1.5" stroke-dasharray="5,3"
                marker-start="url(#arrow)" marker-end="url(#arrow)"/>
          <text x="140" y="152" text-anchor="middle" style="{label_style}">Busto</text>
        """)

    # CINTURA — flecha horizontal
    if "CINTURA" in cols:
        arrows.append(f"""
          <!-- CINTURA -->
          <line x1="78" y1="200" x2="202" y2="200"
                stroke="{arrow_color}" stroke-width="1.5" stroke-dasharray="5,3"
                marker-start="url(#arrow)" marker-end="url(#arrow)"/>
          <text x="140" y="192" text-anchor="middle" style="{label_style}">Cintura</text>
        """)

    # CADERA — flecha horizontal
    if "CADERA" in cols:
        arrows.append(f"""
          <!-- CADERA -->
          <line x1="80" y1="240" x2="200" y2="240"
                stroke="{arrow_color}" stroke-width="1.5" stroke-dasharray="5,3"
                marker-start="url(#arrow)" marker-end="url(#arrow)"/>
          <text x="140" y="232" text-anchor="middle" style="{label_style}">Cadera</text>
        """)

    # LARGO — flecha vertical
    if "LARGO" in cols:
        arrows.append(f"""
          <!-- LARGO -->
          <line x1="38" y1="100" x2="38" y2="295"
                stroke="{arrow_color}" stroke-width="1.5" stroke-dasharray="5,3"
                marker-start="url(#arrow)" marker-end="url(#arrow)"/>
          <text x="28" y="200" text-anchor="middle"
                transform="rotate(-90, 28, 200)"
                style="{label_style}">Largo</text>
        """)

    return f"""
    <svg width="280" height="360" viewBox="0 0 280 360"
         fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <marker id="arrow" markerWidth="6" markerHeight="6"
                refX="3" refY="3" orient="auto">
          <path d="M0,0 L0,6 L6,3 Z" fill="{arrow_color}"/>
        </marker>
      </defs>

      <!-- Prenda -->
      <path d="{shirt_path}" stroke="#2d2d2d" stroke-width="2" fill="white" stroke-linejoin="round"/>
      <path d="{collar_path}" stroke="#2d2d2d" stroke-width="1.5" fill="none"/>
      <line x1="45" y1="85" x2="70" y2="100" stroke="#2d2d2d" stroke-width="1.5"/>
      <line x1="235" y1="85" x2="210" y2="100" stroke="#2d2d2d" stroke-width="1.5"/>

      {"".join(arrows)}
    </svg>
    """

# ── Generador de HTML ────────────────────────────────────────────────────────

def build_html(product_name, headers, rows):
    # Filas de la tabla
    table_rows_html = ""
    for row in rows:
        cells = "".join(f"<td>{cell}</td>" for cell in row)
        table_rows_html += f"<tr>{cells}</tr>\n"

    # Encabezados de la tabla
    header_cells = "".join(f"<th>{h}</th>" for h in headers)

    illustration_svg = build_illustration_svg(headers)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: 1400px;
    height: 720px;
    background: #f5efe8;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 60px;
    padding: 50px 60px;
    font-family: Arial, sans-serif;
  }}

  /* ── Card izquierda ── */
  .card {{
    background: white;
    border-radius: 20px;
    padding: 40px 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 20px rgba(0,0,0,0.07);
    width: 340px;
    min-height: 440px;
    flex-shrink: 0;
  }}

  /* ── Lado derecho ── */
  .right {{
    display: flex;
    flex-direction: column;
    gap: 28px;
    flex: 1;
  }}

  .product-title {{
    font-family: Georgia, "Times New Roman", serif;
    font-size: 52px;
    font-weight: 400;
    color: #1a1a1a;
    line-height: 1.1;
  }}

  /* ── Tabla ── */
  table {{
    border-collapse: separate;
    border-spacing: 0;
    width: 100%;
    border-radius: 14px;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  }}

  th {{
    background: #e8c4b8;
    color: #1a1a1a;
    font-size: 16px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 16px 20px;
    text-align: center;
  }}

  td {{
    background: white;
    font-size: 17px;
    color: #2d2d2d;
    padding: 18px 20px;
    text-align: center;
    border-top: 1px solid #f0e8e3;
  }}

  tr:last-child td {{
    border-bottom: none;
  }}

  td:first-child {{
    font-weight: 600;
    text-align: left;
  }}
</style>
</head>
<body>
  <div class="card">
    {illustration_svg}
  </div>

  <div class="right">
    <h1 class="product-title">{product_name}</h1>
    <table>
      <thead><tr>{header_cells}</tr></thead>
      <tbody>{table_rows_html}</tbody>
    </table>
  </div>
</body>
</html>"""

# ── Generación de imágenes con Playwright ────────────────────────────────────

async def generate_images(products, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1400, "height": 720})

        for name, data in products.items():
            html = build_html(name, data["headers"], data["rows"])

            await page.set_content(html, wait_until="networkidle")

            # Nombre de archivo: slug del producto
            slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
            output_path = os.path.join(output_dir, f"{slug}.png")

            await page.screenshot(path=output_path, full_page=False)
            print(f"  ✓ {name}  →  {output_path}")

        await browser.close()

# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    md_path = os.path.join(base_dir, MD_PATH)
    output_dir = os.path.join(base_dir, OUTPUT_DIR)

    print("📖 Leyendo archivo de medidas...")
    products = parse_markdown(md_path)
    print(f"   {len(products)} productos encontrados\n")

    print("🖼️  Generando imágenes...")
    asyncio.run(generate_images(products, output_dir))

    print(f"\n✅ Listo. Imágenes guardadas en: {output_dir}/")
```

---

## Paso 3 — Ejecutar

Desde la carpeta `/Users/mica/Desktop/simona/`:

```bash
cd /Users/mica/Desktop/simona
python3 generar_imagenes.py
```

---

## Resultado esperado

Se genera **una imagen PNG por producto** en la carpeta `Imagenes/`, nombrada con el slug del producto:

```
Imagenes/
  camisa-vint-blanco.png
  camisa-vint-negro.png
  camisa-cultura-choco-y-beige.png
  ... (34 imágenes en total)
```

---

## Notas para el agente

- **Input:** `Nuevas/CAMISAS-BLUSAS-NUEVAS.md`
- **Output:** `Imagenes/*.png`
- La ilustración adapta automáticamente las flechas según las columnas de cada producto (si tiene HOMBROS, SISA, LARGO, BUSTO, CINTURA, CADERA).
- Si un producto tiene columnas distintas a las mencionadas, el agente debe agregar la lógica correspondiente en la función `build_illustration_svg()`.
- Si se quiere cambiar el diseño, modificar los estilos CSS dentro de `build_html()`.
