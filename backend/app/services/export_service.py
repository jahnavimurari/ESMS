import csv
import io
import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class ExportFormatter:
    """Utilities for generating sanitized CSV, Excel, and PDF reports."""

    @staticmethod
    def _sanitize_cell(value):
        """Sanitizes strings to prevent formula injection (=, +, -, @, tab, CR in CSV/Excel)."""
        if value is None:
            return ""
        if isinstance(value, (int, float, Decimal)):
            return value
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        
        s = str(value)
        # Check formula injection characters
        if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
            return "'" + s
        return s

    @classmethod
    def to_csv(cls, headers, rows):
        """Generates a clean CSV file in-memory preventing formula injection."""
        output = io.StringIO()
        # Add UTF-8 BOM so Excel opens CSVs with proper unicode encoding
        output.write("\ufeff")
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(headers)
        for row in rows:
            writer.writerow([cls._sanitize_cell(cell) for cell in row])
        return output.getvalue().encode("utf-8")

    @classmethod
    def to_excel(cls, title, headers, rows, filter_summary=None):
        """Generates an openpyxl Excel (.xlsx) file in-memory with professional styling."""
        wb = Workbook()
        ws = wb.active
        ws.title = title[:31]  # Excel sheet title limit is 31 chars

        # Styles
        title_font = Font(name="Calibri", size=14, bold=True, color="1E3A8A")
        meta_font = Font(name="Calibri", size=9, italic=True, color="6B7280")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        cell_font = Font(name="Calibri", size=10)
        thin_border = Border(
            left=Side(style="thin", color="E5E7EB"),
            right=Side(style="thin", color="E5E7EB"),
            top=Side(style="thin", color="E5E7EB"),
            bottom=Side(style="thin", color="E5E7EB"),
        )

        curr_row = 1
        # Title
        ws.cell(row=curr_row, column=1, value=f"ESMS – {title}").font = title_font
        curr_row += 1

        # Metadata / Generation Date
        gen_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        ws.cell(row=curr_row, column=1, value=f"Generated on: {gen_time}").font = meta_font
        curr_row += 1

        if filter_summary:
            ws.cell(row=curr_row, column=1, value=f"Applied Filters: {filter_summary}").font = meta_font
            curr_row += 1

        curr_row += 1  # Blank line

        # Headers
        for col_idx, header in enumerate(headers, 1):
            c = ws.cell(row=curr_row, column=col_idx, value=header)
            c.font = header_font
            c.fill = header_fill
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            c.border = thin_border
        curr_row += 1

        # Data rows
        for row_data in rows:
            for col_idx, cell_value in enumerate(row_data, 1):
                sanitized = cls._sanitize_cell(cell_value)
                c = ws.cell(row=curr_row, column=col_idx, value=sanitized)
                c.font = cell_font
                c.border = thin_border
                if isinstance(sanitized, (int, float, Decimal)):
                    c.alignment = Alignment(horizontal="right")
                elif isinstance(sanitized, (datetime, date)):
                    c.alignment = Alignment(horizontal="center")
                else:
                    c.alignment = Alignment(horizontal="left")
            curr_row += 1

        # Auto-adjust column widths
        for col in ws.columns:
            max_len = 0
            col_letter = col[0].column_letter
            for cell in col:
                val = str(cell.value or "")
                if len(val) > max_len:
                    max_len = len(val)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()

    @classmethod
    def to_pdf(cls, title, headers, rows, filter_summary=None):
        """Generates a PDF document in-memory using ReportLab."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#1e3a8a"),
            spaceAfter=4
        )
        meta_style = ParagraphStyle(
            "ReportMeta",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#6b7280"),
            spaceAfter=2
        )
        cell_style = ParagraphStyle(
            "ReportCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#1f2937")
        )
        header_style = ParagraphStyle(
            "ReportHeaderCell",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.white
        )

        elements = []
        elements.append(Paragraph(f"ESMS – {title}", title_style))
        gen_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        elements.append(Paragraph(f"Generated: {gen_time} | Scope: Confidential Enterprise Report", meta_style))
        if filter_summary:
            elements.append(Paragraph(f"Filters: {filter_summary}", meta_style))
        elements.append(Spacer(1, 10))

        # Build table data
        table_data = []
        table_data.append([Paragraph(str(h), header_style) for h in headers])

        if not rows:
            # Empty state row
            empty_msg = [Paragraph("No records found matching specified filters.", cell_style)] + [Paragraph("", cell_style)] * (len(headers) - 1)
            table_data.append(empty_msg)
        else:
            for r in rows:
                row_cells = []
                for cell in r:
                    val_str = "" if cell is None else str(cell)
                    row_cells.append(Paragraph(val_str, cell_style))
                table_data.append(row_cells)

        t = Table(table_data, repeatRows=1)
        t_style = TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
        t.setStyle(t_style)
        elements.append(t)

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

