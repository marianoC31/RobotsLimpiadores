import os
import re

MD_PATH = os.path.join(os.path.dirname(__file__), "DOCUMENTO_ENTREGA_PARTE_1.md")
HTML_PATH = os.path.join(os.path.dirname(__file__), "DOCUMENTO_ENTREGA_PARTE_1.html")

def markdown_to_styled_html():
    with open(MD_PATH, 'r', encoding='utf-8') as f:
        md_text = f.read()

    # Estilos CSS profesionales con soporte de impresión y diagramas
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TC2008B - Evidencia 1: Parte 1 (Sistemas Multiagentes)</title>
    <!-- Marked.js para renderizar Markdown -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <!-- KaTeX para renderizar fórmulas matemáticas -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"></script>
    <!-- Mermaid.js para diagramas UML -->
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        @page {{
            size: A4;
            margin: 20mm;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: #1a202c;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            background-color: #f7fafc;
        }}
        .container {{
            background: #ffffff;
            padding: 45px 50px;
            border-radius: 8px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }}
        h1, h2, h3, h4 {{
            color: #2b6cb0;
            font-weight: 700;
        }}
        h1 {{
            font-size: 26px;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 12px;
            margin-bottom: 20px;
        }}
        h2 {{
            font-size: 21px;
            margin-top: 30px;
            border-bottom: 1px solid #edf2f7;
            padding-bottom: 8px;
        }}
        h3 {{ font-size: 17px; margin-top: 22px; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 13px;
        }}
        th, td {{
            border: 1px solid #cbd5e0;
            padding: 8px 12px;
            text-align: left;
        }}
        th {{
            background-color: #ebf8ff;
            color: #2c5282;
            font-weight: 600;
        }}
        tr:nth-child(even) {{
            background-color: #f7fafc;
        }}
        code {{
            background: #edf2f7;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 13px;
            color: #c53030;
        }}
        pre code {{
            background: none;
            color: inherit;
            padding: 0;
        }}
        pre {{
            background: #2d3748;
            color: #edf2f7;
            padding: 16px;
            border-radius: 6px;
            overflow-x: auto;
        }}
        blockquote {{
            border-left: 4px solid #3182ce;
            margin: 18px 0;
            padding: 10px 18px;
            background-color: #ebf8ff;
            color: #2c5282;
            font-style: italic;
        }}
        .mermaid {{
            text-align: center;
            margin: 25px 0;
        }}
        .print-btn {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #3182ce;
            color: white;
            padding: 10px 18px;
            border-radius: 6px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 4px 6px rgba(0,0,0,0.15);
            border: none;
            z-index: 1000;
        }}
        .print-btn:hover {{
            background: #2b6cb0;
        }}
        @media print {{
            .print-btn {{ display: none; }}
            body {{ background: white; padding: 0; }}
            .container {{ box-shadow: none; padding: 0; }}
        }}
    </style>
</head>
<body>
    <button class="print-btn" onclick="window.print()">🖨️ Guardar como PDF / Imprimir</button>
    <div class="container" id="content"></div>

    <script id="markdown-source" type="text/plain">
{md_text}
    </script>

    <script>
        document.addEventListener("DOMContentLoaded", function() {{
            const md = document.getElementById("markdown-source").textContent;
            document.getElementById("content").innerHTML = marked.parse(md);

            // Renderizar Mermaid
            mermaid.initialize({{ startOnLoad: true, theme: 'default' }});

            // Renderizar KaTeX
            renderMathInElement(document.getElementById("content"), {{
                delimiters: [
                    {{left: '$$', right: '$$', display: true}},
                    {{left: '$', right: '$', display: false}}
                ],
                throwOnError : false
            }});
        }});
    </script>
</body>
</html>
"""
    with open(HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✅ Documento interactivo para exportar a PDF generado en:\n   {HTML_PATH}")

if __name__ == "__main__":
    markdown_to_styled_html()

