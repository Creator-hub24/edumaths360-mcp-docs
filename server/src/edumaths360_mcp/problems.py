"""Deterministic maths problem generation and answer checking.

This module is pure Python with no MCP imports, so the maths logic can be
unit-tested on its own. The MCP layer lives in ``server.py``.

Design notes
------------
* A problem ID *is* the problem. ``lin-g8-medium-4821`` encodes the topic,
  grade, difficulty and random seed, so the server can rebuild the exact
  same problem from the ID alone. No database is needed and the answer never
  has to leave the server.
* Hints are written to guide, never to finish. They may show an intermediate
  step (for example ``3x = 21``) but never the final value.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from fractions import Fraction
from math import gcd, lcm
from typing import Literal, get_args

Topic = Literal["linear_equations", "fractions", "percentages", "quadratics"]
Difficulty = Literal["easy", "medium", "hard"]

TOPICS: tuple[str, ...] = get_args(Topic)
DIFFICULTIES: tuple[str, ...] = get_args(Difficulty)

TOPIC_CODES: dict[str, str] = {
    "linear_equations": "lin",
    "fractions": "frac",
    "percentages": "pct",
    "quadratics": "quad",
}
CODE_TOPICS: dict[str, str] = {code: topic for topic, code in TOPIC_CODES.items()}

#: Which grades (Classes) each topic is offered for.
TOPIC_GRADES: dict[str, tuple[int, ...]] = {
    "linear_equations": (6, 7, 8, 9, 10),
    "fractions": (6, 7, 8),
    "percentages": (6, 7, 8, 9, 10),
    "quadratics": (9, 10),
}

TOPIC_DESCRIPTIONS: dict[str, str] = {
    "linear_equations": "Solve equations in one variable, from x + b = c up to brackets on both sides.",
    "fractions": "Add, subtract and divide fractions, and give answers in simplest form.",
    "percentages": "Percentage of an amount, percentage increase/decrease, and reverse percentages.",
    "quadratics": "Solve quadratic equations by factorisation.",
}

MIN_GRADE, MAX_GRADE = 6, 10
MAX_SEED = 999_999
MAX_HINT_LEVEL = 3

PROBLEM_ID_PATTERN = r"^(lin|frac|pct|quad)-g([6-9]|10)-(easy|medium|hard)-(\d{1,6})$"
_PROBLEM_ID_RE = re.compile(PROBLEM_ID_PATTERN)
_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?(?:\s*/\s*\d+)?")


class ProblemError(ValueError):
    """Raised for invalid input. The message is safe to show to a student."""


@dataclass(frozen=True)
class Problem:
    id: str
    topic: str
    grade: int
    difficulty: str
    seed: int
    statement: str
    answer_format: str
    answer: tuple[Fraction, ...]
    hints: tuple[str, str, str]
    solution: str
    #: Predictable wrong answers mapped to targeted feedback.
    mistakes: dict[Fraction, str] = field(default_factory=dict)


# --------------------------------------------------------------------------- IDs


def make_problem_id(topic: str, grade: int, difficulty: str, seed: int) -> str:
    return f"{TOPIC_CODES[topic]}-g{grade}-{difficulty}-{seed}"


def parse_problem_id(problem_id: str) -> tuple[str, int, str, int]:
    match = _PROBLEM_ID_RE.match(problem_id.strip())
    if not match:
        raise ProblemError(
            f"'{problem_id}' is not a valid problem ID. "
            "IDs look like 'lin-g8-medium-4821'; get one from generate_problem."
        )
    code, grade, difficulty, seed = match.groups()
    return CODE_TOPICS[code], int(grade), difficulty, int(seed)


def validate_request(topic: str, grade: int, difficulty: str, seed: int) -> None:
    if topic not in TOPICS:
        raise ProblemError(f"Unknown topic '{topic}'. Choose one of: {', '.join(TOPICS)}.")
    if not MIN_GRADE <= grade <= MAX_GRADE:
        raise ProblemError(f"Grade must be between {MIN_GRADE} and {MAX_GRADE}; got {grade}.")
    if grade not in TOPIC_GRADES[topic]:
        offered = [t for t in TOPICS if grade in TOPIC_GRADES[t]]
        raise ProblemError(
            f"'{topic}' is not offered for Class {grade}. Topics for Class {grade}: {', '.join(offered)}."
        )
    if difficulty not in DIFFICULTIES:
        raise ProblemError(f"Unknown difficulty '{difficulty}'. Choose one of: {', '.join(DIFFICULTIES)}.")
    if not 0 <= seed <= MAX_SEED:
        raise ProblemError(f"Seed must be between 0 and {MAX_SEED}; got {seed}.")


# ------------------------------------------------------------------- formatting


def _signed(n: int) -> str:
    """Format ``+ 5`` / ``- 5`` for the middle of an expression."""
    return f"+ {n}" if n >= 0 else f"- {-n}"


def _coef(n: int, var: str) -> str:
    """Format a leading coefficient: 1x -> x, -1x -> -x."""
    if n == 1:
        return var
    if n == -1:
        return f"-{var}"
    return f"{n}{var}"


def _term(n: int, var: str) -> str:
    """Format a non-leading term such as ``- 5x`` or ``+ x``."""
    sign = "+" if n >= 0 else "-"
    mag = abs(n)
    return f"{sign} {var if mag == 1 else f'{mag}{var}'}"


def format_fraction(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _fmt_number(value: Fraction) -> str:
    return format_fraction(value) if value.denominator != 1 else str(value.numerator)


# ------------------------------------------------------------------- generators


def _linear(rng: random.Random, grade: int, difficulty: str) -> dict:
    big = grade >= 8
    if difficulty == "easy":
        x = rng.randint(2, 40 if big else 20)
        b = rng.randint(3, 50 if big else 30)
        c = x + b
        return dict(
            statement=f"Solve for x: x + {b} = {c}",
            answer=(Fraction(x),),
            hints=(
                f"The goal is to get x on its own. Which operation undoes '+ {b}'?",
                f"Subtract {b} from both sides. The left side becomes just x. What does the right side become?",
                f"Work out {c} - {b}. Then check: does your value make the original equation true?",
            ),
            solution=f"x + {b} = {c}  \u2192  x = {c} - {b}  \u2192  x = {x}",
            mistakes={Fraction(c + b): f"It looks like you added {b}. To undo '+ {b}', subtract it instead."},
        )
    if difficulty == "medium":
        a = rng.randint(2, 9)
        x = rng.choice([n for n in range(-10, 16) if n not in (0, 1)]) if grade >= 7 else rng.randint(2, 12)
        b = rng.randint(1, 20) * rng.choice([1, -1])
        c = a * x + b
        undo = "Subtract" if b > 0 else "Add"
        return dict(
            statement=f"Solve for x: {a}x {_signed(b)} = {c}",
            answer=(Fraction(x),),
            hints=(
                "Undo the operations in reverse order: deal with the number added or subtracted first, "
                "then the multiplication.",
                f"{undo} {abs(b)} {'from' if b > 0 else 'to'} both sides. You should get {a}x = {c - b}.",
                f"Now divide both sides by {a}. What is {c - b} \u00f7 {a}?",
            ),
            solution=f"{a}x {_signed(b)} = {c}  \u2192  {a}x = {c - b}  \u2192  x = {c - b} \u00f7 {a} = {x}",
            mistakes={
                Fraction(-x): "Check your signs: you have the right size of number but the wrong sign.",
                Fraction(c + b, a): f"Careful with the {_signed(b)}: you moved it across without changing its sign.",
            },
        )
    # hard: a(x + b) = cx + d, with brackets and x on both sides
    a = rng.randint(2, 6)
    c = rng.randint(1, a - 1)
    b = rng.randint(1, 9) * rng.choice([1, -1])
    x = rng.choice([n for n in range(-9, 13) if n not in (0, 1)])
    d = a * (x + b) - c * x
    left = f"{a}(x {_signed(b)})"
    right = f"{_coef(c, 'x')} {_signed(d)}"
    return dict(
        statement=f"Solve for x: {left} = {right}",
        answer=(Fraction(x),),
        hints=(
            f"Expand the bracket first: multiply {a} by each term inside it.",
            f"After expanding: {a}x {_signed(a * b)} = {right}. Collect the x terms on one side "
            "and the plain numbers on the other.",
            (
                f"You should reach {_coef(a - c, 'x')} = {d - a * b}. One more step finishes it."
                if a - c > 1
                else "Subtract the x term on the right from both sides. What is left on the right is your x."
            ),
        ),
        solution=(
            f"{left} = {right}  \u2192  {a}x {_signed(a * b)} = {right}  \u2192  "
            + (f"{a - c}x = {d - a * b}  \u2192  x = {x}" if a - c > 1 else f"x = {x}")
        ),
        mistakes={Fraction(-x): "Check your signs when you move terms across the equals sign."},
    )


def _fractions(rng: random.Random, grade: int, difficulty: str) -> dict:
    fmt = "a fraction in simplest form, for example 7/12 (a whole number such as 3 is fine)"
    if difficulty == "easy":
        d = rng.randint(3, 12)
        a = rng.randint(1, d - 1)
        b = rng.randint(1, d - 1)
        result = Fraction(a + b, d)
        return dict(
            statement=f"Work out {a}/{d} + {b}/{d}. Give your answer in simplest form.",
            answer_format=fmt,
            answer=(result,),
            hints=(
                f"The denominators are already the same ({d}), so every piece is the same size.",
                f"Add the numerators: {a} + {b}. Keep the denominator {d}.",
                "If the numerator and denominator share a common factor, divide both by it to simplify.",
            ),
            solution=f"{a}/{d} + {b}/{d} = {a + b}/{d} = {format_fraction(result)}",
            mistakes={Fraction(a + b, 2 * d): "Only add the numerators. The denominator stays the same."},
        )
    if difficulty == "medium":
        b, d = rng.sample(range(2, 13), 2)
        a = rng.randint(1, b - 1)
        c = rng.randint(1, d - 1)
        op = rng.choice(["+", "-"])
        first, second = Fraction(a, b), Fraction(c, d)
        if op == "-" and first < second:
            a, b, c, d = c, d, a, b
            first, second = second, first
        if op == "-" and first == second:
            op = "+"
        result = first + second if op == "+" else first - second
        m = lcm(b, d)
        word = "Add" if op == "+" else "Subtract"
        return dict(
            statement=f"Work out {a}/{b} {op} {c}/{d}. Give your answer in simplest form.",
            answer_format=fmt,
            answer=(result,),
            hints=(
                f"You can only {word.lower()} fractions when the denominators match. "
                f"What is the lowest common multiple (LCM) of {b} and {d}?",
                f"The LCM is {m}. Rewrite both fractions over {m}: "
                f"{a}/{b} = {a * m // b}/{m} and {c}/{d} = {c * m // d}/{m}.",
                f"{word} the new numerators, keep the denominator {m}, then simplify.",
            ),
            solution=(f"{a}/{b} {op} {c}/{d} = {a * m // b}/{m} {op} {c * m // d}/{m} = {format_fraction(result)}"),
            mistakes=(
                {
                    Fraction(a + c, b + d): (
                        "It looks like you added the numerators and the denominators separately. "
                        "Make the denominators the same first."
                    )
                }
                if op == "+"
                else {}
            ),
        )
    # hard: division of fractions
    b, d = rng.sample(range(2, 11), 2)
    a = rng.randint(1, 9)
    c = rng.randint(1, 9)
    while gcd(a, b) != 1:
        a += 1
    while gcd(c, d) != 1:
        c += 1
    result = Fraction(a, b) / Fraction(c, d)
    return dict(
        statement=f"Work out {a}/{b} \u00f7 {c}/{d}. Give your answer in simplest form.",
        answer_format=fmt,
        answer=(result,),
        hints=(
            "Dividing by a fraction is the same as multiplying by its reciprocal (flip it upside down).",
            f"Rewrite the division as {a}/{b} \u00d7 {d}/{c}.",
            "Multiply the numerators together and the denominators together, then simplify.",
        ),
        solution=f"{a}/{b} \u00f7 {c}/{d} = {a}/{b} \u00d7 {d}/{c} = {a * d}/{b * c} = {format_fraction(result)}",
        mistakes={
            Fraction(a, b)
            * Fraction(c, d): "You multiplied by the second fraction. Flip it (take the reciprocal) first.",
            1 / result: "You flipped the first fraction. Only the fraction you divide by gets flipped.",
        },
    )


def _percentages(rng: random.Random, grade: int, difficulty: str) -> dict:
    fmt = "a number, for example 45 (no % or currency sign needed)"
    big = grade >= 8
    if difficulty == "easy":
        p = rng.choice([5, 10, 15, 20, 25, 30, 40, 50, 60, 75])
        step = 100 // gcd(p, 100)
        n = step * rng.randint(2, 40 if big else 15)
        result = Fraction(p * n, 100)
        return dict(
            statement=f"What is {p}% of {n}?",
            answer_format=fmt,
            answer=(result,),
            hints=(
                f"'Per cent' means 'out of 100', so {p}% is the same as {p}/100.",
                f"Find 1% of {n} first ({n} \u00f7 100), or find 10% ({n} \u00f7 10), then scale up to {p}%.",
                f"Multiply: ({p} \u00f7 100) \u00d7 {n}.",
            ),
            solution=f"{p}% of {n} = {p}/100 \u00d7 {n} = {_fmt_number(result)}",
            mistakes={Fraction(n * 100, p): f"You divided by {p}% instead of multiplying by it."},
        )
    if difficulty == "medium":
        p = rng.choice([5, 10, 12, 15, 20, 25, 30, 40])
        step = 100 // gcd(p, 100)
        n = step * rng.randint(5 if big else 2, 60 if big else 20)
        change = Fraction(p * n, 100)
        rises = rng.random() < 0.5
        while n <= 100:  # keep prices realistic; n stays a multiple of step
            n *= 2
        change = Fraction(p * n, 100)
        item = rng.choice(["school bag", "geometry box", "water bottle", "lunch box", "cricket ball"])
        result = n + change if rises else n - change
        verb = "rises" if rises else "falls"
        return dict(
            statement=f"A {item} costs Rs {n}. Its price {verb} by {p}%. What is the new price in rupees?",
            answer_format=fmt,
            answer=(result,),
            hints=(
                f"Work out the change first, then {'add it to' if rises else 'subtract it from'} the original price.",
                f"The change is {p}% of Rs {n}.",
                f"Shortcut: the new price is {100 + p if rises else 100 - p}% of the original, "
                f"so multiply {n} by {100 + p if rises else 100 - p} and divide by 100.",
            ),
            solution=(
                f"Change = {p}% of {n} = {_fmt_number(change)}; new price = {n} "
                f"{'+' if rises else '-'} {_fmt_number(change)} = {_fmt_number(result)}"
            ),
            mistakes={
                change: f"That is the size of the change. Now {'add it to' if rises else 'subtract it from'} Rs {n}.",
                (n - change if rises else n + change): f"Check the direction: the price {verb}.",
            },
        )
    # hard: reverse percentage
    p = rng.choice([10, 20, 25, 40, 50])
    q = 100 - p
    step = 100 // gcd(q, 100)
    original = step * rng.randint(4 if big else 2, 40 if big else 20)
    while original < 200:
        original *= 2
    sale = Fraction(original * q, 100)
    return dict(
        statement=(
            f"After a {p}% discount, a school bag costs Rs {_fmt_number(sale)}. What was the original price in rupees?"
        ),
        answer_format=fmt,
        answer=(Fraction(original),),
        hints=(
            f"The sale price is not 100% of the original. After a {p}% discount, what percentage of the "
            "original price is left?",
            f"Rs {_fmt_number(sale)} is {q}% of the original price.",
            f"If {q}% is Rs {_fmt_number(sale)}, find 1% (divide by {q}), then multiply by 100.",
        ),
        solution=(
            f"{q}% of original = {_fmt_number(sale)}  \u2192  "
            f"original = {_fmt_number(sale)} \u00f7 {q} \u00d7 100 = {original}"
        ),
        mistakes={
            sale * Fraction(100 + p, 100): (
                f"You added {p}% of the sale price, but the discount was taken from the original price, "
                "which is a bigger number."
            )
        },
    )


def _quadratic_text(a: int, b: int, c: int) -> str:
    lead = "x\u00b2" if a == 1 else f"{a}x\u00b2"
    middle = f" {_term(b, 'x')}" if b else ""
    const = f" {_signed(c)}" if c else ""
    return f"{lead}{middle}{const} = 0"


def _factor_pairs(n: int) -> str:
    n = abs(n)
    pairs = [f"{i} \u00d7 {n // i}" for i in range(1, int(n**0.5) + 1) if n % i == 0]
    return ", ".join(pairs)


def _quadratics(rng: random.Random, grade: int, difficulty: str) -> dict:
    fmt = "both values of x separated by a comma, for example 2, -5 (fractions such as 3/2 are fine)"
    if difficulty in ("easy", "medium"):
        if difficulty == "easy":
            r1, r2 = rng.sample(range(1, 10), 2)
        else:
            choices = [n for n in range(-9, 10) if n != 0]
            r1, r2 = rng.sample(choices, 2)
            if r1 > 0 and r2 > 0:
                r2 = -r2
        b, c = -(r1 + r2), r1 * r2
        eq = _quadratic_text(1, b, c)
        return dict(
            statement=f"Solve {eq}. Give both values of x.",
            answer_format=fmt,
            answer=(Fraction(r1), Fraction(r2)),
            hints=(
                f"Look for two numbers that multiply to {c} and add up to {b}.",
                f"Factor pairs of {abs(c)} are {_factor_pairs(c)} (either number can be negative). "
                f"Which pair, with the right signs, adds up to {b}?",
                "Write the equation as (x + m)(x + n) = 0. If a product is zero, one of the factors "
                "must be zero, so set each bracket equal to 0 and solve.",
            ),
            solution=f"{eq}  \u2192  (x {_signed(-r1)})(x {_signed(-r2)}) = 0  \u2192  x = {r1} or x = {r2}",
            mistakes={},
        )
    # hard: leading coefficient p > 1, one fractional root
    p = rng.randint(2, 5)
    q = rng.choice([n for n in range(-9, 10) if n != 0 and gcd(abs(n), p) == 1])
    r = rng.choice([n for n in range(-8, 9) if n != 0])
    # (p x - q)(x - r) = 0  \u2192  roots q/p and r
    a, b, c = p, -(p * r + q), q * r
    eq = _quadratic_text(a, b, c)
    u, v = -p * r, -q  # split of the middle term: ux + vx
    return dict(
        statement=f"Solve {eq}. Give both values of x.",
        answer_format=fmt,
        answer=(Fraction(q, p), Fraction(r)),
        hints=(
            f"Multiply a \u00d7 c: {a} \u00d7 {c} = {a * c}. "
            f"Find two numbers that multiply to {a * c} and add up to {b}.",
            f"The two numbers are {u} and {v}. Split the middle term: {a}x\u00b2 {_term(u, 'x')} {_term(v, 'x')} "
            f"{_signed(c)} = 0, then factorise in pairs (grouping).",
            "You should end up with two brackets multiplied together equal to 0. Set each bracket to 0 "
            "and solve each small linear equation.",
        ),
        solution=(
            f"{eq}  \u2192  ({p}x {_signed(-q)})(x {_signed(-r)}) = 0  \u2192  "
            f"x = {format_fraction(Fraction(q, p))} or x = {r}"
        ),
        mistakes={},
    )


_GENERATORS = {
    "linear_equations": _linear,
    "fractions": _fractions,
    "percentages": _percentages,
    "quadratics": _quadratics,
}


def generate(topic: str, grade: int, difficulty: str, seed: int) -> Problem:
    """Build a problem. The same arguments always give the same problem."""
    validate_request(topic, grade, difficulty, seed)
    rng = random.Random(f"{topic}|{grade}|{difficulty}|{seed}")
    spec = _GENERATORS[topic](rng, grade, difficulty)
    spec.setdefault("answer_format", "a whole number, for example 7 or -3")
    # A "common mistake" value must never coincide with the real answer.
    spec["mistakes"] = {k: v for k, v in spec["mistakes"].items() if k not in spec["answer"]}
    return Problem(
        id=make_problem_id(topic, grade, difficulty, seed),
        topic=topic,
        grade=grade,
        difficulty=difficulty,
        seed=seed,
        **spec,
    )


def problem_from_id(problem_id: str) -> Problem:
    return generate(*parse_problem_id(problem_id))


# ------------------------------------------------------------------- checking


def parse_numbers(text: str) -> list[Fraction]:
    """Pull every number out of a free-text answer.

    Accepts ``7``, ``x = -3``, ``7/12``, ``2.5``, ``x = 2 or x = -3`` and the
    Unicode minus sign. Raises ProblemError if no number is found.
    """
    cleaned = text.replace("\u2212", "-").replace(",", " ")
    values: list[Fraction] = []
    for token in _NUMBER_RE.findall(cleaned):
        token = token.replace(" ", "")
        if "/" in token and token.split("/")[1].strip("0") == "":
            raise ProblemError("A fraction cannot have 0 as its denominator.")
        values.append(Fraction(token))
    if not values:
        raise ProblemError("I could not find a number in that answer.")
    return values


@dataclass(frozen=True)
class CheckResult:
    correct: bool
    feedback: str


def check(problem: Problem, answer_text: str) -> CheckResult:
    """Compare a student's answer with the stored answer. Never reveals the answer."""
    try:
        values = parse_numbers(answer_text)
    except ProblemError as exc:
        raise ProblemError(f"{exc} Expected format: {problem.answer_format}.") from exc

    if problem.topic == "quadratics":
        expected = set(problem.answer)
        given = set(values)
        if given == expected:
            return CheckResult(
                True,
                "Correct! Both roots are right. Substitute each one back in to see why.",
            )
        right = given & expected
        if right and len(given) < len(expected):
            return CheckResult(
                False,
                "One root is right. A quadratic like this has two roots; find the other one.",
            )
        if right:
            return CheckResult(
                False,
                "One of your roots is right, but the other is not. Check that bracket again.",
            )
        if {-v for v in given} == expected:
            return CheckResult(
                False,
                "Check your signs: if (x - 2) = 0 then x = 2, not -2. Re-read each bracket.",
            )
        return CheckResult(False, "Not quite. Try factorising again, or ask for a hint.")

    value = values[-1]  # "3x + 5 = 26 so x = 7" -> take the final number
    expected_value = problem.answer[0]
    if value == expected_value:
        note = ""
        if problem.topic == "fractions" and "/" in answer_text:
            num, _, den = answer_text.replace(" ", "").rpartition("/")
            num_digits = re.findall(r"-?\d+$", num)
            if num_digits and gcd(int(num_digits[0]), int(re.findall(r"^\d+", den)[0])) != 1:
                note = " Your value is right, but it is not in simplest form yet. Can you simplify it?"
        return CheckResult(True, "Correct! Well done." + note)
    if value in problem.mistakes:
        return CheckResult(False, problem.mistakes[value])
    return CheckResult(False, "Not quite. Re-check each step, or ask for a hint.")
