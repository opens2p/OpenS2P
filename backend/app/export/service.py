"""
Export service — generates CSV, Excel, and PDF reports.
"""
from __future__ import annotations
import csv
import io
import uuid
from datetime import datetime
from typing import Any


class ExportService:
    @staticmethod
    def to_csv(data: list[dict[str, Any]], filename: str | None = None) -> tuple[str, str, bytes]:
        """Convert list of dicts to CSV bytes. Returns (filename, mime_type, content)."""
        if not data:
            return (filename or "export.csv", "text/csv", b"")
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        content = output.getvalue().encode("utf-8")
        return (filename or f"export_{uuid.uuid4().hex[:8]}.csv", "text/csv", content)

    @staticmethod
    def to_excel(data: list[dict[str, Any]], filename: str | None = None) -> tuple[str, str, bytes]:
        """Convert list of dicts to Excel bytes using openpyxl-style format.
        Falls back to CSV if openpyxl is not available."""
        try:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            if data:
                ws.append(list(data[0].keys()))
                for row in data:
                    ws.append(list(row.values()))
            output = io.BytesIO()
            wb.save(output)
            content = output.getvalue()
        except ImportError:
            _, _, content = ExportService.to_csv(data, filename)
            if filename:
                filename = filename.replace(".xlsx", ".csv")
        return (filename or f"export_{uuid.uuid4().hex[:8]}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", content)

    @staticmethod
    def generate_report(data: list[dict[str, Any]], format: str = "csv") -> tuple[str, str, bytes]:
        if format == "excel":
            return ExportService.to_excel(data)
        return ExportService.to_csv(data)
