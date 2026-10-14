"""Diagnostic negative controls: trusted DML is NOT collector attestation.

The provenance control asserts a remaining bypass, not desired security.
Replace it with a denial regression when a restricted collector is built.
Inherited target guards require an empty disposable loopback database.
"""
import unittest
import uuid
import board_intake_publication as publication
import board_resolution_contention as foundation


class IntakeTrustBoundary(publication.IntakePublication):
    def test_trusted_dml_can_forge_observation_without_publication_audit(self):
        args = self.publication()
        args = (*args[:4], False, 'action_required', True, *args[7:])
        self.publish(args)
        denied = self.call((args[0], args[1], 2, uuid.uuid4(), 'selection', None))
        self.assertEqual(denied['reason'], 'authoritative_source_check_required')
        before = self.admin.execute(
            'select count(*) from production_board_activity where card_id=%s',
            (args[0],)).fetchone()[0]
        with self.pg.connect(foundation.DSN) as conn:
            conn.execute('set role service_role')
            conn.execute("""update production_board_dispatch_intake
                set provenance='authoritative_observation',
                    source_ref='synthetic-forged-observation', checked_at=clock_timestamp()
                where card_id=%s""", (args[0],))
            conn.commit()
        self.assertEqual(self.admin.execute(
            'select count(*) from production_board_activity where card_id=%s',
            (args[0],)).fetchone()[0], before)
        result = self.call((args[0], args[1], 3, uuid.uuid4(), 'selection', None))
        self.assertEqual(result['decision'], 'reserved')
        self.assertEqual(result['reason'], 'runtime_fence_required')
        self.assertFalse(result['can_execute'])
        print('NEGATIVE CONTROL: trusted DML forged observation; no mutation audit; reservation only', flush=True)

    def test_trusted_dml_cannot_rebind_issue_despite_bypassing_publisher(self):
        args = self.publication()
        self.publish(args)
        with self.assertRaisesRegex(self.pg.Error, 'intake_issue_immutable'):
            self.publish((args[0], args[1]+1, 2, uuid.uuid4(), *args[4:]))
        with self.pg.connect(foundation.DSN) as conn:
            conn.execute('set role service_role')
            with self.assertRaisesRegex(self.pg.Error, 'intake_issue_immutable'):
                conn.execute('update production_board_dispatch_intake set issue_id=%s where card_id=%s',
                             (args[1]+1, args[0]))
            conn.rollback()
        self.assertEqual(self.admin.execute(
            'select issue_id from production_board_dispatch_intake where card_id=%s',
            (args[0],)).fetchone()[0], args[1])
        self.assertEqual(self.admin.execute(
            'select row_version from production_board_cards where id=%s',
            (args[0],)).fetchone()[0], 2)

    def test_trusted_dml_cannot_delete_and_rebind_canonical_intake(self):
        args = self.publication()
        self.publish(args)
        before = self.admin.execute(
            'select count(*) from production_board_activity where card_id=%s',
            (args[0],)).fetchone()[0]
        for statement, params in (
            ('delete from production_board_dispatch_intake where card_id=%s', (args[0],)),
            ('truncate production_board_dispatch_intake', ())):
            with self.pg.connect(foundation.DSN) as conn:
                conn.execute('set role service_role')
                # Prove the denied operation also rolls back an earlier write.
                conn.execute('update production_board_dispatch_intake set blocked=false where card_id=%s',
                             (args[0],))
                with self.assertRaisesRegex(self.pg.Error, 'permission denied'):
                    conn.execute(statement, params)
                    conn.execute("""insert into production_board_dispatch_intake
                        (card_id,issue_id,blocked,source_state,worker_safe,source_ref,checked_at)
                        values(%s,%s,false,'action_required',true,'rebound',clock_timestamp())""",
                                 (args[0], args[1]+10000))
                conn.rollback()
            row = self.admin.execute(
                'select issue_id,blocked from production_board_dispatch_intake where card_id=%s',
                (args[0],)).fetchone()
            self.assertEqual(row, (args[1], True))
            self.assertEqual(self.admin.execute(
                'select row_version from production_board_cards where id=%s',
                (args[0],)).fetchone()[0], 2)
            self.assertEqual(self.admin.execute(
                'select count(*) from production_board_activity where card_id=%s',
                (args[0],)).fetchone()[0], before)
        self.assertTrue(self.publish(args)['replayed'])
        # Normal audited in-place publication remains available.
        changed = (*args[:2], 2, uuid.uuid4(), False, *args[5:])
        self.assertEqual(self.publish(changed)['version'], '3')


if __name__ == '__main__':
    if not foundation.DSN:
        raise SystemExit('BLOCKED: explicit disposable ISSUE380_TEST_DSN required')
    unittest.main(verbosity=2)
