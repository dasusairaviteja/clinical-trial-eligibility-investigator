"""Filesystem controls for the private research arm mapping, not clinical validation."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from clinical_trial.adjudication import write_private_key


class PrivateReviewKeyTests(unittest.TestCase):
    def test_private_before_first_write_even_with_permissive_umask(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "key.json"
            original_fdopen = os.fdopen
            observed = []

            def inspect_descriptor(descriptor, *args, **kwargs):
                observed.append(os.fstat(descriptor).st_mode & 0o777)
                return original_fdopen(descriptor, *args, **kwargs)

            previous_umask = os.umask(0)
            try:
                with patch("clinical_trial.adjudication.os.fdopen", side_effect=inspect_descriptor):
                    write_private_key(path, {"mapping": "fixture"})
            finally:
                os.umask(previous_umask)
            self.assertEqual(observed, [0o600])
            self.assertEqual(json.loads(path.read_text()), {"mapping": "fixture"})

    def test_existing_files_and_symlinks_are_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "existing.json"
            target.write_text("original")
            link = Path(directory) / "link.json"
            link.symlink_to(target)
            for path in (target, link):
                with self.assertRaises(FileExistsError):
                    write_private_key(path, {"mapping": "fixture"})
            self.assertEqual(target.read_text(), "original")

    def test_invalid_payload_does_not_create_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "key.json"
            with self.assertRaises(ValueError):
                write_private_key(path, {"invalid": float("nan")})
            self.assertFalse(path.exists())
