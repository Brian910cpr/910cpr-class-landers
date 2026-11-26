import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from scripts import run_layered_release_probe as probe

class ProbeTests(unittest.TestCase):
    def test_failed_calculation_restores_shadow_policy_and_records_no_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            policy=root/'data/config/layered_scheduling_policy.json';policy.parent.mkdir(parents=True)
            original=b'{"mode":"shadow"}';policy.write_bytes(original)
            snap=root/'data/audit/live_availability_snapshot_preview.json';snap.parent.mkdir(parents=True);snap.write_text('{"layered_commitment_coverage":[]}')
            canonical=root/'data/runtime/canonical_scheduling_demand.json';canonical.parent.mkdir(parents=True);canonical.write_text('{"sessions":[]}')
            def fail(key):
                self.assertIsInstance(key,dict)
                self.assertEqual(json.loads(policy.read_bytes())["mode"],"active_local_v2")
                raise ValueError("invalid source")
            with patch.object(probe,'ROOT',root),patch.object(probe,'load_block_schedule_page_configs',return_value={'bls':{}}),patch.object(probe,'build_block_schedule_page',side_effect=fail):
                with self.assertRaises(ValueError):probe.run()
            self.assertEqual(policy.read_bytes(),original)
            result=json.loads((root/'data/runtime/audit_previews/v2_release_probe/proof.json').read_text())
            self.assertFalse(result['published']);self.assertNotIn('calculation_completed',result)

    def test_partial_window_evaluation_is_not_release_proof(self):
        def page(inputs, evaluated, failed):
            return {'counts': dict(input_windows=inputs,
                                   evaluated_windows=evaluated,
                                   failed_windows=failed)}
        complete = page(147, 147, 0)
        pages = {key: complete for key in probe.REQUIRED_PAGE_KEYS}
        self.assertTrue(probe.coverage_release_passed(pages))
        self.assertTrue(probe.coverage_release_passed(dict(pages, acls=page(0, 0, 0))))
        self.assertFalse(probe.coverage_release_passed(dict(pages, acls=page(147, 136, 11))))
        self.assertFalse(probe.coverage_release_passed(dict(pages, bls=page(147, 136, 0))))
        self.assertFalse(probe.coverage_release_passed({key: page(0, 0, 0) for key in pages}))
        self.assertFalse(probe.coverage_release_passed(dict(pages, bls={'counts': {}})))
        self.assertFalse(probe.coverage_release_passed({'bls': complete}))
        self.assertFalse(probe.coverage_release_passed({}))

    def test_proof_summary_does_not_emit_private_source_details(self):
        raw = [
            {'reason': 'missing directional travel rule: private-home->primary',
             'instructor': 'private-person', 'source_id': 'private-id',
             'start': '2026-11-26T12:34:00-05:00'},
            {'reason': 'invalid source private-id'},
        ]
        counts, by_date = probe.public_issue_summary(raw)
        self.assertEqual(counts, {'missing_directional_travel_rule': 1,
                                  'availability_coverage_unknown': 1})
        self.assertEqual(by_date, {
            '2026-11-26': {'missing_directional_travel_rule': 1},
            'unscoped': {'availability_coverage_unknown': 1},
        })
        serialized = json.dumps([counts, by_date])
        for private in ('private-home', 'private-person', 'private-id', '12:34'):
            self.assertNotIn(private, serialized)

    def test_proof_rejection_histogram_strips_reference_suffixes(self):
        raw = {"conflict_or_transition:fixture-private-one": 2,
               "conflict_or_transition:fixture-private-two": 4,
               "commitment_coverage_unknown:fixture-private-three": 1,
               "new fixture-private label": 5, "lead_time": 3}
        safe = probe.public_rejection_counts(raw)
        self.assertEqual(safe, {"conflict_or_transition": 6,
                                "commitment_coverage_unknown": 1,
                                "other_rejection": 5, "lead_time": 3})
        self.assertNotIn("fixture-private", json.dumps(safe))

    def test_probe_output_never_contains_source_from_rejection_histogram(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for rel, data in {
                "data/config/layered_scheduling_policy.json": {"mode": "shadow"},
                "data/audit/live_availability_snapshot_preview.json": {},
                "data/runtime/canonical_scheduling_demand.json": {},
            }.items():
                target = root / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps(data))
            payload = {
                "counts": {"input_windows": 1, "evaluated_windows": 1, "failed_windows": 0},
                "rejectionReasonCounts": {"conflict_or_transition:fixture-private-source": 2},
            }
            with (
                patch.object(probe, "ROOT", root),
                patch.object(probe, "load_block_schedule_page_configs",
                             return_value={k: {} for k in probe.REQUIRED_PAGE_KEYS}),
                patch.object(probe, "build_block_schedule_page", return_value=payload),
                patch.object(probe, "apply_final_live_availability_guard", return_value=payload),
                patch.object(probe, "public_selector_availability_payload", return_value={"dates": []}),
                patch.object(probe, "render_html", return_value="<body></body>"),
                patch("builtins.print") as stdout,
            ):
                probe.run()
            serialized = (root / "data/runtime/audit_previews/v2_release_probe/proof.json").read_text()
            self.assertNotIn("fixture-private-source", serialized)
            self.assertNotIn("fixture-private-source", stdout.call_args.args[0])
            self.assertEqual(json.loads(serialized)["pages"]["bls"]["rejection_reasons"],
                             {"conflict_or_transition": 2})

    def test_public_proof_strips_unpublished_offer_and_block_geometry(self):
        payload = {
            "counts": {"input_windows": 2, "evaluated_windows": 2,
                       "failed_windows": 0, "private-counter": 1},
            "synthesisBlockedDates": ["2099-10-09"],
            "schedulingModel": "private-metadata",
        }
        feed = {"dates": [{"date": "2099-10-10", "startTimes": [
            {"startTime": "13:37", "courses": [
                {"courseId": "private-course", "session_id": "private-session",
                 "offerType": "seated_class", "instructor": "private-instructor"},
                {"scheduleRole": "barnacle"},
                {},
            ]}
        ]}]}
        proof = probe.aggregate_page_proof(payload, feed)
        self.assertEqual(proof["offer_roles"], {"seated": 1, "barnacle": 1, "open": 1})
        self.assertEqual(proof["synthesis_blocked_date_count"], 1)
        self.assertEqual(proof["counts"], {"input_windows": 2,
                                          "evaluated_windows": 2, "failed_windows": 0})
        self.assertNotRegex(json.dumps(proof), "2099|13:37|private")

    def test_workflow_uploads_only_aggregate_proof(self):
        workflow = (probe.ROOT / ".github/workflows/refresh-admin-availability.yml").read_text()
        job = workflow.split("\n  v2-release-probe:", 1)[1]
        self.assertEqual([line.strip() for line in job.splitlines() if line.strip().startswith("path:")],
                         ["path: data/runtime/audit_previews/v2_release_probe/proof.json"])
