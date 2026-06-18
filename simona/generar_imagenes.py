import re
import os
import asyncio
from playwright.async_api import async_playwright
from PIL import Image

MD_PATH = "Nuevas/CAMISAS-BLUSAS-NUEVAS.md"
OUTPUT_DIR = "Imagenes"
SVG_REF_PATH = "referencia-talles.svg"

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

# ── Carga y prepara el SVG de referencia ─────────────────────────────────────

def load_reference_svg(svg_path):
    with open(svg_path, "r", encoding="utf-8") as f:
        content = f.read()
    # Hacer el SVG responsivo reemplazando width/height fijos por los del viewBox
    content = re.sub(r'\bwidth="[^"]*"', 'width="280"', content, count=1)
    content = re.sub(r'\bheight="[^"]*"', 'height="350"', content, count=1)
    return content

# ── Generador de HTML ────────────────────────────────────────────────────────

def build_html(product_name, headers, rows, reference_svg):
    table_rows_html = ""
    for row in rows:
        cells = "".join(f"<td>{cell}</td>" for cell in row)
        table_rows_html += f"<tr>{cells}</tr>\n"

    header_cells = "".join(f"<th>{h}</th>" for h in headers)

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
    {reference_svg}
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

async def generate_images(products, output_dir, reference_svg):
    os.makedirs(output_dir, exist_ok=True)

    # device_scale_factor = 300/72 ≈ 4.167 para renderizar a 300 PPI
    scale = 300 / 72

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(
            viewport={"width": 1400, "height": 720},
            device_scale_factor=scale,
        )

        for name, data in products.items():
            html = build_html(name, data["headers"], data["rows"], reference_svg)

            await page.set_content(html, wait_until="networkidle")

            slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
            output_path = os.path.join(output_dir, f"{slug}.png")

            await page.screenshot(path=output_path, full_page=False)

            # Establecer metadato DPI = 300 en el PNG
            img = Image.open(output_path)
            img.save(output_path, dpi=(300, 300))

            print(f"  ✓ {name}  →  {output_path}")

        await browser.close()

# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    md_path = os.path.join(base_dir, MD_PATH)
    output_dir = os.path.join(base_dir, OUTPUT_DIR)
    svg_path = os.path.join(base_dir, SVG_REF_PATH)

    print("📖 Leyendo archivo de medidas...")
    products = parse_markdown(md_path)
    print(f"   {len(products)} productos encontrados\n")

    print("🖼️  Cargando SVG de referencia...")
    reference_svg = load_reference_svg(svg_path)

    print("🖼️  Generando imágenes...")
    asyncio.run(generate_images(products, output_dir, reference_svg))

    print(f"\n✅ Listo. Imágenes guardadas en: {output_dir}/")
