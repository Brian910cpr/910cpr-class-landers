from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Any, Iterable

from .models import NormalizedCertification, SourceFile
from .normalize import (
    assign_fingerprints,
    canonical_header,
    clean_text,
    normalize_course,
    normalize_ecard,
    normalize_email,
    parse_date,
    split_name,
)

SUPPORTED_EXTENSIONS = {".csv", ".xls", ".xlsx", ".xlsb", ".ods"}


def _rows_from_csv(path: Path) -> Iterable[tuple[str, list[list[Any]]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    yield path.stem, rows


def _rows_from_workbook(path: Path) -> Iterable[tuple[str, list[list[Any]]]]:
    try:
        from python_calamine import CalamineWorkbook
    except ImportError as exc:
        raise RuntimeError(
            "python-calamine is required for XLS/XLSX/ODS parsing; install requirements.txt"
        ) from exc
    workbook = CalamineWorkbook.from_path(str(path))
    for sheet_name in workbook.sheet_names:
        sheet = workbook.get_sheet_by_name(sheet_name)
        yield sheet_name, sheet.to_python(skip_empty_area=True)


def workbook_rows(path: Path) -> Iterable[tuple[str, list[list[Any]]]]:
    if path.suffix.casefold() == ".csv":
        yield from _rows_from_csv(path)
    else:
        yield from _rows_from_workbook(path)


def _header_row(rows: list[list[Any]]) -> tuple[int, dict[str, int]]:
    best: tuple[int, dict[str, int]] | None = None
    for index, row in enumerate(rows[:25]):
        mapped: dict[str, int] = {}
        for col, value in enumerate(row):
            canonical = canonical_header(value)
            if canonical in {
                "ecard_code", "first_name", "last_name", "full_name", "email",
                "course", "class_date", "issue_date", "expiration_date",
                "corporate_customer",
            }:
                mapped.setdefault(canonical, col)
        score = len(mapped) + (2 if "ecard_code" in mapped else 0)
        if best is None or score > len(best[1]) + (2 if "ecard_code" in best[1] else 0):
            best = (index, mapped)
    if best is None or len(best[1]) < 2:
        raise ValueError("no_recognizable_header_row")
    return best


def _value(row: list[Any], mapping: dict[str, int], key: str) -> Any:
    index = mapping.get(key)
    return row[index] if index is not None and index < len(row) else None


def parse_file(source: SourceFile, path: Path) -> tuple[list[NormalizedCertification], list[str]]:
    sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    records: list[NormalizedCertification] = []
    errors: list[str] = []
    for sheet_name, rows in workbook_rows(path):
        if not rows:
            errors.append(f"{sheet_name}:empty_sheet")
            continue
        try:
            header_index, mapping = _header_row(rows)
        except ValueError as exc:
            errors.append(f"{sheet_name}:{exc}")
            continue
        headers = [clean_text(value) for value in rows[header_index]]
        for source_row, row in enumerate(rows[header_index + 1 :], start=header_index + 2):
            if not any(clean_text(value) for value in row):
                continue
            raw = {
                headers[index] if index < len(headers) and headers[index] else f"column_{index + 1}":
                    clean_text(value)
                for index, value in enumerate(row)
                if clean_text(value)
            }
            first, last, normalized_name, name_raw = split_name(
                _value(row, mapping, "first_name"),
                _value(row, mapping, "last_name"),
                _value(row, mapping, "full_name"),
            )
            ecard_code, ecard_error = normalize_ecard(_value(row, mapping, "ecard_code"))
            class_date, class_error = parse_date(_value(row, mapping, "class_date"))
            issue_date, issue_error = parse_date(_value(row, mapping, "issue_date"))
            expiration_date, expiration_error = parse_date(
                _value(row, mapping, "expiration_date")
            )
            validation_errors = [
                error
                for error in (ecard_error, class_error, issue_error, expiration_error)
                if error
            ]
            if not normalized_name:
                validation_errors.append("missing_participant_name")
            record_category = "certification"
            if not ecard_code and expiration_date and normalized_name:
                record_category = "historical_expiration_reference"
                validation_errors = [
                    error for error in validation_errors
                    if error != "missing_ecard_code"
                ]
            record = NormalizedCertification(
                source_file_id=source.id,
                source_file_name=source.name,
                source_file_modified_at=source.modified_at,
                source_file_sha256=sha256,
                source_sheet=sheet_name,
                source_row=source_row,
                participant_name_raw=name_raw,
                first_name=first,
                last_name=last,
                normalized_name=normalized_name,
                email=normalize_email(_value(row, mapping, "email")),
                course_name_raw=clean_text(_value(row, mapping, "course")),
                normalized_course=normalize_course(_value(row, mapping, "course")),
                ecard_code=ecard_code,
                class_date=class_date,
                issue_date=issue_date,
                expiration_date=expiration_date,
                corporate_customer=clean_text(
                    _value(row, mapping, "corporate_customer")
                ) or None,
                raw_record=raw,
                record_category=record_category,
                validation_errors=validation_errors,
            )
            assign_fingerprints(record)
            records.append(record)
    return records, errors
