"""
Pytest fixtures: generate minimal in-memory fixture files so tests run
without requiring the full synthetic dataset to be present.
"""
from __future__ import annotations

import io
from pathlib import Path

import openpyxl
import pytest
from PIL import Image, ImageDraw


@pytest.fixture(scope="session")
def fixtures_dir(tmp_path_factory) -> Path:
    d = tmp_path_factory.mktemp("fixtures")
    return d


@pytest.fixture(scope="session")
def sample_pdf(fixtures_dir: Path) -> Path:
    """Minimal 2-page PDF with known equipment tags."""
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    path = fixtures_dir / "sample.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Compressor-C1 OEM Manual", styles["Title"]),
        Paragraph(
            "Maximum Operating Pressure for Compressor-C1 is 150 psi. "
            "Inspection interval for Valve-V12 is every 3 months.",
            styles["BodyText"],
        ),
        Spacer(1, 12),
        Paragraph(
            "Pump-P3 emergency cooldown: 15 minutes minimum before access.",
            styles["BodyText"],
        ),
    ]
    doc.build(story)
    return path


@pytest.fixture(scope="session")
def sample_xlsx(fixtures_dir: Path) -> Path:
    """Minimal Excel workbook with 3 data rows."""
    path = fixtures_dir / "sample.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["work_order_id", "equipment_tag", "date", "technician", "finding", "action_taken"])
    ws.append(["WO-001", "Compressor-C1", "2025-01-15", "Alice", "Routine check", "No action"])
    ws.append(["WO-002", "Valve-V12",     "2025-02-10", "Bob",   "Packing weep",  "Re-torqued gland"])
    ws.append(["WO-003", "Pump-P3",       "2025-03-20", "Alice", "Normal",        "No action"])
    wb.save(str(path))
    return path


@pytest.fixture(scope="session")
def sample_png(fixtures_dir: Path) -> Path:
    """Minimal PNG with printed text (for OCR fixture)."""
    path = fixtures_dir / "sample.png"
    img = Image.new("L", (600, 200), color=255)
    draw = ImageDraw.Draw(img)
    draw.text((20, 20), "Inspection Report", fill=0)
    draw.text((20, 50), "Equipment Tag: Compressor-C1", fill=0)
    draw.text((20, 80), "Max Pressure: 150 psi", fill=0)
    img.save(str(path))
    return path


@pytest.fixture(scope="session")
def sample_txt(fixtures_dir: Path) -> Path:
    """Plain-text incident report."""
    path = fixtures_dir / "incident_report_test.txt"
    path.write_text(
        "INCIDENT REPORT\nEquipment Tag: Pump-P3\nSeverity: HIGH\n"
        "Description: Bearing temperature exceeded 230 deg F on Pump-P3.\n",
        encoding="utf-8",
    )
    return path
