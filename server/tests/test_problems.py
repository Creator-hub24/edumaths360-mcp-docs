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
    parse_choice,
    parse_numbers,
    parse_problem_id,
    problem_from_id,
    topics_in_section,
)

ALL_COMBOS = [(t, d) for t in TOPICS for d in DIFFICULTIES]
NUMERIC_COMBOS = [(t, d) for t, d in ALL_COMBOS if TOPIC_SECTIONS[t] != "varc"]
VARC_COMBOS = [(t, d) for t, d in ALL_COMBOS if TOPIC_SECTIONS[t] == "varc"]


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


@pytest.mark.parametrize("topic,difficulty", NUMERIC_COMBOS)
def test_correct_answer_is_accepted(topic, difficulty):
    for seed in range(50):
        problem = generate(topic, difficulty, seed)
        assert check(problem, _answer_text(problem)).correct, problem


@pytest.mark.parametrize("topic,difficulty", NUMERIC_COMBOS)
def test_answers_are_exact_and_tidy(topic, difficulty):
    # Single answers are whole numbers or short decimals such as 37.5, never 16.666...
    for seed in range(50):
        problem = generate(topic, difficulty, seed)
        for value in problem.answer:
            if topic != "quadratics":
                assert value.denominator in (1, 2, 4, 5, 8), (problem.id, value)


@pytest.mark.parametrize("topic,difficulty", NUMERIC_COMBOS)
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


@pytest.mark.parametrize("topic,difficulty", NUMERIC_COMBOS)
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


@pytest.mark.parametrize("topic,difficulty", NUMERIC_COMBOS)
def test_common_mistakes_never_equal_the_answer(topic, difficulty):
    for seed in range(50):
        problem = generate(topic, difficulty, seed)
        assert not set(problem.mistakes) & set(problem.answer), problem.id


def test_sections_cover_every_topic():
    assert set(SECTIONS) == {"quant", "reasoning", "varc"}
    assert sorted(t for s in SECTIONS for t in topics_in_section(s)) == sorted(TOPICS)
    assert topics_in_section("reasoning") == ["number_series"]
    assert topics_in_section("varc") == ["para_jumbles", "odd_sentence_out", "para_summary"]


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


# --------------------------------------------------------------------- VARC


def _shingles(text: str, n: int = 5) -> set[str]:
    words = re.findall(r"[a-z']+", text.lower())
    return {" ".join(words[i : i + n]) for i in range(len(words) - n + 1)}


def _correct_text(problem) -> str:
    """The text a hint must never quote: the odd sentence or the correct option."""
    if problem.kind == "choice":
        return problem.choices[problem.key]
    if problem.kind == "pick":
        return re.search(rf"^{problem.key}\. (.*)$", problem.statement, re.MULTILINE).group(1)
    return ""


def test_varc_bank_has_enough_original_items():
    from edumaths360_mcp.varc_bank import ODD_SENTENCE_OUT, PARA_JUMBLES, PARA_SUMMARY

    for bank in (PARA_JUMBLES, ODD_SENTENCE_OUT, PARA_SUMMARY):
        assert set(bank) == set(DIFFICULTIES)
        assert sum(len(items) for items in bank.values()) >= 8
    texts = [s for items in PARA_JUMBLES.values() for item in items for s in item["sentences"]]
    assert len(texts) == len(set(texts))  # no sentence reused


@pytest.mark.parametrize("topic,difficulty", VARC_COMBOS)
def test_varc_correct_key_is_accepted(topic, difficulty):
    for seed in range(60):
        problem = generate(topic, difficulty, seed)
        assert problem.section == "varc" and problem.key
        assert check(problem, problem.key).correct, problem.id
        if problem.kind == "order":
            assert problem.key != "".join(sorted(problem.key))  # never shown already in order
            assert check(problem, "-".join(problem.key)).correct
            assert check(problem, " ".join(problem.key)).correct
        if problem.kind == "pick":
            assert check(problem, f"Sentence {problem.key}").correct
        if problem.kind == "choice":
            assert check(problem, f"({problem.key.lower()})").correct
            assert check(problem, f"Option {problem.key}").correct
            assert check(problem, problem.choices[problem.key]).correct
            assert check(problem, problem.choices[problem.key].upper().rstrip(".")).correct


@pytest.mark.parametrize("topic,difficulty", VARC_COMBOS)
def test_varc_wrong_answers_are_rejected_without_leaking(topic, difficulty):
    for seed in range(60):
        problem = generate(topic, difficulty, seed)
        if problem.kind == "order":
            wrong = ["".join(sorted(problem.key)), problem.key[::-1]]
        elif problem.kind == "pick":
            wrong = [str(i) for i in range(1, 6) if str(i) != problem.key]
        else:
            wrong = [letter for letter in "ABCD" if letter != problem.key]
        for answer in wrong:
            if answer == problem.key:
                continue
            result = check(problem, answer)
            assert not result.correct
            assert problem.key not in re.findall(r"[A-D1-9]+", result.feedback), (problem.id, result.feedback)
            assert not _shingles(_correct_text(problem)) & _shingles(result.feedback)


@pytest.mark.parametrize("topic,difficulty", VARC_COMBOS)
def test_varc_hints_never_reveal_or_narrow_to_the_answer(topic, difficulty):
    for seed in range(100):
        problem = generate(topic, difficulty, seed)
        assert len(problem.hints) == 3
        for hint in problem.hints:
            # No sentence numbers or option letters at all, so a hint cannot point at a label...
            assert not re.search(r"\d", hint), (problem.id, hint)
            assert not re.search(r"\b(option|sentence)\s+[A-D1-9]\b|\([A-Da-d]\)", hint, re.IGNORECASE)
            # ...and no quoting of the odd sentence or the correct option.
            assert not _shingles(_correct_text(problem)) & _shingles(hint), (problem.id, hint)


def test_varc_selection_is_repeatable_and_varied():
    assert generate("para_jumbles", "hard", 5) == generate("para_jumbles", "hard", 5)
    keys = {generate("odd_sentence_out", "easy", seed).key for seed in range(40)}
    assert len(keys) >= 4  # the odd sentence moves around
    statements = {generate("para_summary", "medium", seed).statement for seed in range(40)}
    assert len(statements) >= 6


def test_para_summary_distractor_feedback():
    problem = generate("para_summary", "medium", 42)  # museums passage, key B
    assert problem.key == "B"
    assert "only one detail" in check(problem, "A").feedback
    assert "further than the passage" in check(problem, "c").feedback
    assert "changes what the passage says" in check(problem, "option D").feedback


@pytest.mark.parametrize(
    "topic,answer,message",
    [
        ("para_jumbles", "123", "exactly once"),
        ("para_jumbles", "1124", "exactly once"),
        ("odd_sentence_out", "seven", "sentence number"),
        ("odd_sentence_out", "9", "sentence number"),
        ("para_summary", "E", "could not match"),
        ("para_summary", "something about ports", "could not match"),
    ],
)
def test_varc_unreadable_answers(topic, answer, message):
    with pytest.raises(ProblemError, match=message):
        check(generate(topic, "easy", 3), answer)


def test_parse_choice_formats():
    problem = generate("para_summary", "hard", 1)
    for text in ["B", "b", "(B)", "B)", "option b", "Answer is B"]:
        assert parse_choice(problem, text) == "B"
