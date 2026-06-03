"""Tests for services/parser.py"""

import os
import tempfile

from app.services.parser import extract_text


class TestExtractText:
    def test_txt_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("Python developer with 5 years experience in Flask and AWS.")
            f.flush()
            path = f.name

        try:
            text = extract_text(path)
            assert "Python" in text
            assert "Flask" in text
            assert "5 years" in text
        finally:
            os.unlink(path)

    def test_unsupported_format(self):
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            path = f.name
        try:
            text = extract_text(path)
            assert text == "Unsupported file format"
        finally:
            os.unlink(path)
