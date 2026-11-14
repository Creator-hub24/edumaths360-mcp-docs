"""Unit tests for the pure problem engine (no MCP involved)."""

import re
from fractions import Fraction

import pytest

from edumaths360_mcp.problems import (
    DIFFICULTIES,
    SECTIONS,
    TOPIC_SECTIONS,
    TOPICS,
    ProblemError,
    check,
    format_fraction,
    generate,
    parse_numbers,
    parse_problem_id,
    problem_from_id,
    topics_in_section,
)

ALL_COMBOS = [(t, d) for t in TOPICS for d in DIFFICULTIES]


def _answer_text(problem) -> str:
    return ", ".join(format_fraction(v) for v in problem.answer)


@pytest.mark.parametrize("topic,difficulty", ALL_COMBOS)
def test_same_seed_gives_same_problem(topic, difficulty):
    assert generate(topic, difficulty, 7) == generate(topic, difficulty, 7)


@pytest.mark.parametrize("topic,difficulty", ALL_COMBOS)
def test_id_round_trips(topic, difficulty):
    problem = generate(topic, difficulty, 123)
    assert parse_problem_id(problem.id) == (topic, difficulty, 123)
    assert problem_from_id(problem.id) == problem
    assert problem.section == TOPIC_SECTIONS[topic]


@pytest.mark.parametrize("topic,difficulty", ALL_COMBOS)
def test_correct_answer_is_accepted(topic, difficulty):
    for seed in range(50):
        problem = generate(topic, difficulty, seed)
        assert check(problem, _answer_text(problem)).correct, problem


@pytest.mark.parametrize("topic,difficulty", ALL_COMBOS)
def test_answers_are_exact_and_tidy(topic, difficulty):
    # Single answers are whole numbers or short decimals such as 37.5, never 16.666...
    for seed in range(50):
        problem = generate(topic, difficulty, seed)
        for value in problem.answer:
            if topic != "quadratics":
                assert value.denominator in (1, 2, 4, 5, 8), (problem.id, value)


@pytest.mark.parametrize("topic,difficulty", ALL_COMBOS)
def test_hints_never_state_the_final_answer(topic, difficulty):
    for seed in range(100):
        problem = generate(topic, difficulty, seed)
        assert len(problem.hints) == 3
        for value in problem.answer:
            shown = re.escape(format_fraction(value))
            for hint in problem.hints:
                # "x = 7", "= 7", "is 7" would all give the game away.
                assert not re.search(rf"(=|\bis)\s*{shown}(?![\d/%x])", hint), (
                    problem.id,
                    hint,
                )


@pytest.mark.parametrize("topic,difficulty", ALL_COMBOS)
def test_wrong_answer_feedback_never_contains_answer(topic, difficulty):
    for seed in range(25):
        problem = generate(topic, difficulty, seed)
        result = check(problem, "999999")
        assert not result.correct
        for value in problem.answer:
            assert not re.search(
                rf"(?<![\d/]){re.escape(format_fraction(value))}(?![\d/])",
                result.feedback,
            )


@pytest.mark.parametrize("topic,difficulty", ALL_COMBOS)
def test_common_mistakes_never_equal_the_answer(topic, difficulty):
    for seed in range(50):
        problem = generate(topic, difficulty, seed)
        assert not set(problem.mistakes) & set(problem.answer), problem.id


def test_sections_cover_every_topic():
    assert set(SECTIONS) == {"quant", "reasoning"}
    assert sorted(t for s in SECTIONS for t in topics_in_section(s)) == sorted(TOPICS)
    assert topics_in_section("reasoning") == ["number_series"]


def test_profit_loss_answer_formats():
    problem = generate("profit_loss", "hard", 42)  # sold at 800 for a 20% loss; gain 30% -> 1300
    assert check(problem, "1300").correct
    assert check(problem, "Rs 1,300").correct
    assert check(problem, "SP = Rs. 1300.0").correct
    assert not check(problem, "1040").correct


def test_percentage_base_error_gets_targeted_feedback():
    problem = generate("profit_loss", "hard", 42)
    assert "cost price" in check(problem, "1040").feedback  # 30% added to the old selling price


def test_indian_digit_grouping_is_accepted():
    assert parse_numbers("Rs 1,20,000") == [Fraction(120000)]
    assert parse_numbers("2, -5", thousands=False) == [Fraction(2), Fraction(-5)]


def test_decimal_answer():
    problem = generate("percentages", "hard", 2)  # price rises 60% -> cut consumption by 37.5%
    assert check(problem, "37.5%").correct
    assert check(problem, "75/2").correct


def test_linear_pair_y_value_is_diagnosed():
    problem = generate("linear_equations", "medium", 42)  # 2x + 7y = 71, 3x + 5y = 57 -> x = 4, y = 9
    assert check(problem, "x = 4").correct
    assert "value of y" in check(problem, "9").feedback
    assert "sign" in check(problem, "-4").feedback.lower()


def test_quadratic_roots_any_order_and_partial():
    problem = generate("quadratics", "medium", 42)  # x^2 + 3x - 54 = 0 -> -9, 6
    assert check(problem, "-9, 6").correct
    assert check(problem, "x = 6 or x = -9").correct
    partial = check(problem, "6")
    assert not partial.correct and "one root" in partial.feedback.lower()
    assert "sign" in check(problem, "9, -6").feedback.lower()


def test_quadratic_fraction_root():
    problem = generate("quadratics", "hard", 42)  # 4x^2 - 15x + 9 = 0 -> 3/4, 3
    assert check(problem, "3/4, 3").correct
    assert check(problem, "3, 0.75").correct


def test_series_and_units_digit():
    assert check(generate("number_series", "hard", 42), "129").correct  # 5, 9, 17, 33, 65, ?
    units = generate("number_system", "medium", 42)  # units digit of 47^975
    assert check(units, str(pow(47, 975, 10))).correct


def test_unicode_minus_is_accepted():
    assert parse_numbers("x = \u22123") == [Fraction(-3)]


@pytest.mark.parametrize(
    "args,message",
    [
        (("algebra", "easy", 1), "Unknown topic"),
        (("percentages", "extreme", 1), "Unknown difficulty"),
        (("percentages", "easy", -1), "Seed"),
        (("percentages", "easy", 1_000_000), "Seed"),
    ],
)
def test_invalid_requests_are_rejected(args, message):
    with pytest.raises(ProblemError, match=message):
        generate(*args)


@pytest.mark.parametrize(
    "bad_id",
    ["", "pct-g8-medium-1", "pct-1", "xyz-easy-1", "pct-easy-1234567", "pct-extreme-1"],
)
def test_bad_problem_ids(bad_id):
    with pytest.raises(ProblemError, match="not a valid problem ID"):
        parse_problem_id(bad_id)


def test_answer_without_number():
    problem = generate("percentages", "easy", 1)
    with pytest.raises(ProblemError, match="could not find a number"):
        check(problem, "no idea")


def test_zero_denominator():
    problem = generate("ratio_proportion", "easy", 1)
    with pytest.raises(ProblemError, match="denominator"):
        check(problem, "3/0")


@pytest.mark.parametrize("seed", range(200))
def test_solution_steps_are_not_repeated(seed):
    for topic, difficulty in ALL_COMBOS:
        steps = [s.strip() for s in generate(topic, difficulty, seed).solution.split("→")]
        assert len(steps) == len(set(steps)), steps
