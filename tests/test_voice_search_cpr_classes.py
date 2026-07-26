from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class VoiceSearchCprClassesWorkerTests(unittest.TestCase):
    def test_worker_endpoint_contract(self) -> None:
        result = subprocess.run(
            ["node", "--test", "worker/tests/voiceSearchCprClasses.test.mjs"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=30,
        )
        if result.returncode != 0:
            sys.stderr.write(result.stdout)
            sys.stderr.write(result.stderr)
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
