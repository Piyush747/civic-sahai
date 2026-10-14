from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "data-model.md"
OUTPUT = ROOT / "docs" / "civic-sahai-data-model.pdf"
PAGE_WIDTH, PAGE_HEIGHT = 595, 842
LEFT, TOP, BOTTOM = 54, 790, 54


def clean(value: str) -> str:
    value = value.replace("->", "to").replace("–", "-").replace("—", "-")
    return value.encode("latin-1", "replace").decode("latin-1")


def wrap(text: str, width: int = 92) -> list[str]:
    words = clean(text).split()
    lines, current = [], ""
    for word in words:
        if len(current) + len(word) + 1 > width and current:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        lines.append(current)
    return lines or [""]


def parse_lines(markdown: str) -> list[tuple[str, str]]:
    result = []
    in_table = False
    for raw in markdown.splitlines():
        line = raw.strip()
        if not line:
            result.append(("space", ""))
        elif line.startswith("### "):
            result.append(("h3", line[4:]))
        elif line.startswith("## "):
            result.append(("h2", line[3:]))
        elif line.startswith("# "):
            result.append(("h1", line[2:]))
        elif line.startswith("|---") or line.startswith("| ---"):
            in_table = True
        elif line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            result.append(("table", "  |  ".join(cells)))
        elif line.startswith("- "):
            result.append(("bullet", line[2:]))
        elif re.match(r"^\d+\. ", line):
            result.append(("bullet", line))
        else:
            result.append(("body", line))
    return result


def pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def make_pdf(lines: list[tuple[str, str]]) -> bytes:
    pages: list[list[str]] = [[]]
    y = TOP
    for kind, text in lines:
        size = {"h1": 22, "h2": 16, "h3": 12, "body": 9, "bullet": 9, "table": 8, "space": 5}[kind]
        leading = {"h1": 30, "h2": 23, "h3": 18, "body": 13, "bullet": 13, "table": 12, "space": 8}[kind]
        chunks = [""] if kind == "space" else wrap(text, 88 if kind != "table" else 86)
        for chunk in chunks:
            if y - leading < BOTTOM:
                pages.append([])
                y = TOP
            if kind == "bullet":
                chunk = "- " + chunk
            font = "F2" if kind in {"h1", "h2", "h3"} else "F1"
            pages[-1].append(f"BT /{font} {size} Tf {LEFT} {y} Td ({pdf_escape(chunk)}) Tj ET")
            y -= leading
        if kind in {"h1", "h2", "h3"}:
            y -= 4

    objects: list[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    page_refs = " ".join(f"{5 + i * 2} 0 R" for i in range(len(pages)))
    objects.append(f"<< /Type /Pages /Kids [{page_refs}] /Count {len(pages)} >>".encode())
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
    for index, commands in enumerate(pages):
        stream = "\n".join(commands).encode("latin-1", "replace")
        page_number = 5 + index * 2
        content_number = page_number + 1
        objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {content_number} 0 R >>".encode())
        objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream")
    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode())
        output.extend(obj)
        output.extend(b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return bytes(output)


OUTPUT.write_bytes(make_pdf(parse_lines(SOURCE.read_text())))
print(OUTPUT)
