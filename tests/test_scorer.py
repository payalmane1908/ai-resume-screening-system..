"""Tests for services/scorer.py"""

from app.services.scorer import (
    achievements_score,
    extract_years_of_experience,
    experience_score,
    normalize_weights,
    rank_candidates,
    skill_match_score,
    weighted_score,
)


class TestSkillMatchScore:
    def test_full_match(self):
        score, matched, missing = skill_match_score(["python", "flask"], ["python", "flask"])
        assert score == 100.0
        assert sorted(matched) == ["flask", "python"]
        assert missing == []

    def test_partial_match(self):
        score, matched, missing = skill_match_score(["python"], ["python", "flask", "aws"])
        assert 30 <= score <= 34  # 1/3 = 33.33
        assert matched == ["python"]
        assert "flask" in missing

    def test_no_match(self):
        score, matched, missing = skill_match_score(["java"], ["python", "flask"])
        assert score == 0.0
        assert matched == []
        assert len(missing) == 2

    def test_empty_jd_skills(self):
        score, matched, missing = skill_match_score(["python"], [])
        assert score == 0.0

    def test_empty_resume_skills(self):
        score, matched, missing = skill_match_score([], ["python"])
        assert score == 0.0
        assert missing == ["python"]


class TestExtractYearsOfExperience:
    def test_basic_years(self):
        assert extract_years_of_experience("I have 5 years of experience") == 5.0

    def test_plus_years(self):
        assert extract_years_of_experience("10+ years in software development") == 10.0

    def test_decimal_years(self):
        assert extract_years_of_experience("3.5 years of Python development") == 3.5

    def test_multiple_mentions(self):
        text = "2 years in Java, 5 years in Python"
        assert extract_years_of_experience(text) == 5.0  # Takes the max

    def test_no_experience(self):
        assert extract_years_of_experience("Fresh graduate looking for work") == 0.0

    def test_none_input(self):
        assert extract_years_of_experience(None) == 0.0


class TestExperienceScore:
    def test_meets_target(self):
        assert experience_score(5, 5) == 100.0

    def test_exceeds_target(self):
        assert experience_score(10, 5) == 100.0  # capped at 100

    def test_below_target(self):
        assert experience_score(2, 4) == 50.0

    def test_zero_target(self):
        assert experience_score(0, 0) == 100.0


class TestAchievementsScore:
    def test_multiple_achievements(self):
        assert achievements_score(["a", "b", "c"]) == 60.0  # 3 * 20

    def test_capped_at_100(self):
        assert achievements_score(["a"] * 10) == 100.0

    def test_no_achievements(self):
        assert achievements_score([]) == 0.0

    def test_none(self):
        assert achievements_score(None) == 0.0


class TestWeightedScore:
    def test_default_weights(self):
        score = weighted_score(80, 70, 60, 50)
        assert 0 <= score <= 100

    def test_perfect_match_bonus(self):
        score = weighted_score(90, 90, 90, 90)
        assert score > 90  # Should get "Perfect Match" bonus

    def test_low_relevance_penalty(self):
        score = weighted_score(10, 20, 90, 90)
        # Should be penalized with 0.7 multiplier
        normal = 0.4 * 10 + 0.35 * 20 + 0.15 * 90 + 0.10 * 90
        assert score < normal


class TestNormalizeWeights:
    def test_default(self):
        w = normalize_weights()
        assert abs(sum(w.values()) - 1.0) < 0.01

    def test_custom(self):
        w = normalize_weights({"keyword": 50, "semantic": 50})
        assert abs(sum(w.values()) - 1.0) < 0.01


class TestRankCandidates:
    def test_ranking_order(self):
        cands = [
            {"name": "A", "final_score": 60},
            {"name": "B", "final_score": 90},
            {"name": "C", "final_score": 75},
        ]
        ranked = rank_candidates(cands)
        assert ranked[0]["name"] == "B"
        assert ranked[0]["rank"] == 1
        assert ranked[1]["name"] == "C"
        assert ranked[2]["name"] == "A"
