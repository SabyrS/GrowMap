from pathlib import Path

pages = [
    (
        "GrowMap",
        [
            "Personal assistant for planning and analyzing plantings",
            "Garden and balcony focus",
            "Interactive maps, weather advice, analytics",
        ],
    ),
    (
        "Problem and goal",
        [
            "Keep track of plantings and care in one place",
            "Avoid mistakes with weather-based advice",
            "Analyze watering and harvest efficiency",
        ],
    ),
    (
        "Level 1 (mandatory)",
        [
            "Auth: register/login, private maps and plants",
            "Interactive 2D map (SVG) with object info",
            "Plant catalog with requirements",
            "Weather API recommendations (not raw data)",
            "Single analytics page (charts + summary)",
        ],
    ),
    (
        "Level 2 (bonus)",
        [
            "Plant compatibility warnings when nearby",
            "Harvest logging with efficiency vs average",
            "Action history: watering, planting, harvest",
        ],
    ),
    (
        "Level 3 (optional)",
        [
            "LLM explanations only (no calculations)",
            "Not used in current implementation",
            "Rule-based insights are primary",
        ],
    ),
    (
        "Tech and demo flow",
        [
            "Flask + SQLite + SVG + Chart.js",
            "Create map -> add plants -> log actions",
            "Weather advice -> analytics charts",
            "Result: clear plan and accountability",
        ],
    ),
]

WIDTH, HEIGHT = 792, 612
FONT_OBJ_NUM = 100


def pdf_text_lines(title, lines):
    content = ["BT", "/F1 36 Tf", "50 540 Td", f"({title}) Tj", "ET"]
    y = 490
    for line in lines:
        safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        content += ["BT", "/F1 20 Tf", f"50 {y} Td", f"({safe}) Tj", "ET"]
        y -= 32
    return "\n".join(content)


def build_pdf(path):
    objects = []

    page_obj_nums = []
    content_obj_nums = []
    current_obj = 3
    for _ in pages:
        page_obj_nums.append(current_obj)
        content_obj_nums.append(current_obj + 1)
        current_obj += 2

    for idx, (title, lines) in enumerate(pages):
        content = pdf_text_lines(title, lines)
        content_bytes = content.encode("utf-8")
        content_obj = (
            f"{content_obj_nums[idx]} 0 obj\n"
            f"<< /Length {len(content_bytes)} >>\n"
            "stream\n"
            f"{content}\n"
            "endstream\n"
            "endobj\n"
        )
        page_obj = (
            f"{page_obj_nums[idx]} 0 obj\n"
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {WIDTH} {HEIGHT}] "
            f"/Resources << /Font << /F1 {FONT_OBJ_NUM} 0 R >> >> "
            f"/Contents {content_obj_nums[idx]} 0 R >>\n"
            "endobj\n"
        )
        objects.append(page_obj)
        objects.append(content_obj)

    catalog_obj = "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    kids = " ".join([f"{n} 0 R" for n in page_obj_nums])
    pages_obj = (
        f"2 0 obj\n<< /Type /Pages /Kids [{kids}] /Count {len(page_obj_nums)} >>\nendobj\n"
    )
    font_obj = (
        f"{FONT_OBJ_NUM} 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
    )

    all_objects = [catalog_obj, pages_obj] + objects + [font_obj]

    xref_offsets = []
    output = ["%PDF-1.4\n"]
    for obj in all_objects:
        xref_offsets.append(sum(len(part) for part in output))
        output.append(obj)

    xref_start = sum(len(part) for part in output)

    xref = ["xref\n", f"0 {len(all_objects)+1}\n", "0000000000 65535 f \n"]
    for off in xref_offsets:
        xref.append(f"{off:010d} 00000 n \n")

    trailer = (
        "trailer\n"
        f"<< /Size {len(all_objects)+1} /Root 1 0 R >>\n"
        "startxref\n"
        f"{xref_start}\n"
        "%%EOF\n"
    )

    pdf_data = "".join(output) + "".join(xref) + trailer
    Path(path).write_bytes(pdf_data.encode("latin1"))


if __name__ == "__main__":
    build_pdf("docs/Presentation.pdf")
