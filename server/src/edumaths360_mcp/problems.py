"""Deterministic quantitative-aptitude and reasoning problems, with answer checking.

This module is pure Python with no MCP imports, so the maths logic can be
unit-tested on its own. The MCP layer lives in ``server.py``.

The topics follow what CAT, other MBA entrance tests and similar competitive
exams ask in their quantitative aptitude (arithmetic, algebra, number system)
and logical reasoning sections.

Design notes
------------
* A problem ID *is* the problem. ``tsd-medium-4821`` encodes the topic,
  difficulty and random seed, so the server can rebuild the exact same problem
  from the ID alone. No database is needed and the answer never has to leave
  the server.
* Hints are written to guide, never to finish. They may show an intermediate
  step (for example the cost price before the final selling price) but never
  the final value.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from fractions import Fraction
from functools import cache
from math import gcd, lcm, prod
from typing import Literal, get_args

Topic = Literal[
    "percentages",
    "profit_loss",
    "ratio_proportion",
    "time_speed_distance",
    "time_work",
    "interest",
    "linear_equations",
    "quadratics",
    "number_system",
    "number_series",
]
Difficulty = Literal["easy", "medium", "hard"]
Section = Literal["quant", "reasoning"]

TOPICS: tuple[str, ...] = get_args(Topic)
DIFFICULTIES: tuple[str, ...] = get_args(Difficulty)
SECTIONS: tuple[str, ...] = get_args(Section)

TOPIC_CODES: dict[str, str] = {
    "percentages": "pct",
    "profit_loss": "pl",
    "ratio_proportion": "ratio",
    "time_speed_distance": "tsd",
    "time_work": "work",
    "interest": "int",
    "linear_equations": "lin",
    "quadratics": "quad",
    "number_system": "num",
    "number_series": "series",
}
CODE_TOPICS: dict[str, str] = {code: topic for topic, code in TOPIC_CODES.items()}

#: Exam section and area for each topic.
TOPIC_SECTIONS: dict[str, str] = {
    "percentages": "quant",
    "profit_loss": "quant",
    "ratio_proportion": "quant",
    "time_speed_distance": "quant",
    "time_work": "quant",
    "interest": "quant",
    "linear_equations": "quant",
    "quadratics": "quant",
    "number_system": "quant",
    "number_series": "reasoning",
}
TOPIC_AREAS: dict[str, str] = {
    "percentages": "arithmetic",
    "profit_loss": "arithmetic",
    "ratio_proportion": "arithmetic",
    "time_speed_distance": "arithmetic",
    "time_work": "arithmetic",
    "interest": "arithmetic",
    "linear_equations": "algebra",
    "quadratics": "algebra",
    "number_system": "number system",
    "number_series": "logical reasoning",
}
#: Plain-English names for prose, for example in the tutor prompt.
TOPIC_LABELS: dict[str, str] = {
    "percentages": "percentages",
    "profit_loss": "profit and loss",
    "ratio_proportion": "ratio and proportion",
    "time_speed_distance": "time, speed and distance",
    "time_work": "time and work",
    "interest": "simple and compound interest",
    "linear_equations": "linear equations",
    "quadratics": "quadratic equations",
    "number_system": "number system",
    "number_series": "number series",
}
SECTION_DESCRIPTIONS: dict[str, str] = {
    "quant": "Quantitative aptitude: arithmetic, algebra and number system.",
    "reasoning": "Logical reasoning: pattern-based items with one verifiable numeric answer.",
}
TOPIC_DESCRIPTIONS: dict[str, str] = {
    "percentages": "Percentage of a quantity, successive percentage change, and price-consumption problems.",
    "profit_loss": "Cost price, selling price, marked price and discount, and profit or loss percentages.",
    "ratio_proportion": "Dividing in a ratio, combining ratios, and mixtures.",
    "time_speed_distance": "Trains, unit conversion, average speed and relative speed.",
    "time_work": "Working together, finding one person's rate, and pipes and cisterns.",
    "interest": "Simple interest, compound interest, and the CI - SI difference.",
    "linear_equations": "Word problems and pairs of linear equations in two variables.",
    "quadratics": "Solve quadratic equations by factorisation.",
    "number_system": "HCF and LCM, units digits of powers, and counting factors.",
    "number_series": "Find the next term: arithmetic, geometric, difference and mixed series.",
}

MAX_SEED = 999_999
MAX_HINT_LEVEL = 3

PROBLEM_ID_PATTERN = r"^(pct|pl|ratio|tsd|work|int|lin|quad|num|series)-(easy|medium|hard)-(\d{1,6})$"
_PROBLEM_ID_RE = re.compile(PROBLEM_ID_PATTERN)
_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?(?:\s*/\s*\d+)?")
_THOUSANDS_RE = re.compile(r"(?<=\d),(?=\d{2,3}(?!\d))")

_TIMES = " \u00d7 "

DEFAULT_FORMAT = "a number, for example 450 (no units, % or Rs sign needed)"


class ProblemError(ValueError):
    """Raised for invalid input. The message is safe to show to a student."""


@dataclass(frozen=True)
class Problem:
    id: str
    topic: str
    section: str
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


def make_problem_id(topic: str, difficulty: str, seed: int) -> str:
    return f"{TOPIC_CODES[topic]}-{difficulty}-{seed}"


def parse_problem_id(problem_id: str) -> tuple[str, str, int]:
    match = _PROBLEM_ID_RE.match(problem_id.strip())
    if not match:
        raise ProblemError(
            f"'{problem_id}' is not a valid problem ID. IDs look like 'tsd-medium-4821'; get one from generate_problem."
        )
    code, difficulty, seed = match.groups()
    return CODE_TOPICS[code], difficulty, int(seed)


def validate_request(topic: str, difficulty: str, seed: int) -> None:
    if topic not in TOPICS:
        raise ProblemError(f"Unknown topic '{topic}'. Choose one of: {', '.join(TOPICS)}.")
    if difficulty not in DIFFICULTIES:
        raise ProblemError(f"Unknown difficulty '{difficulty}'. Choose one of: {', '.join(DIFFICULTIES)}.")
    if not 0 <= seed <= MAX_SEED:
        raise ProblemError(f"Seed must be between 0 and {MAX_SEED}; got {seed}.")


def topics_in_section(section: str) -> list[str]:
    return [t for t in TOPICS if TOPIC_SECTIONS[t] == section]


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


def _dec(value: Fraction) -> str:
    """Show a value as a whole number or short decimal when it terminates (37.5), else as a fraction."""
    if value.denominator == 1:
        return str(value.numerator)
    for places in range(1, 4):
        scaled = value * 10**places
        if scaled.denominator == 1:
            text = f"{abs(scaled.numerator):0{places + 1}d}"
            sign = "-" if value < 0 else ""
            return f"{sign}{text[:-places]}.{text[-places:]}"
    return format_fraction(value)


def _factorise(n: int) -> str:
    sup = str.maketrans("0123456789", "\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079")
    parts, p = [], 2
    while p * p <= n:
        e = 0
        while n % p == 0:
            n //= p
            e += 1
        if e:
            parts.append(f"{p}{str(e).translate(sup) if e > 1 else ''}")
        p += 1
    if n > 1:
        parts.append(str(n))
    return " \u00d7 ".join(parts)


# ------------------------------------------------------------------- generators
#
# Each generator returns a dict with statement, answer, hints, solution and
# mistakes (plus answer_format when the default does not fit). Numbers are
# chosen so that every answer is exact.


def _percentages(rng: random.Random, difficulty: str) -> dict:
    if difficulty == "easy":
        p = rng.choice([5, 8, 12, 15, 16, 20, 24, 25, 35, 40, 45, 60, 75])
        step = 100 // gcd(p, 100)
        n = step * rng.randint(max(2, 200 // step), max(10, 5000 // step))
        result = Fraction(p * n, 100)
        return dict(
            statement=f"What is {p}% of {n}?",
            answer=(result,),
            hints=(
                f"'Per cent' means 'out of 100', so {p}% is the same as {p}/100.",
                f"Find 1% of {n} first ({n} \u00f7 100), or 10% ({n} \u00f7 10), then scale up to {p}%.",
                f"Multiply: ({p} \u00f7 100) \u00d7 {n}.",
            ),
            solution=f"{p}% of {n} = {p}/100 \u00d7 {n} = {_dec(result)}",
            mistakes={Fraction(n * 100, p): f"You divided by {p}% instead of multiplying by it."},
        )
    if difficulty == "medium":
        a = rng.choice([10, 20, 25, 30, 50])
        b = rng.choice([10, 20, 25, 40])
        candidates = [n for n in range(200, 10_001, 100) if n * (100 + a) * (100 - b) % 10_000 == 0]
        n = rng.choice(candidates)
        mid = n * (100 + a) // 100
        final = mid * (100 - b) // 100
        item = rng.choice(["laptop", "smartphone", "scooter", "television", "refrigerator"])
        return dict(
            statement=(
                f"The price of a {item} is Rs {n}. It is first increased by {a}%, and then the new price is "
                f"decreased by {b}%. What is the final price in rupees?"
            ),
            answer=(Fraction(final),),
            hints=(
                f"The second percentage is taken on the new price, not on the original Rs {n}.",
                f"After the {a}% increase, the price becomes Rs {mid}.",
                f"Now take {b}% off Rs {mid}: multiply by {100 - b} and divide by 100.",
            ),
            solution=f"{n} \u00d7 {100 + a}/100 = {mid}  \u2192  {mid} \u00d7 {100 - b}/100 = {final}",
            mistakes={
                Fraction(n * (100 + a - b), 100): (
                    "You combined the two percentages directly. The decrease is taken on the increased price, "
                    "so apply the changes one after the other."
                ),
                Fraction(mid): "That is the price after the increase only. Now apply the decrease.",
            },
        )
    # hard: price rise and consumption cut
    p = rng.choice([25, 60, 100, 150, 300, 400, 900])
    item = rng.choice(["sugar", "petrol", "cooking oil", "rice", "milk"])
    cut = Fraction(100 * p, 100 + p)
    return dict(
        statement=(
            f"The price of {item} rises by {p}%. By what percentage must a family reduce its consumption "
            f"so that its spending on {item} stays the same?"
        ),
        answer_format="a number without the % sign, for example 20 or 37.5",
        answer=(cut,),
        hints=(
            "Spending = price \u00d7 quantity. If spending stays fixed and the price goes up, the quantity "
            "must go down.",
            f"The new price is {100 + p}/100 of the old price, so the new quantity must be 100/{100 + p} "
            "of the old quantity.",
            "The cut is the drop in quantity as a share of the old quantity: (1 - new/old) \u00d7 100.",
        ),
        solution=(
            f"New quantity = 100/{100 + p} of old  \u2192  cut = {p}/{100 + p} \u00d7 100  \u2192  cut = {_dec(cut)}%"
        ),
        mistakes={
            Fraction(p): (
                "Cutting by the same percentage as the price rise is too much: the rise is measured on the old "
                "price, but the cut is measured on the old quantity. Compare old and new prices instead."
            )
        },
    )


def _profit_loss(rng: random.Random, difficulty: str) -> dict:
    if difficulty == "easy":
        p = rng.choice([5, 10, 12, 15, 20, 25, 30, 40])
        cp = rng.choice([c for c in range(100, 5001, 20) if c * p % 100 == 0])
        change = cp * p // 100
        gain = rng.random() < 0.6
        sp = cp + change if gain else cp - change
        word = "profit" if gain else "loss"
        return dict(
            statement=(
                f"A shopkeeper buys an article for Rs {cp} and sells it at a {word} of {p}%. "
                "What is the selling price in rupees?"
            ),
            answer=(Fraction(sp),),
            hints=(
                f"Profit and loss percentages are always worked out on the cost price, Rs {cp}.",
                f"The {word} is {p}% of Rs {cp}.",
                f"Selling price = cost price {'+ profit' if gain else '- loss'}, or directly "
                f"{100 + p if gain else 100 - p}% of the cost price.",
            ),
            solution=f"{word.capitalize()} = {p}% of {cp} = {change}  \u2192  SP = {cp} {'+' if gain else '-'} "
            f"{change} = {sp}",
            mistakes={
                Fraction(change): f"That is the {word} itself. Now {'add it to' if gain else 'subtract it from'} "
                "the cost price.",
                Fraction(cp - change if gain else cp + change): (
                    f"Check the direction: a {word} means the selling price is "
                    f"{'more' if gain else 'less'} than the cost price."
                ),
            },
        )
    if difficulty == "medium":
        p = rng.choice([8, 10, 12, 20, 25, 50])
        d = rng.choice([4, 10, 20, 25, 40])
        cp = rng.choice([c for c in range(200, 20_001, 100) if c * (100 + p) % (100 * (100 - d)) == 0])
        sp = cp * (100 + p) // 100
        mp = sp * 100 // (100 - d)
        return dict(
            statement=(
                f"A trader buys an article for Rs {cp}. He wants a profit of {p}% even after giving a discount "
                f"of {d}% on the marked price. What should the marked price be, in rupees?"
            ),
            answer=(Fraction(mp),),
            hints=(
                "Work backwards: first find the selling price that gives the required profit.",
                f"The selling price must be {100 + p}% of Rs {cp}, which comes to Rs {sp}.",
                f"After a {d}% discount the customer pays {100 - d}% of the marked price. So Rs {sp} is "
                f"{100 - d}% of the marked price; scale it up to 100%.",
            ),
            solution=f"SP = {cp} \u00d7 {100 + p}/100 = {sp}  \u2192  MP = {sp} \u00d7 100/{100 - d} = {mp}",
            mistakes={
                Fraction(cp * (100 + p + d), 100): (
                    "Adding the discount % to the profit % does not work: the discount is taken on the "
                    "marked price, not on the cost price."
                ),
                Fraction(sp * (100 + d), 100): (
                    "The discount is a percentage of the marked price, so you cannot add it back as a "
                    "percentage of the selling price."
                ),
                Fraction(sp): (
                    "That is the selling price. The marked price is higher, because the discount comes off it."
                ),
            },
        )
    # hard: selling price at a loss, find the price for a gain
    loss = rng.choice([5, 10, 15, 20, 25])
    g = rng.choice([5, 10, 15, 20, 25, 30])
    cp = rng.randrange(200, 5001, 100)
    s1 = cp * (100 - loss) // 100
    target = cp * (100 + g) // 100
    return dict(
        statement=(
            f"By selling an article for Rs {s1}, a trader loses {loss}%. At what price, in rupees, should "
            f"he sell it to gain {g}%?"
        ),
        answer=(Fraction(target),),
        hints=(
            f"Find the cost price first. A loss of {loss}% means Rs {s1} is {100 - loss}% of the cost price.",
            f"To get the cost price, divide Rs {s1} by {100 - loss} and multiply by 100.",
            f"Now find {100 + g}% of that cost price.",
        ),
        solution=f"CP = {s1} \u00d7 100/{100 - loss} = {cp}  \u2192  new SP = {cp} \u00d7 {100 + g}/100 = {target}",
        mistakes={
            Fraction(s1 * (100 + g), 100): "The gain % is worked out on the cost price, not on the old selling price.",
            Fraction(s1 * (100 + loss + g), 100): (
                "Percentages of different amounts cannot simply be added. Find the cost price first."
            ),
            Fraction(cp): "That is the cost price. Now add the gain.",
        },
    )


def _ratio(rng: random.Random, difficulty: str) -> dict:
    if difficulty == "easy":
        a, b = rng.sample(range(1, 10), 2)
        g = gcd(a, b)
        a, b = a // g, b // g
        k = rng.randint(20, 500)
        total = (a + b) * k
        return dict(
            statement=f"Rs {total} is divided between P and Q in the ratio {a}:{b}. How much does P get, in rupees?",
            answer=(Fraction(a * k),),
            hints=(
                f"Add the ratio parts: the money is split into {a} + {b} equal parts.",
                f"One part is worth Rs {total} \u00f7 {a + b}.",
                f"P gets {a} of those parts.",
            ),
            solution=f"One part = {total} \u00f7 {a + b} = {k}  \u2192  P = {a} \u00d7 {k} = {a * k}",
            mistakes={
                Fraction(b * k): f"That is Q's share. P's part of the ratio is {a}.",
                Fraction(total * a, b): "Divide by the total number of parts, not by Q's part.",
            },
        )
    if difficulty == "medium":
        a1, b1 = rng.sample(range(1, 10), 2)
        b2, c2 = rng.sample(range(1, 10), 2)
        a1, b1 = a1 // gcd(a1, b1), b1 // gcd(a1, b1)
        b2, c2 = b2 // gcd(b2, c2), c2 // gcd(b2, c2)
        m = lcm(b1, b2)
        big_a, big_b, big_c = a1 * m // b1, m, c2 * m // b2
        g = gcd(gcd(big_a, big_b), big_c)
        big_a, big_b, big_c = big_a // g, big_b // g, big_c // g
        s = big_a + big_b + big_c
        k = rng.randint(10, 300)
        total = s * k
        return dict(
            statement=(
                f"A, B and C share Rs {total}. A:B = {a1}:{b1} and B:C = {b2}:{c2}. What is C's share, in rupees?"
            ),
            answer=(Fraction(big_c * k),),
            hints=(
                "B appears in both ratios. Rewrite them so that B has the same number in each.",
                (
                    f"Scale both ratios so that B becomes {m} (the LCM of {b1} and {b2}), "
                    "then write A:B:C as one ratio."
                    if b1 != b2
                    else f"B already has the same number, {b1}, in both ratios, so write A:B:C as one ratio."
                ),
                "Add the three parts of A:B:C, find the value of one part, then multiply by C's parts.",
            ),
            solution=(
                f"A:B:C = {big_a}:{big_b}:{big_c}  \u2192  one part = {total} \u00f7 {s} = {k}  \u2192  "
                f"C = {big_c} \u00d7 {k} = {big_c * k}"
            ),
            mistakes={
                Fraction(big_a * k): "That is A's share. Check which part of A:B:C belongs to C.",
                Fraction(big_b * k): "That is B's share. Check which part of A:B:C belongs to C.",
            },
        )
    # hard: adding water to a mixture
    m = rng.randint(2, 9)
    w = rng.choice([n for n in range(1, m + 3) if gcd(n, m) == 1])
    w2 = rng.choice([n for n in range(w + 1, w + 7) if gcd(n, m) == 1])
    k = rng.randint(2, 20)
    litres = (m + w) * k
    added = (w2 - w) * k
    return dict(
        statement=(
            f"A {litres}-litre mixture contains milk and water in the ratio {m}:{w}. How many litres of water "
            f"must be added to make the ratio {m}:{w2}?"
        ),
        answer=(Fraction(added),),
        hints=(
            "Adding water does not change the amount of milk. Start by finding how much milk there is.",
            f"Milk is {m}/{m + w} of the mixture and water is {w}/{m + w} of it.",
            f"In the new mixture, water must be {w2}/{m} times the milk. Compare that with the water already there.",
        ),
        solution=(
            f"Milk = {litres} \u00d7 {m}/{m + w} = {m * k} L, water = {w * k} L  \u2192  "
            f"water needed = {m * k} \u00d7 {w2}/{m} = {w2 * k} L  \u2192  add {w2 * k} - {w * k} = {added} L"
        ),
        mistakes={
            Fraction(w2 * k): "That is the total water needed. Subtract the water already in the mixture.",
            Fraction(w2 - w): "That is the difference in ratio parts. Find how many litres one part is worth.",
        },
    )


@cache
def _harmonic_pairs() -> tuple[tuple[int, int], ...]:
    """Pairs (x, y), x < y, where 2xy / (x + y) and xy / (x + y) are whole numbers."""
    return tuple((x, y) for x in range(4, 91) for y in range(x + 1, 181) if (x * y) % (x + y) == 0)


@cache
def _pipe_triples() -> tuple[tuple[int, int, int], ...]:
    """(a, b, c): fill pipes a, b and empty pipe c give a whole number of hours."""
    triples = []
    for a in range(2, 25):
        for b in range(a + 1, 31):
            for c in range(2, 61):
                if c in (a, b):
                    continue
                net = Fraction(1, a) + Fraction(1, b) - Fraction(1, c)
                if net > 0 and (1 / net).denominator == 1 and 1 / net <= 120:
                    triples.append((a, b, c))
    return tuple(triples)


def _time_speed_distance(rng: random.Random, difficulty: str) -> dict:
    if difficulty == "easy":
        speed = rng.choice([36, 54, 72, 90, 108, 126, 144])
        v = speed * 5 // 18
        t = rng.choice([n for n in range(5, 61) if 100 <= v * n <= 600])
        length = v * t
        return dict(
            statement=f"A train {length} m long is running at {speed} km/h. How many seconds does it take to pass "
            "a signal pole?",
            answer=(Fraction(t),),
            hints=(
                "To pass a pole, the train must cover a distance equal to its own length.",
                "Work in metres and seconds. To convert km/h to m/s, multiply by 5/18.",
                f"{speed} km/h works out to {v} m/s. Time = distance \u00f7 speed.",
            ),
            solution=f"{speed} \u00d7 5/18 = {v} m/s  \u2192  time = {length} \u00f7 {v} = {t} s",
            mistakes={
                Fraction(length, speed): "Check the units: the length is in metres but the speed is in km/h. "
                "Convert the speed first."
            },
        )
    if difficulty == "medium":
        x, y = rng.choice([(a, b) for a, b in _harmonic_pairs() if a >= 20 and b <= 3 * a and b <= 120])
        if rng.random() < 0.5:
            x, y = y, x
        avg = Fraction(2 * x * y, x + y)
        vehicle = rng.choice(["car", "bus", "motorbike", "delivery van"])
        return dict(
            statement=(
                f"A {vehicle} travels from town P to town Q at {x} km/h and returns along the same road at "
                f"{y} km/h. What is the average speed for the whole trip, in km/h?"
            ),
            answer=(avg,),
            hints=(
                "Average speed is total distance \u00f7 total time. It is not the average of the two speeds.",
                f"Pick a convenient one-way distance, such as {lcm(x, y)} km (the LCM of {x} and {y}), and work "
                "out the time for each leg.",
                "The total distance is twice the one-way distance. Divide it by the total time. "
                "(For equal distances the shortcut is 2xy \u00f7 (x + y).)",
            ),
            solution=f"Average = 2 \u00d7 {x} \u00d7 {y} \u00f7 ({x} + {y})  \u2192  {2 * x * y} \u00f7 {x + y} "
            f"= {_dec(avg)} km/h",
            mistakes={
                Fraction(x + y, 2): "That is the simple average of the two speeds. More time is spent at the "
                "slower speed, so the true average is lower."
            },
        )
    # hard: two trains crossing each other
    opposite = rng.random() < 0.5
    if opposite:
        rel = rng.choice([72, 90, 108, 126, 144, 162, 180])
        s2 = rng.randint(30, rel - 30)
        s1 = rel - s2
    else:
        rel = rng.choice([18, 36, 54, 72])
        s2 = rng.randint(30, 80)
        s1 = s2 + rel
    v = rel * 5 // 18
    t = rng.choice([n for n in range(5, 200) if 150 <= v * n <= 800])
    total = v * t
    l1 = rng.randrange(60, total - 59, 5)
    l2 = total - l1
    other = s1 - s2 if opposite else s1 + s2
    direction = "opposite directions" if opposite else "the same direction"
    return dict(
        statement=(
            f"Two trains, {l1} m and {l2} m long, run on parallel tracks in {direction} at {s1} km/h and "
            f"{s2} km/h. How many seconds do they take to cross each other completely?"
        ),
        answer=(Fraction(t),),
        hints=(
            "Think about relative speed: how fast does one train move as seen from the other?",
            f"In opposite directions the speeds add; in the same direction they subtract. The distance to cover "
            f"is both lengths together, {l1} + {l2} m.",
            "Convert the relative speed to m/s by multiplying by 5/18, then time = distance \u00f7 speed.",
        ),
        solution=(
            f"Relative speed = {s1} {'+' if opposite else '-'} {s2} = {rel} km/h  \u2192  "
            f"{rel} \u00d7 5/18 = {v} m/s  \u2192  time = {total} \u00f7 {v} = {t} s"
        ),
        mistakes={
            Fraction(l1 * 18, rel * 5): "Crossing completely means covering both trains' lengths, not just one.",
            **(
                {
                    Fraction(total * 18, other * 5): (
                        "Check the relative speed: trains in opposite directions add their speeds, trains in "
                        "the same direction subtract them."
                    )
                }
                if other
                else {}
            ),
        },
    )


def _time_work(rng: random.Random, difficulty: str) -> dict:
    if difficulty == "easy":
        a, b = rng.choice([p for p in _harmonic_pairs() if p[1] <= 90])
        t = a * b // (a + b)
        units = lcm(a, b)
        return dict(
            statement=(
                f"A can finish a piece of work in {a} days and B can finish it in {b} days. Working together, "
                "how many days will they take?"
            ),
            answer=(Fraction(t),),
            hints=(
                f"Think in work per day: A does 1/{a} of the job each day and B does 1/{b}.",
                f"Take the total work as {units} units (the LCM of {a} and {b}). How many units does each "
                "person do per day?",
                "Add their daily units, then divide the total work by that.",
            ),
            solution=(
                f"Total work = {units} units  \u2192  A does {units // a}/day, B does {units // b}/day  \u2192  "
                f"days = {units} \u00f7 {units // a + units // b} = {t}"
            ),
            mistakes={
                Fraction(a + b, 2): "Averaging the days does not work: together they must be faster than the "
                "faster person alone.",
                Fraction(a + b): (
                    "Adding the days would mean they work one after the other. Working together is faster."
                ),
            },
        )
    if difficulty == "medium":
        a, b = rng.choice([p for p in _harmonic_pairs() if p[1] <= 90])
        t = a * b // (a + b)
        known, unknown = (a, b) if rng.random() < 0.5 else (b, a)
        units = lcm(t, known)
        b_rate = units // t - units // known
        return dict(
            statement=(
                f"A and B together can finish a job in {t} days. A alone can finish it in {known} days. "
                "How many days would B take alone?"
            ),
            answer=(Fraction(unknown),),
            hints=(
                "Daily work adds up: A's daily work + B's daily work = their combined daily work.",
                f"Take the total work as {units} units (the LCM of {t} and {known}). Work out the units per day "
                "for the pair and for A.",
                "B's daily units are the difference. Divide the total work by B's daily units.",
            ),
            solution=(
                f"Total work = {units} units  \u2192  together {units // t}/day, A {units // known}/day  \u2192  "
                f"B does {b_rate}/day  \u2192  B alone = {units} \u00f7 {b_rate} = {unknown} days"
            ),
            mistakes={
                Fraction(known - t): "Subtracting days does not work. Subtract the work done per day instead.",
            },
        )
    # hard: pipes and cisterns
    a, b, c = rng.choice(_pipe_triples())
    units = lcm(a, b, c)
    net = units // a + units // b - units // c
    hours = units // net
    return dict(
        statement=(
            f"Pipes A and B can fill a tank in {a} hours and {b} hours respectively. Pipe C can empty the full "
            f"tank in {c} hours. If all three are opened together on an empty tank, how many hours will it take "
            "to fill?"
        ),
        answer=(Fraction(hours),),
        hints=(
            "Filling pipes add water every hour; the emptying pipe takes some away.",
            f"Take the tank as {units} units (the LCM of {a}, {b} and {c}). A adds {units // a}, B adds "
            f"{units // b} and C removes {units // c} units each hour.",
            "Find the net units filled per hour, then divide the size of the tank by it.",
        ),
        solution=(
            f"Tank = {units} units  \u2192  net per hour = {units // a} + {units // b} - {units // c} = {net}  "
            f"\u2192  time = {units} \u00f7 {net} = {hours} hours"
        ),
        mistakes={
            Fraction(a * b, a + b): "You left out pipe C, which is emptying the tank.",
            1 / (Fraction(1, a) + Fraction(1, b) + Fraction(1, c)): (
                "Pipe C empties the tank, so subtract its rate instead of adding it."
            ),
        },
    )


def _interest(rng: random.Random, difficulty: str) -> dict:
    if difficulty == "easy":
        p = rng.randrange(1000, 20_001, 500)
        r = rng.randint(4, 15)
        t = rng.randint(2, 6)
        one = p * r // 100
        si = one * t
        return dict(
            statement=f"Find the simple interest, in rupees, on Rs {p} at {r}% per annum for {t} years.",
            answer=(Fraction(si),),
            hints=(
                "Simple interest is the same every year, because it is always worked out on the original sum.",
                f"One year's interest is {r}% of Rs {p}.",
                f"Multiply one year's interest by {t}. (Formula: SI = P \u00d7 R \u00d7 T \u00f7 100.)",
            ),
            solution=f"One year = {p} \u00d7 {r}/100 = {one}  \u2192  SI = {one} \u00d7 {t} = {si}",
            mistakes={
                Fraction(p + si): "That is the amount (principal + interest). The question asks for the interest only.",
                Fraction(one): f"That is one year's interest. The money is invested for {t} years.",
            },
        )
    if difficulty == "medium":
        r = rng.choice([4, 5, 8, 10, 12, 15, 20, 25])
        p = rng.choice([n for n in range(1000, 50_001, 100) if n * ((100 + r) ** 2 - 10_000) % 10_000 == 0])
        a1 = Fraction(p * (100 + r), 100)
        a2 = a1 * Fraction(100 + r, 100)
        ci = a2 - p
        return dict(
            statement=(
                f"Find the compound interest, in rupees, on Rs {p} for 2 years at {r}% per annum, compounded annually."
            ),
            answer=(ci,),
            hints=(
                "With compound interest, the second year's interest is also earned on the first year's interest.",
                f"After year 1 the amount grows to {p} \u00d7 {100 + r}/100, which comes to Rs {_dec(a1)}.",
                f"Find the amount after year 2 the same way, then subtract the principal Rs {p}.",
            ),
            solution=(
                f"A1 = {p} \u00d7 {100 + r}/100 = {_dec(a1)}  \u2192  A2 = {_dec(a1)} \u00d7 {100 + r}/100 = "
                f"{_dec(a2)}  \u2192  CI = {_dec(a2)} - {p} = {_dec(ci)}"
            ),
            mistakes={
                Fraction(2 * p * r, 100): "That is simple interest. With compound interest the second year earns "
                "interest on the first year's interest too.",
                a2: "That is the amount after 2 years. Subtract the principal to get the interest.",
            },
        )
    # hard: CI - SI difference for 2 years
    r = rng.choice([4, 5, 8, 10, 12, 15, 20])
    p = rng.choice([n for n in range(1000, 50_001, 100) if n * r * r % 10_000 == 0])
    diff = p * r * r // 10_000
    return dict(
        statement=(
            f"The difference between the compound interest and the simple interest on a sum for 2 years at "
            f"{r}% per annum is Rs {diff}. Find the sum, in rupees."
        ),
        answer=(Fraction(p),),
        hints=(
            "Over 2 years, CI and SI differ only by the interest earned on the first year's interest.",
            f"So the difference is {r}% of {r}% of the sum, that is, sum \u00d7 ({r}/100)\u00b2.",
            f"Rearrange: sum = difference \u00d7 (100/{r})\u00b2.",
        ),
        solution=f"{diff} = P \u00d7 ({r}/100)\u00b2  \u2192  P = {diff} \u00d7 10000/{r * r} = {p}",
        mistakes={
            Fraction(diff * 100, r): "You applied the rate only once. The difference is interest on interest, "
            "so the rate applies twice.",
        },
    )


def _linear(rng: random.Random, difficulty: str) -> dict:
    if difficulty == "easy":
        x = rng.randint(20, 200)
        y = rng.randint(5, x - 1)
        s, d = x + y, x - y
        return dict(
            statement=f"The sum of two numbers is {s} and their difference is {d}. What is the larger number?",
            answer=(Fraction(x),),
            hints=(
                "Call the larger number x and the smaller y. Write one equation for the sum and one for "
                "the difference.",
                "Add the two equations: the y terms cancel out.",
                f"You get 2x = {s + d}. One more step finishes it.",
            ),
            solution=f"x + y = {s}, x - y = {d}  \u2192  2x = {s + d}  \u2192  x = {x}",
            mistakes={
                Fraction(y): "That is the smaller number. The question asks for the larger one.",
                Fraction(s + d): "You found 2x. Divide by 2 to get x.",
            },
        )
    if difficulty == "medium":
        while True:
            x = rng.choice([n for n in range(-10, 13) if n not in (0, 1)])
            y = rng.choice([n for n in range(-10, 13) if n not in (0, 1, x)])
            a1, a2 = rng.randint(1, 9), rng.randint(1, 9)
            b1 = rng.randint(1, 9) * rng.choice([1, -1])
            b2 = rng.randint(1, 9) * rng.choice([1, -1])
            if a1 * b2 - a2 * b1 != 0 and (a1, b1) != (a2, b2):
                break
        c1, c2 = a1 * x + b1 * y, a2 * x + b2 * y
        m = lcm(abs(b1), abs(b2))
        m1, m2 = m // abs(b1), m // abs(b2)
        same_sign = (b1 > 0) == (b2 > 0)
        coef = a1 * m1 - a2 * m2 if same_sign else a1 * m1 + a2 * m2
        const = c1 * m1 - c2 * m2 if same_sign else c1 * m1 + c2 * m2
        eq1 = f"{_coef(a1, 'x')} {_term(b1, 'y')} = {c1}"
        eq2 = f"{_coef(a2, 'x')} {_term(b2, 'y')} = {c2}"
        steps = [f"{_coef(coef, 'x')} = {const}"] if coef != 1 else []
        return dict(
            statement=f"Solve the pair of equations {eq1} and {eq2}. What is the value of x?",
            answer_format="a whole number, for example 7 or -3",
            answer=(Fraction(x),),
            hints=(
                "Eliminate one variable: make the coefficients of y the same size in both equations.",
                f"Multiply the first equation by {m1} and the second by {m2}, then "
                f"{'subtract' if same_sign else 'add'} them so that y disappears.",
                "Once y is gone you have one equation in x. Solve it, then check in either original equation.",
            ),
            solution="  \u2192  ".join(["Eliminate y", *steps, f"x = {x}"]),
            mistakes={
                Fraction(y): "That is the value of y. The question asks for x.",
                Fraction(-x): "Check your signs: you have the right size of number but the wrong sign.",
            },
        )
    # hard: ages in a ratio, now and later
    while True:
        p, q = rng.sample(range(1, 10), 2)
        if gcd(p, q) == 1:
            break
    for _ in range(50):  # prefer a tidy future ratio such as 3:4 over 43:67
        k = rng.randint(2, 12)
        n = rng.randint(2, 20)
        g = gcd(p * k + n, q * k + n)
        r, s = (p * k + n) // g, (q * k + n) // g
        if max(r, s) <= 20:
            break
    return dict(
        statement=(
            f"The present ages of A and B are in the ratio {p}:{q}. After {n} years, the ratio of their ages "
            f"will be {r}:{s}. What is A's present age, in years?"
        ),
        answer=(Fraction(p * k),),
        hints=(
            f"Let the present ages be {p}k and {q}k years.",
            f"After {n} years, ({p}k + {n}) / ({q}k + {n}) must equal {r}/{s}. Cross-multiply.",
            "Solve the linear equation for k, then multiply by A's part of the ratio.",
        ),
        solution=f"{s}({p}k + {n}) = {r}({q}k + {n})  \u2192  k = {k}  \u2192  A = {p} \u00d7 {k} = {p * k}",
        mistakes={
            Fraction(k): f"That is the multiplier k. Multiply it by A's ratio part, {p}.",
            Fraction(q * k): "That is B's present age. The question asks for A's.",
            Fraction(p * k + n): f"That is A's age after {n} years. The question asks for the present age.",
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


def _quadratics(rng: random.Random, difficulty: str) -> dict:
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


def _number_system(rng: random.Random, difficulty: str) -> dict:
    fmt = "a whole number, for example 12"
    if difficulty == "easy":
        h = rng.randint(4, 30)
        m1, m2 = rng.sample(range(2, 16), 2)
        while gcd(m1, m2) != 1:
            m2 += 1
        n1, n2 = h * m1, h * m2
        hcf, lcm_ = h, h * m1 * m2
        if rng.random() < 0.5:
            return dict(
                statement=f"Find the HCF (highest common factor) of {n1} and {n2}.",
                answer_format=fmt,
                answer=(Fraction(hcf),),
                hints=(
                    "Write each number as a product of prime factors.",
                    "The HCF uses only the primes that appear in both numbers, each with its lower power.",
                    "Multiply those common prime powers. (Or use Euclid's method: HCF(a, b) = HCF(b, a mod b).)",
                ),
                solution=f"{n1} = {_factorise(n1)}, {n2} = {_factorise(n2)}  \u2192  HCF = {hcf}",
                mistakes={
                    Fraction(lcm_): "That is the LCM. The HCF is the largest number that divides both.",
                    Fraction(n1 * n2): "That is the product of the numbers, not their HCF.",
                },
            )
        return dict(
            statement=f"Find the LCM (lowest common multiple) of {n1} and {n2}.",
            answer_format=fmt,
            answer=(Fraction(lcm_),),
            hints=(
                "Write each number as a product of prime factors.",
                "The LCM uses every prime that appears in either number, each with its higher power.",
                "Multiply those prime powers. (Check: HCF \u00d7 LCM equals the product of the two numbers.)",
            ),
            solution=f"{n1} = {_factorise(n1)}, {n2} = {_factorise(n2)}  \u2192  LCM = {lcm_}",
            mistakes={
                Fraction(hcf): "That is the HCF. The LCM is the smallest number that both divide into.",
                Fraction(n1 * n2): "The product is a common multiple, but not the lowest one, because the "
                "numbers share a factor.",
            },
        )
    if difficulty == "medium":
        last = rng.choice([2, 3, 4, 7, 8, 9])
        base = last + 10 * rng.randint(0, 9)
        exp = rng.randint(20, 999)
        cycle = []
        v = last
        while v not in cycle:
            cycle.append(v)
            v = v * last % 10
        rem = exp % len(cycle)
        digit = pow(base, exp, 10)
        return dict(
            statement=f"What is the units digit of {base}^{exp}?",
            answer_format="a single digit from 0 to 9",
            answer=(Fraction(digit),),
            hints=(
                "Only the units digit of the base matters, and the units digits of its powers repeat in a cycle.",
                f"Write out the units digits of {last}^1, {last}^2, {last}^3 and {last}^4, and spot the cycle.",
                "Divide the power by the cycle length. The remainder gives the position in the cycle "
                "(a remainder of 0 means the last position).",
            ),
            solution=(
                f"Units digits of powers of {last} cycle through {', '.join(map(str, cycle))}  \u2192  "
                f"{exp} mod {len(cycle)} = {rem}  \u2192  units digit {digit}"
            ),
            mistakes=(
                {Fraction(1): "A remainder of 0 points to the last digit of the cycle, not to a power of 0."}
                if rem == 0
                else {}
            ),
        )
    # hard: number of factors
    while True:
        primes = sorted(rng.sample([2, 3, 5, 7, 11], rng.choice([2, 3])))
        exps = [rng.randint(1, 4) for _ in primes]
        n = prod(pr**e for pr, e in zip(primes, exps, strict=True))
        if 100 <= n <= 200_000:
            break
    count = prod(e + 1 for e in exps)
    return dict(
        statement=f"How many positive factors (divisors) does {n} have?",
        answer_format=fmt,
        answer=(Fraction(count),),
        hints=(
            "Start by writing the number as a product of prime powers.",
            "Every factor picks a power of each prime, anywhere from power 0 up to the power in the number.",
            "So if N = p^a \u00d7 q^b \u00d7 r^c, the number of factors is (a + 1)(b + 1)(c + 1).",
        ),
        solution=(f"{n} = {_factorise(n)}  \u2192  {_TIMES.join(f'({e} + 1)' for e in exps)} = {count}"),
        mistakes={
            Fraction(sum(exps)): "That is the sum of the powers. Add 1 to each power, then multiply.",
            Fraction(prod(exps)): "Add 1 to each power before multiplying: power 0 counts too.",
            Fraction(sum(e + 1 for e in exps)): "Multiply the (power + 1) values instead of adding them.",
        },
    )


def _number_series(rng: random.Random, difficulty: str) -> dict:
    fmt = "a whole number, for example 64"
    if difficulty == "easy":
        a = rng.randint(2, 60)
        d = rng.randint(3, 15) * rng.choice([1, 1, -1])
        if d < 0:
            a += 6 * -d
        terms = [a + i * d for i in range(5)]
        nxt = a + 5 * d
        return dict(
            statement=f"Find the next number in the series: {', '.join(map(str, terms))}, ?",
            answer_format=fmt,
            answer=(Fraction(nxt),),
            hints=(
                "Look at the gap between each pair of neighbouring terms.",
                "The gap is the same every time.",
                "Apply that same gap to the last term.",
            ),
            solution=f"Common difference {d}  \u2192  next = {terms[-1]} {_signed(d)} = {nxt}",
            mistakes={Fraction(terms[-1] - d): "Check the direction: is the series going up or down?"},
        )
    if difficulty == "medium":
        if rng.random() < 0.5:
            r = rng.choice([2, 3])
            a = rng.randint(2, 9)
            terms = [a * r**i for i in range(5)]
            nxt = a * r**5
            return dict(
                statement=f"Find the next number in the series: {', '.join(map(str, terms))}, ?",
                answer_format=fmt,
                answer=(Fraction(nxt),),
                hints=(
                    "The gaps grow quickly. Try dividing each term by the one before it.",
                    "Each term is the previous term multiplied by the same number.",
                    "Multiply the last term by that number.",
                ),
                solution=f"Each term \u00d7 {r}  \u2192  next = {terms[-1]} \u00d7 {r} = {nxt}",
                mistakes={
                    Fraction(2 * terms[-1] - terms[-2]): "The gaps are not equal. Compare ratios instead.",
                },
            )
        a = rng.randint(1, 30)
        g0 = rng.randint(1, 8)
        e = rng.randint(1, 5)
        gaps = [g0 + i * e for i in range(5)]
        terms = [a]
        for gap in gaps[:4]:
            terms.append(terms[-1] + gap)
        nxt = terms[-1] + gaps[4]
        return dict(
            statement=f"Find the next number in the series: {', '.join(map(str, terms))}, ?",
            answer_format=fmt,
            answer=(Fraction(nxt),),
            hints=(
                "Write down the gaps between neighbouring terms.",
                "The gaps themselves form a simple pattern: they change by the same amount each time.",
                "Find the next gap, then add it to the last term.",
            ),
            solution=(
                f"Gaps {', '.join(map(str, gaps[:4]))}  \u2192  next gap {gaps[4]}  \u2192  "
                f"next = {terms[-1]} + {gaps[4]} = {nxt}"
            ),
            mistakes={
                Fraction(terms[-1] + gaps[3]): "You repeated the last gap. Look at how the gaps themselves change."
            },
        )
    # hard: multiply-and-add, or two interleaved series
    if rng.random() < 0.5:
        m = rng.choice([2, 3])
        c = rng.choice([-3, -2, -1, 1, 2, 3])
        a = rng.randint(3, 9)
        terms = [a]
        for _ in range(4):
            terms.append(terms[-1] * m + c)
        nxt = terms[-1] * m + c
        return dict(
            statement=f"Find the next number in the series: {', '.join(map(str, terms))}, ?",
            answer_format=fmt,
            answer=(Fraction(nxt),),
            hints=(
                "The terms grow roughly by multiplying. Compare each term with the previous term times a "
                "small whole number.",
                f"Multiply each term by {m}. What is left over to reach the next term?",
                "The leftover is the same every time. Multiply the last term, then adjust by the leftover.",
            ),
            solution=f"Each term \u00d7 {m} {_signed(c)}  \u2192  next = {terms[-1]} \u00d7 {m} {_signed(c)} = {nxt}",
            mistakes={Fraction(terms[-1] * m): f"Close: you multiplied by {m} but forgot the fixed adjustment."},
        )
    a1, d1 = rng.randint(1, 20), rng.randint(2, 9)
    a2, d2 = rng.randint(20, 60), rng.randint(2, 9) * rng.choice([1, -1])
    odd = [a1 + i * d1 for i in range(4)]
    even = [a2 + i * d2 for i in range(4)]
    terms = [odd[0], even[0], odd[1], even[1], odd[2], even[2], odd[3]]
    nxt = even[3]
    return dict(
        statement=f"Find the next number in the series: {', '.join(map(str, terms))}, ?",
        answer_format=fmt,
        answer=(Fraction(nxt),),
        hints=(
            "Neighbouring terms do not follow one rule. Compare terms that are two places apart.",
            "The terms in odd positions form one series and the terms in even positions form another.",
            "The missing term is in an even position, so continue the even-position series.",
        ),
        solution=(
            f"Odd positions {', '.join(map(str, odd))} (step {d1}), even positions "
            f"{', '.join(map(str, even[:3]))} (step {d2})  \u2192  next = {even[2]} {_signed(d2)} = {nxt}"
        ),
        mistakes={
            Fraction(odd[3] + d1): ("That continues the odd-position series. The missing term is in an even position."),
        },
    )


_GENERATORS = {
    "percentages": _percentages,
    "profit_loss": _profit_loss,
    "ratio_proportion": _ratio,
    "time_speed_distance": _time_speed_distance,
    "time_work": _time_work,
    "interest": _interest,
    "linear_equations": _linear,
    "quadratics": _quadratics,
    "number_system": _number_system,
    "number_series": _number_series,
}


def generate(topic: str, difficulty: str, seed: int) -> Problem:
    """Build a problem. The same arguments always give the same problem."""
    validate_request(topic, difficulty, seed)
    rng = random.Random(f"{topic}|{difficulty}|{seed}")
    spec = _GENERATORS[topic](rng, difficulty)
    spec.setdefault("answer_format", DEFAULT_FORMAT)
    # A "common mistake" value must never coincide with the real answer.
    spec["mistakes"] = {k: v for k, v in spec["mistakes"].items() if k not in spec["answer"]}
    return Problem(
        id=make_problem_id(topic, difficulty, seed),
        topic=topic,
        section=TOPIC_SECTIONS[topic],
        difficulty=difficulty,
        seed=seed,
        **spec,
    )


def problem_from_id(problem_id: str) -> Problem:
    return generate(*parse_problem_id(problem_id))


# ------------------------------------------------------------------- checking


def parse_numbers(text: str, *, thousands: bool = True) -> list[Fraction]:
    """Pull every number out of a free-text answer.

    Accepts ``7``, ``x = -3``, ``7/12``, ``2.5``, ``Rs 1,200``, ``37.5%``,
    ``x = 2 or x = -3`` and the Unicode minus sign. With ``thousands=True``,
    commas inside numbers (``1,20,000``) are treated as digit grouping; pass
    ``False`` when commas separate several answers. Raises ProblemError if no
    number is found.
    """
    cleaned = text.replace("\u2212", "-")
    if thousands:
        cleaned = _THOUSANDS_RE.sub("", cleaned)
    cleaned = cleaned.replace(",", " ")
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
    multi = len(problem.answer) > 1
    try:
        values = parse_numbers(answer_text, thousands=not multi)
    except ProblemError as exc:
        raise ProblemError(f"{exc} Expected format: {problem.answer_format}.") from exc

    if multi:
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
    if value == problem.answer[0]:
        return CheckResult(True, "Correct! Well done. Now try to solve the next one faster.")
    if value in problem.mistakes:
        return CheckResult(False, problem.mistakes[value])
    return CheckResult(False, "Not quite. Re-check each step, or ask for a hint.")
