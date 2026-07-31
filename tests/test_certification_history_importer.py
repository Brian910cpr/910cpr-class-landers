from __future__ import annotations

import csv
import tempfile
import unittest
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

from scripts.certification_import.matching import DeterministicMatcher
from scripts.certification_import.models import NormalizedCertification, SourceFile
from scripts.certification_import.normalize import (
    assign_fingerprints,
    normalize_ecard,
    parse_date,
)
from scripts.certification_import.parsers import parse_file
from scripts.certification_import.policy import (
    AHA_MONTH_END_POLICY,
    assess_certification,
    two_years_through_end_of_month,
)
from scripts.certification_import.reconcile import reconcile


def write_xlsx(path: Path, sheets: list[tuple[str, list[list[object]]]]) -> None:
    relationships = []
    workbook_sheets = []
    content_overrides = []
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for index, (name, rows) in enumerate(sheets, start=1):
            relationships.append(
                f'<Relationship Id="rId{index}" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
                f'Target="worksheets/sheet{index}.xml"/>'
            )
            workbook_sheets.append(
                f'<sheet name="{escape(name)}" sheetId="{index}" r:id="rId{index}"/>'
            )
            content_overrides.append(
                f'<Override PartName="/xl/worksheets/sheet{index}.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            )
            row_xml = []
            for row_number, row in enumerate(rows, start=1):
                cells = []
                for column, value in enumerate(row, start=1):
                    letters = ""
                    current = column
                    while current:
                        current, remainder = divmod(current - 1, 26)
                        letters = chr(65 + remainder) + letters
                    cells.append(
                        f'<c r="{letters}{row_number}" t="inlineStr"><is><t>'
                        f'{escape(str(value))}</t></is></c>'
                    )
                row_xml.append(f'<row r="{row_number}">{"".join(cells)}</row>')
            archive.writestr(
                f"xl/worksheets/sheet{index}.xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                f'<sheetData>{"".join(row_xml)}</sheetData></worksheet>',
            )
        archive.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            + "".join(content_overrides)
            + "</Types>",
        )
        archive.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
            'Target="xl/workbook.xml"/></Relationships>',
        )
        archive.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f'<sheets>{"".join(workbook_sheets)}</sheets></workbook>',
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            + "".join(relationships)
            + "</Relationships>",
        )


def source(path: Path, file_id: str = "file-1") -> SourceFile:
    return SourceFile(
        id=file_id,
        name=path.name,
        modified_at="2026-07-30T00:00:00Z",
        mime_type="application/octet-stream",
        size=path.stat().st_size,
    )


def certification(**overrides: object) -> NormalizedCertification:
    values = {
        "source_file_id": "file",
        "source_file_name": "invented.xlsx",
        "source_file_modified_at": "2026-07-30T00:00:00Z",
        "source_file_sha256": "a" * 64,
        "source_sheet": "Sheet1",
        "source_row": 2,
        "participant_name_raw": "Avery Sample",
        "first_name": "Avery",
        "last_name": "Sample",
        "normalized_name": "avery sample",
        "email": "avery@example.test",
        "course_name_raw": "AHA BLS",
        "normalized_course": "BLS",
        "ecard_code": "123456789012",
        "class_date": "2026-07-01",
        "issue_date": None,
        "source_expiration_date": "2028-07-31",
        "corporate_customer": None,
        "raw_record": {"eCard Code": "123456789012"},
    }
    values.update(overrides)
    record = NormalizedCertification(**values)
    assign_fingerprints(record)
    return record


def profile(
    profile_id: str = "profile-1", first: str = "Avery", last: str = "Sample",
    email: str = "avery@example.test", course: str = "BLS", **overrides: object,
) -> dict[str, object]:
    row: dict[str, object] = {
        "id": profile_id,
        "billing_account": "#031",
        "required_training": course,
        "workflow_stage": 3,
        "status_detail": "Awaiting eCard",
        "prior_class_date": None,
        "expiration_date": None,
        "prior_ecard_code": None,
        "scheduled_class_date": "2026-07-01T12:00:00Z",
        "customers": {"first_name": first, "last_name": last, "email": email},
    }
    row.update(overrides)
    return row


class ParserTests(unittest.TestCase):
    def test_xlsx_parsing_and_header_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.xlsx"
            write_xlsx(path, [("Cards", [
                ["eCard Number", "Class Date", "First", "Last", "Email Address", "Course Name"],
                ["123456789012", "7/1/2026", "Avery", "Sample", "avery@example.test", "AHA BLS"],
            ])])
            rows, errors = parse_file(source(path), path)
            self.assertEqual(errors, [])
            self.assertEqual(rows[0].ecard_code, "123456789012")
            self.assertEqual(rows[0].normalized_course, "BLS")
            self.assertEqual(rows[0].class_date, "2026-07-01")

    def test_csv_parsing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerows([
                    ["eCard Code", "Course Date", "First Name", "Last Name", "Email", "Course Modules"],
                    ["123456789012", "7/1/2026", "Avery", "Sample", "avery@example.test", "Heartsaver Total"],
                ])
            rows, _ = parse_file(source(path), path)
            self.assertEqual(rows[0].normalized_course, "HS_TOTAL")

    def test_multiple_sheet_workbook(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "multi.xlsx"
            header = [["eCard Code", "First Name", "Last Name", "Course"]]
            write_xlsx(path, [
                ("First", header + [["123456789012", "Avery", "Sample", "BLS"]]),
                ("Second", header + [["123456789013", "Jordan", "Example", "BLS"]]),
            ])
            rows, _ = parse_file(source(path), path)
            self.assertEqual({row.source_sheet for row in rows}, {"First", "Second"})

    def test_missing_ecard_is_invalid_not_discarded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.csv"
            path.write_text(
                "eCard Code,First Name,Last Name,Course\n,Avery,Sample,BLS\n",
                encoding="utf-8",
            )
            rows, _ = parse_file(source(path), path)
            self.assertEqual(len(rows), 1)
            self.assertIn("missing_ecard_code", rows[0].validation_errors)

    def test_expiration_row_without_ecard_is_reference_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "expiration-reference.csv"
            path.write_text(
                "eCard Code,First Name,Last Name,Class Date,Expiration Date\n"
                ",Avery,Sample,7/1/2024,7/31/2026\n",
                encoding="utf-8",
            )
            rows, _ = parse_file(source(path), path)
            self.assertEqual(
                rows[0].record_category, "historical_expiration_reference"
            )
            self.assertNotIn("missing_ecard_code", rows[0].validation_errors)
            result = reconcile(
                rows, {"profiles": [profile()], "history": []}
            )[0]
            self.assertEqual(result.match.status, "reference_only")
            self.assertIsNone(result.proposed_history_insert)
            self.assertIsNone(result.proposed_profile_update)

    def test_malformed_date_is_preserved_as_error(self) -> None:
        value, error = parse_date("not-a-date")
        self.assertIsNone(value)
        self.assertEqual(error, "malformed_date:not-a-date")

    def test_normalized_ecard_hyphens_and_spaces(self) -> None:
        self.assertEqual(normalize_ecard("1234-5678 9012"), ("123456789012", None))


class MatchingTests(unittest.TestCase):
    def test_exact_email_match(self) -> None:
        result = DeterministicMatcher([profile()], []).match(certification())
        self.assertEqual(result.status, "exact_match")
        self.assertEqual(result.method, "exact_email_compatible_course")

    def test_exact_name_course_date_match(self) -> None:
        candidate = profile(email="different@example.test")
        result = DeterministicMatcher([candidate], []).match(
            certification(email=None)
        )
        self.assertEqual(result.method, "exact_name_compatible_course_and_date")

    def test_unique_exact_name_and_compatible_course_match(self) -> None:
        candidate = profile(
            email="different@example.test",
            scheduled_class_date="2026-08-01T12:00:00Z",
        )
        result = DeterministicMatcher([candidate], []).match(
            certification(email=None)
        )
        self.assertEqual(
            result.method, "exact_name_unique_compatible_profile"
        )

    def test_ambiguous_duplicate_names(self) -> None:
        rows = [profile("one"), profile("two")]
        result = DeterministicMatcher(rows, []).match(certification(email=None))
        self.assertEqual(result.status, "ambiguous")

    def test_incompatible_course_match(self) -> None:
        result = DeterministicMatcher([profile(course="HS Total")], []).match(
            certification()
        )
        self.assertNotEqual(result.status, "exact_match")

    def test_fuzzy_name_is_review_only(self) -> None:
        result = DeterministicMatcher(
            [profile(first="Averyy", email="different@example.test")], []
        ).match(certification(email=None))
        self.assertEqual(result.status, "probable_match")
        self.assertIsNone(result.employee_profile_id)
        self.assertEqual(result.suggested_employee_profile_id, "profile-1")

    def test_non_maxim_record(self) -> None:
        result = DeterministicMatcher([profile()], []).match(
            certification(corporate_customer="CANYON")
        )
        self.assertEqual(result.status, "non_maxim")


class ReconcileTests(unittest.TestCase):
    def test_duplicate_files_and_rows(self) -> None:
        first = certification(source_file_id="one")
        second = certification(source_file_id="two")
        result = reconcile([first, second], {"profiles": [profile()], "history": []})
        self.assertIsNone(result[0].duplicate_of)
        self.assertIsNotNone(result[1].duplicate_of)

    def test_older_expiration_rejected(self) -> None:
        candidate = profile(
            expiration_date="2029-01-01",
            prior_ecard_code="999999999999",
            prior_class_date="2027-01-01T12:00:00Z",
        )
        result = reconcile(
            [certification()], {"profiles": [candidate], "history": []}
        )[0]
        self.assertIsNone(result.proposed_profile_update)
        self.assertIn("earlier_or_equal_expiration", result.skip_reasons)

    def test_newer_expiration_accepted(self) -> None:
        candidate = profile(
            expiration_date="2027-01-01",
            prior_ecard_code="999999999999",
            prior_class_date="2025-01-01T12:00:00Z",
        )
        result = reconcile(
            [certification()], {"profiles": [candidate], "history": []}
        )[0]
        self.assertEqual(
            result.proposed_profile_update["expiration_date"], "2028-07-31"
        )

    def test_corrected_replacement_ecard_preserves_new_history(self) -> None:
        result = reconcile(
            [certification(ecard_code="123456789013")],
            {"profiles": [profile(prior_ecard_code="123456789012")], "history": []},
        )[0]
        self.assertEqual(
            result.proposed_history_insert["ecard_number"], "123456789013"
        )

    def test_rerun_idempotency(self) -> None:
        record = certification()
        history = [{
            "id": "history-1",
            "employee_profile_id": "profile-1",
            "ecard_number": record.ecard_code,
            "course": "BLS",
        }]
        result = reconcile(
            [record], {"profiles": [profile()], "history": history}
        )[0]
        self.assertIsNone(result.proposed_history_insert)
        self.assertIn("ecard_already_in_certification_history", result.skip_reasons)

    def test_ambiguous_existing_ecard_never_proposes_reconciliation(self) -> None:
        record = certification()
        history = [{
            "id": "history-1",
            "employee_profile_id": "profile-1",
            "ecard_number": record.ecard_code,
            "course": "BLS",
            "source_occurrences": [],
        }]
        result = reconcile(
            [record],
            {"profiles": [profile(course="HS Total")], "history": history},
        )[0]
        self.assertEqual(result.match.status, "conflict")
        self.assertIsNone(result.proposed_history_reconciliation)
        self.assertIsNone(result.proposed_profile_update)

    def test_unsupported_file_format_set(self) -> None:
        from scripts.certification_import.parsers import SUPPORTED_EXTENSIONS
        self.assertNotIn(".pdf", SUPPORTED_EXTENSIONS)


class CertificationPolicyTests(unittest.TestCase):
    TODAY = date(2026, 7, 30)
    CALCULATED_AT = datetime(2026, 7, 30, 12, tzinfo=timezone.utc)

    def assess(self, record: NormalizedCertification):
        return assess_certification(
            record,
            profile(),
            today=self.TODAY,
            calculated_at=self.CALCULATED_AT,
        )

    def test_old_credential_without_expiration_is_historical_unknown(self) -> None:
        decision = self.assess(certification(
            normalized_course="UNKNOWN",
            course_name_raw="Unverified Provider CPR",
            class_date="2022-01-10",
            source_expiration_date=None,
        ))
        self.assertEqual(decision.certification_status, "historical_unknown")
        self.assertEqual(decision.expiration_source, "unknown")

    def test_recent_without_verified_policy_is_historical_unknown(self) -> None:
        decision = self.assess(certification(
            normalized_course="UNKNOWN",
            course_name_raw="Unverified Provider CPR",
            class_date="2026-07-20",
            source_expiration_date=None,
        ))
        self.assertEqual(decision.certification_status, "historical_unknown")

    def test_explicit_future_expiration_is_current(self) -> None:
        decision = self.assess(certification(
            source_expiration_date="2027-01-01"
        ))
        self.assertEqual(decision.certification_status, "current")
        self.assertEqual(decision.expiration_source, "source")
        self.assertIsNone(decision.calculation_policy)

    def test_explicit_past_expiration_is_expired(self) -> None:
        decision = self.assess(certification(
            source_expiration_date="2025-01-01"
        ))
        self.assertEqual(decision.certification_status, "expired")
        self.assertEqual(decision.expiration_source, "source")

    def test_verified_calculated_future_expiration_is_current(self) -> None:
        decision = self.assess(certification(
            class_date="2026-07-01",
            source_expiration_date=None,
        ))
        self.assertEqual(decision.certification_status, "current")
        self.assertEqual(decision.expiration_date, "2028-07-31")
        self.assertEqual(decision.expiration_source, "calculated_policy")
        self.assertEqual(decision.calculation_policy, AHA_MONTH_END_POLICY)
        self.assertEqual(decision.calculated_from_date, "2026-07-01")

    def test_verified_calculated_past_expiration_is_expired(self) -> None:
        decision = self.assess(certification(
            class_date="2022-07-01",
            source_expiration_date=None,
        ))
        self.assertEqual(decision.certification_status, "expired")
        self.assertEqual(decision.expiration_date, "2024-07-31")

    def test_newer_compatible_credential_supersedes_older(self) -> None:
        history = [{
            "id": "old-history",
            "employee_profile_id": "profile-1",
            "ecard_number": "999999999999",
            "course": "BLS",
            "issue_date": "2024-06-01",
            "certification_status": "current",
        }]
        result = reconcile(
            [certification(
                class_date="2026-07-01",
                source_expiration_date=None,
            )],
            {"profiles": [profile()], "history": history},
            today=self.TODAY,
            calculated_at=self.CALCULATED_AT,
        )[0]
        self.assertEqual(
            result.proposed_history_supersessions[0]["history_id"],
            "old-history",
        )

    def test_unrelated_course_is_not_superseded(self) -> None:
        history = [{
            "id": "pals-history",
            "employee_profile_id": "profile-1",
            "ecard_number": "999999999999",
            "course": "PALS",
            "issue_date": "2024-06-01",
            "certification_status": "current",
        }]
        result = reconcile(
            [certification(
                class_date="2026-07-01",
                source_expiration_date=None,
            )],
            {"profiles": [profile()], "history": history},
            today=self.TODAY,
            calculated_at=self.CALCULATED_AT,
        )[0]
        self.assertEqual(result.proposed_history_supersessions, [])

    def test_historical_unknown_does_not_project(self) -> None:
        result = reconcile(
            [certification(
                class_date=None,
                issue_date=None,
                source_expiration_date=None,
            )],
            {"profiles": [profile()], "history": []},
            today=self.TODAY,
        )[0]
        self.assertEqual(
            result.proposed_history_insert["certification_status"],
            "historical_unknown",
        )
        self.assertIsNone(result.proposed_profile_update)
        self.assertNotIn(
            "workflow_stage",
            result.proposed_history_insert,
        )

    def test_expired_certification_does_not_change_workflow(self) -> None:
        result = reconcile(
            [certification(source_expiration_date="2025-01-01")],
            {"profiles": [profile()], "history": []},
            today=self.TODAY,
        )[0]
        self.assertIsNone(result.proposed_profile_update)
        self.assertEqual(
            result.proposed_history_insert["certification_status"], "expired"
        )

    def test_current_projects_only_when_newer_and_compatible(self) -> None:
        result = reconcile(
            [certification(source_expiration_date="2028-07-31")],
            {"profiles": [profile(
                expiration_date="2027-01-01",
                prior_class_date="2025-01-01T12:00:00Z",
            )], "history": []},
            today=self.TODAY,
        )[0]
        self.assertEqual(
            result.proposed_profile_update["expiration_date"], "2028-07-31"
        )

    def test_existing_ecard_conflicting_course_is_conflict_review(self) -> None:
        record = certification()
        history = [{
            "id": "history-1",
            "employee_profile_id": "profile-1",
            "ecard_number": record.ecard_code,
            "course": "BLS",
            "source_occurrences": [],
        }]
        result = reconcile(
            [record],
            {"profiles": [profile(course="HS Total")], "history": history},
            today=self.TODAY,
        )[0]
        self.assertEqual(result.match.status, "conflict")
        self.assertIsNone(result.proposed_history_reconciliation)

    def test_existing_ecard_conflicting_participant_is_conflict_review(self) -> None:
        record = certification(
            email="different@example.test",
            normalized_name="different person",
        )
        history = [{
            "id": "history-1",
            "employee_profile_id": "profile-1",
            "ecard_number": record.ecard_code,
            "course": "BLS",
            "source_occurrences": [],
        }]
        result = reconcile(
            [record],
            {"profiles": [profile()], "history": history},
            today=self.TODAY,
        )[0]
        self.assertEqual(result.match.status, "conflict")
        self.assertEqual(
            result.match.method, "existing_ecard_identity_conflict"
        )
        self.assertIsNone(result.proposed_history_reconciliation)

    def test_calculated_expiration_is_distinguishable_from_source(self) -> None:
        calculated = self.assess(certification(
            source_expiration_date=None
        ))
        sourced = self.assess(certification(
            source_expiration_date="2028-07-31"
        ))
        self.assertEqual(calculated.expiration_source, "calculated_policy")
        self.assertEqual(sourced.expiration_source, "source")
        self.assertIsNotNone(calculated.calculation_version)
        self.assertIsNone(sourced.calculation_version)

    def test_month_end_boundaries_include_leap_years(self) -> None:
        self.assertEqual(
            two_years_through_end_of_month("2024-02-29"), "2026-02-28"
        )
        self.assertEqual(
            two_years_through_end_of_month("2022-02-10"), "2024-02-29"
        )
        self.assertEqual(
            two_years_through_end_of_month("2025-04-01"), "2027-04-30"
        )


if __name__ == "__main__":
    unittest.main()
