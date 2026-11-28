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
        self.assertTrue(probe.coverage_passed(pages))
        self.assertTrue(probe.coverage_passed(dict(pages, acls=page(0, 0, 0))))
        self.assertFalse(probe.coverage_passed(dict(pages, acls=page(147, 136, 11))))
        self.assertFalse(probe.coverage_passed(dict(pages, bls=page(147, 136, 0))))
        self.assertFalse(probe.coverage_passed({key: page(0, 0, 0) for key in pages}))
        self.assertFalse(probe.coverage_passed(dict(pages, bls={'counts': {}})))
        self.assertFalse(probe.coverage_passed({'bls': complete}))
        self.assertFalse(probe.coverage_passed({}))

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
        from scripts.fetch_canonical_scheduling_demand import stable_hash
        from scripts.validate_layered_occupancy_projection import SCHEMA
        endpoint = {"generated_at": "2026-10-31T14:00:00Z", "sessions": []}
        fingerprint = (endpoint["generated_at"], stable_hash(endpoint))
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
                             return_value={k: {"key": k} for k in probe.REQUIRED_PAGE_KEYS}),
                patch.object(probe, "load_publication_demand", return_value=endpoint),
                patch.object(probe, "build_block_schedule_page", side_effect=lambda config: dict(payload,
                    pageKey=config["key"], schedulingModel=SCHEMA,
                    _canonicalDemandFingerprint=fingerprint,
                    _windowCoverageEvidence={"calendar_hash":"fixture", "expected":{}, "closed":{}}, layeredDiagnostics={"projected_sources": [], "reports": []})),
                patch.object(probe, "apply_final_live_availability_guard", side_effect=lambda row: row),
                patch.object(probe, "public_selector_availability_payload", return_value={"dates": []}),
                patch.object(probe, "render_html", return_value="<body></body>"),
                patch("builtins.print") as stdout,
            ):
                with self.assertRaisesRegex(RuntimeError, "independent customer outcome"):
                    probe.run()
            serialized = (root / "data/runtime/audit_previews/v2_release_probe/proof.json").read_text()
            proof = json.loads(serialized)
            self.assertTrue(proof["calculation_completed"])
            self.assertTrue(proof["coverage_passed"])
            self.assertEqual(proof["outcome_status"], "unproven")
            self.assertFalse(proof["release_passed"])
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



class IndependentOutcomeComparatorTests(unittest.TestCase):
    def setUp(self):
        self.scopes = {(page, "2099-01-01", "fixture-instructor", "fixture-course")
                       for page in probe.REQUIRED_PAGE_KEYS}
        self.target = next(scope for scope in self.scopes if scope[0] == "bls")
        self.offer = ("2099-01-01T13:00:00Z", "2099-01-01T15:00:00Z",
                      "fixture-room", "open", "request_only")
        self.expected = {scope: {"offers": [], "zero_reason": "no_qualified_coverage"}
                         for scope in self.scopes}
        self.expected[self.target] = {"offers": [self.offer]}
        self.actual = {scope: list(entry["offers"])
                       for scope, entry in self.expected.items()}

    def compare(self, actual=None, expected=None, observed_epoch="fixture-epoch"):
        return probe.compare_expected_outcomes(
            self.scopes, self.expected if expected is None else expected,
            self.actual if actual is None else actual,
            expected_epoch="fixture-epoch", observed_epoch=observed_epoch)

    def test_exact_match_and_independently_explained_zero(self):
        self.assertEqual(self.compare()["status"], "matched")
        actual = dict(self.actual)
        actual[self.target] = [("2099-01-01T08:00:00-05:00", "2099-01-01T10:00:00-05:00",
                                *self.offer[2:])]
        self.assertEqual(self.compare(actual)["status"], "matched")

    def test_empty_or_dropped_family_cannot_match(self):
        all_empty = {scope: [] for scope in self.scopes}
        self.assertEqual(self.compare(all_empty)["missing_offer_count"], 1)
        self.assertEqual(self.compare({})["status"], "mismatch")
        missing = dict(self.actual)
        del missing[self.target]
        self.assertEqual(self.compare(missing)["missing_scope_count"], 1)

    def test_matching_counts_wrong_start_role_or_capability_fail(self):
        mutations = [
            ("2099-01-01T13:30:00Z", *self.offer[1:]),
            (*self.offer[:3], "seated", self.offer[4]),
            (*self.offer[:4], "verified_booking"),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                result = self.compare(self.actual | {self.target: [mutation]})
                self.assertEqual(result["status"], "mismatch")
                self.assertEqual(result["missing_offer_count"], 1)
                self.assertEqual(result["unexpected_offer_count"], 1)
                self.assertNotRegex(json.dumps(result), "fixture|2099")

    def test_private_seated_leak_and_duplicates_fail(self):
        scope = next(scope for scope in self.scopes if scope[0] == "acls")
        result = self.compare(self.actual | {scope: [(*self.offer[:3], "seated", "verified_booking")]})
        self.assertEqual(result["unexpected_offer_count"], 1)
        self.assertEqual(result["status"], "mismatch")
        result = self.compare(self.actual | {self.target: [self.offer, self.offer]})
        self.assertEqual(result["duplicate_offer_count"], 1)

    def test_missing_stale_or_invalid_expectation_is_not_match(self):
        self.assertEqual(self.compare(expected={})["status"], "mismatch")
        self.assertEqual(self.compare(observed_epoch="older")["status"], "unproven")
        scope = next(scope for scope in self.scopes if scope[0] == "pals")
        expected = self.expected | {scope: {"offers": []}}
        self.assertEqual(self.compare(expected=expected)["invalid_scope_count"], 1)

    def test_invalid_offer_bounds_fail(self):
        invalid = ("2099-01-01T16:00:00Z", *self.offer[1:])
        result = self.compare(self.actual | {self.target: [invalid]})
        self.assertEqual(result["invalid_offer_count"], 1)
        self.assertEqual(result["status"], "mismatch")


class FrozenRunnerTests(unittest.TestCase):
    def test_frozen_local_runner_checks_real_route_and_authority_axes(self):
        import hashlib
        import shutil
        from datetime import timedelta
        from scripts import layered_release_oracle as o
        from scripts.fetch_canonical_scheduling_demand import stable_hash
        from scripts.validate_layered_occupancy_projection import SCHEMA

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            authorities = root / "restricted" / "authorities"
            authorities.mkdir(parents=True)
            target = authorities.parent / "expected.json"
            for rel in o.INPUTS:
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}")
            shutil.copyfile(probe.ROOT / "docs/assets/resolved-selector-availability.js",
                            root / "docs/assets/resolved-selector-availability.js")
            now = o.instant("2026-10-31T14:00:00Z")
            pages = probe.REQUIRED_PAGE_KEYS
            endpoint = {"generated_at": now.isoformat(), "sessions": []}
            fingerprint = (endpoint["generated_at"], stable_hash(endpoint))
            configs = {page: {"allowed_course_ids": ["101"], "output_path": f"docs/{page}.html"}
                       for page in pages}
            configs["bls"]["allowed_course_ids"].append("202")
            hashes = o.freeze_inputs(root)
            epoch = o.epoch_for(now, hashes)
            manifest = dict(schema=o.SCHEMA, as_of=now.isoformat(), epoch=epoch, input_sha256=hashes,
                page_courses={p: c["allowed_course_ids"] for p, c in configs.items()},
                instructors={"primary-key": "Fixture Lead", "other-key": "Fixture Other"},
                rooms={"Fixture Room": "fixture-room"}, authority_sha256={}, outcomes=[])
            witnesses = {"qualified_instructors": {"instructors": manifest["instructors"]},
                         "resources": {"rooms": manifest["rooms"]},
                         "catalog": {"page_courses": manifest["page_courses"]}}
            for lane in o.AUTHORITIES:
                content = json.dumps(dict(epoch=epoch, **witnesses.get(lane, {}))).encode()
                (authorities / (lane + ".json")).write_bytes(content)
                manifest["authority_sha256"][lane] = hashlib.sha256(content).hexdigest()
            slot_date = "2026-10-31"
            scope = ("bls", slot_date, "primary-key", "101")
            extra_scope = ("bls", slot_date, "primary-key", "202")
            seated_scope = ("bls", "2026-11-01", "primary-key", "101")
            expected = {
                scope: ["2026-11-01T03:30:00Z", "2026-11-01T05:30:00Z", "fixture-room", "open", "request_only"],
                extra_scope: ["2026-11-01T03:30:00Z", "2026-11-01T04:30:00Z", "fixture-room", "barnacle", "request_only"],
                seated_scope: ["2026-11-01T18:00:00Z", "2026-11-01T19:00:00Z", "fixture-room", "seated", "request_only"],
            }
            for i in range(90):
                day = (now.astimezone(o.ET).date() + timedelta(days=i)).isoformat()
                for page in pages:
                    for teacher in manifest["instructors"]:
                        for course in manifest["page_courses"][page]:
                            key = (page, day, teacher, course)
                            row = dict(scope=list(key), offers=[expected[key]] if key in expected else [])
                            if key not in expected:
                                row["zero_reason"] = "no_authorized_route" if teacher == "primary-key" else "no_qualified_coverage"
                            manifest["outcomes"].append(row)
            target.write_text(json.dumps(manifest))

            course = dict(courseId="101", instructor="Fixture Lead", location="Fixture Room",
                          schedulerConsumptionMinutes=120, offerType="dynamic_appointment")
            edge = dict(course, courseId="202", schedulerConsumptionMinutes=60, scheduleRole="barnacle")
            seated = dict(course, offerType="seated_class", schedulerConsumptionMinutes=60,
                          registrationUrl="https://www.910cpr.com/register/?session=123")
            populated = dict(validUntil="2026-10-31T15:00:00Z", dates=[
                dict(date=slot_date, startTimes=[dict(startTime="23:30", courses=[course, edge])]),
                dict(date="2026-11-01", startTimes=[dict(startTime="13:00", courses=[seated])])])
            capabilities = {"sessions": {}}

            def build(config):
                from scripts.block_start_time_selector import selector_reference_datetime
                self.assertEqual(selector_reference_datetime(), now.astimezone(o.ET).replace(tzinfo=None))
                page = next(k for k, v in configs.items() if config is v)
                return dict(page=page, pageKey=page, schedulingModel=SCHEMA,
                            _canonicalDemandFingerprint=fingerprint,
                    _windowCoverageEvidence={"calendar_hash":"fixture", "expected":{}, "closed":{}},
                            layeredDiagnostics={"projected_sources": [], "reports": []},
                            counts=dict(input_windows=1, evaluated_windows=1, failed_windows=0))

            def render(payload):
                p = payload["page"]
                return (
                    '<body>\nconst availabilityUrl = ' + json.dumps('/data/block-selector-availability/' + p + '.json?v=one') +
                    ';\nconst courseOptions = [{"courseId":"101"},{"courseId":"202"}];\n' +
                    'const nativeClassCapabilities = ' + json.dumps(capabilities) + ';\n</body>')

            def run():
                with (
                    patch.object(probe, "ROOT", root),
                    patch.object(probe, "load_block_schedule_page_configs", return_value=configs),
                    patch.object(probe, "load_publication_demand", return_value=endpoint),
                    patch.object(probe, "build_block_schedule_page", side_effect=build),
                    patch.object(probe, "apply_final_live_availability_guard", side_effect=lambda x: x),
                    patch.object(probe, "render_html", side_effect=render),
                    patch.object(probe, "public_selector_availability_payload",
                        side_effect=lambda payload: populated if payload["page"]=="bls" else {"dates": []}),
                    patch("builtins.print") as stdout,
                ):
                    with self.assertRaisesRegex(RuntimeError, "publication remains stopped"):
                        probe.run(target)
                saved = root / "data/runtime/audit_previews/v2_release_probe/proof.json"
                report = json.loads(saved.read_text())
                self.assertNotRegex(saved.read_text() + str(stdout.call_args), "Fixture|fixture-room|primary-key|23:30")
                self.assertFalse(report["release_passed"])
                return report

            self.assertEqual(run()["outcome_status"], "local_replay_matched")
            capabilities["sessions"]["123"] = dict(courseId="101", date="2026-11-01",
                                                    startTime="13:00", location="Fixture Room")
            mismatch = run()
            self.assertEqual(mismatch["outcome_status"], "mismatch")
            self.assertEqual(mismatch["local_replay_comparison"]["unexpected_offer_count"], 1)
            capabilities["sessions"].clear()
            originals = manifest["outcomes"]
            manifest["outcomes"] = [r for r in originals if r["scope"][1] != "2026-11-16"
                                     and r["scope"][2] != "other-key"]
            target.write_text(json.dumps(manifest))
            self.assertGreater(run()["local_replay_comparison"]["missing_scope_count"], 90)
            manifest["outcomes"] = originals
            manifest["epoch"] = "wrong-epoch"
            target.write_text(json.dumps(manifest))
            # Bad manifest fails before any attested/frozen replay may run.
            with self.assertRaisesRegex(ValueError, "epoch mismatch"):
                o.configure(manifest, hashes, configs, pages, authorities)

    def test_wrong_local_date_does_not_match_even_when_both_sides_are_wrong(self):
        case = IndependentOutcomeComparatorTests()
        case.setUp()
        offer = ("2099-01-01T02:00:00Z", "2099-01-01T06:00:00Z", *case.offer[2:])
        result = case.compare(case.actual | {case.target: [offer]},
                              case.expected | {case.target: {"offers":[offer]}})
        self.assertEqual(result["status"], "mismatch")
        self.assertEqual(result["invalid_offer_count"], 2)
