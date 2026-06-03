"""Tests for services/skill_extractor.py"""

from app.services.skill_extractor import clean_text, extract_skills, highlight_skills


class TestExtractSkills:
    def test_basic_skills(self):
        text = "I am proficient in Python, Flask, and SQL."
        skills = extract_skills(text)
        assert "python" in skills
        assert "flask" in skills
        assert "sql" in skills

    def test_synonyms(self):
        text = "Experience with JS and ReactJS."
        skills = extract_skills(text)
        assert "javascript" in skills
        assert "react" in skills

    def test_case_insensitive(self):
        text = "PYTHON, DOCKER, AWS"
        skills = extract_skills(text)
        assert "python" in skills
        assert "docker" in skills
        assert "aws" in skills

    def test_no_false_positives(self):
        text = "I enjoy cooking and gardening."
        skills = extract_skills(text)
        assert len(skills) == 0

    def test_multi_word_skills(self):
        text = "Strong background in machine learning and natural language processing."
        skills = extract_skills(text)
        assert "machine learning" in skills
        assert "nlp" in skills

    def test_empty_input(self):
        assert extract_skills("") == []
        assert extract_skills(None) == []


class TestCleanText:
    def test_removes_special_chars(self):
        result = clean_text("Python (3.x) & Flask!")
        assert "python" in result
        assert "flask" in result

    def test_preserves_plus(self):
        result = clean_text("C++ developer")
        assert "c++" in result


class TestHighlightSkills:
    def test_wraps_in_mark(self):
        result = highlight_skills("I know Python and Flask", ["python", "flask"])
        assert "<mark>" in result
        assert "Python" in result or "python" in result

    def test_empty_skills(self):
        result = highlight_skills("Hello world", [])
        assert result == "Hello world"

    def test_none_text(self):
        result = highlight_skills(None, ["python"])
        assert result == ""
