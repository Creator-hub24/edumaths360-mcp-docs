"""Unit tests for the pure maths layer (no MCP involved)."""

import re
from fractions import Fraction

import pytest

from edumaths360_mcp.problems import (
    DIFFICULTIES,
    TOPIC_GRADES,
    TOPICS,
    ProblemError,
    check,
    format_fraction,
    generate,
    parse_numbers,
    parse_problem_id,
    problem_from_id,
)

ALL_COMBOS = [(t, g, d) for t in TOPICS for g in TOPIC_GRADES[t] for d in DIFFICULTIES]


def _answer_text(problem) -> str:
    return ", ".join(format_fraction(v) for v in problem.answer)


@pytest.mark.parametrize("topic,grade,difficulty", ALL_COMBOS)
def test_same_seed_gives_same_problem(topic, grade, difficulty):
    assert generate(topic, grade, difficulty, 7) == generate(topic, grade, difficulty, 7)


@pytest.mark.parametrize("topic,grade,difficulty", ALL_COMBOS)
def test_id_round_trips(topic, grade, difficulty):
    problem = generate(topic, grade, difficulty, 123)
    assert parse_problem_id(problem.id) == (topic, grade, difficulty, 123)
    assert problem_from_id(problem.id) == problem


@pytest.mark.parametrize("topic,grade,difficulty", ALL_COMBOS)
def test_correct_answer_is_accepted(topic, grade, difficulty):
    for seed in range(25):
        problem = generate(topic, grade, difficulty, seed)
        assert check(problem, _answer_text(problem)).correct, problem


@pytest.mark.parametrize("topic,grade,difficulty", ALL_COMBOS)
def test_hints_never_state_the_final_answer(topic, grade, difficulty):
    for seed in range(50):
        problem = generate(topic, grade, difficulty, seed)
        assert len(problem.hints) == 3
        for value in problem.answer:
            shown = re.escape(format_fraction(value))
            for hint in problem.hints:
                # "x = 7", "= 7", "is 7" would all give the game away.
                assert not re.search(rf"(=|\bis)\s*{shown}(?![\d/%x])", hint), (
                    problem.id,
                    hint,
                )


@pytest.mark.parametrize("topic,grade,difficulty", ALL_COMBOS)
def test_wrong_answer_feedback_never_contains_answer(topic, grade, difficulty):
    for seed in range(25):
        problem = generate(topic, grade, difficulty, seed)
        result = check(problem, "999999")
        assert not result.correct
        for value in problem.answer:
            assert not re.search(
                rf"(?<![\d/]){re.escape(format_fraction(value))}(?![\d/])",
                result.feedback,
            )


def test_linear_answer_formats():
    problem = generate("linear_equations", 8, "medium", 42)  # 7x + 7 = 105
    assert check(problem, "14").correct
    assert check(problem, "x = 14").correct
    assert check(problem, " x=14.0 ").correct
    assert not check(problem, "x = -14").correct


def test_sign_error_gets_targeted_feedback():
    problem = generate("linear_equations", 8, "medium", 42)
    assert "sign" in check(problem, "-14").feedback.lower()


def test_fraction_added_tops_and_bottoms_is_diagnosed():
    for seed in range(200):
        problem = generate("fractions", 7, "medium", seed)
        if "+" in problem.statement:
            a, b, c, d = map(int, re.findall(r"\d+", problem.statement)[:4])
            wrong = Fraction(a + c, b + d)
            if wrong not in problem.answer:
                assert "denominators" in check(problem, format_fraction(wrong)).feedback
                return
    pytest.fail("no addition problem found")


def test_unsimplified_fraction_is_correct_but_nudged():
    problem = generate("fractions", 8, "easy", 42)  # 1/3 + 1/3 = 2/3
    result = check(problem, "4/6")
    assert result.correct
    assert "simplest form" in result.feedback


def test_quadratic_roots_any_order_and_partial():
    problem = generate("quadratics", 10, "medium", 42)  # x^2 - 2x - 15 = 0 -> 5, -3
    assert check(problem, "5, -3").correct
    assert check(problem, "x = -3 or x = 5").correct
    partial = check(problem, "5")
    assert not partial.correct and "one root" in partial.feedback.lower()
    assert "sign" in check(problem, "-5, 3").feedback.lower()


def test_quadratic_fraction_root():
    problem = generate("quadratics", 9, "hard", 42)  # 2x^2 + x - 10 = 0 -> -5/2, 2
    assert check(problem, "-5/2, 2").correct
    assert check(problem, "2, -2.5").correct


def test_unicode_minus_is_accepted():
    assert parse_numbers("x = \u22123") == [Fraction(-3)]


@pytest.mark.parametrize(
    "args,message",
    [
        (("quadratics", 7, "easy", 1), "not offered for Class 7"),
        (("fractions", 9, "easy", 1), "not offered for Class 9"),
        (("algebra", 8, "easy", 1), "Unknown topic"),
        (("linear_equations", 11, "easy", 1), "between 6 and 10"),
        (("linear_equations", 8, "extreme", 1), "Unknown difficulty"),
        (("linear_equations", 8, "easy", -1), "Seed"),
    ],
)
def test_invalid_requests_are_rejected(args, message):
    with pytest.raises(ProblemError, match=message):
        generate(*args)


@pytest.mark.parametrize(
    "bad_id",
    ["", "lin-8-medium-1", "lin-g11-easy-1", "xyz-g8-easy-1", "lin-g8-easy-1234567"],
)
def test_bad_problem_ids(bad_id):
    with pytest.raises(ProblemError, match="not a valid problem ID"):
        parse_problem_id(bad_id)


def test_answer_without_number():
    problem = generate("percentages", 8, "easy", 1)
    with pytest.raises(ProblemError, match="could not find a number"):
        check(problem, "no idea")


def test_zero_denominator():
    problem = generate("fractions", 7, "easy", 1)
    with pytest.raises(ProblemError, match="denominator"):
        check(problem, "3/0")


@pytest.mark.parametrize("seed", range(200))
def test_solution_steps_are_not_repeated(seed):
    for topic, grade, difficulty in ALL_COMBOS:
        steps = [s.strip() for s in generate(topic, grade, difficulty, seed).solution.split("→")]
        assert len(steps) == len(set(steps)), steps
