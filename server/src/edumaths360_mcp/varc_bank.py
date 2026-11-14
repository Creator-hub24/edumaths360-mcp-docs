"""Original CAT-style VARC items written for Edumaths360.

Every passage and sentence here was written for this project; none is copied
from a CAT paper or a coaching site. ``problems.py`` picks an item with a
seeded random generator and shuffles the labels, so the same problem ID always
shows the same item in the same order.

* Para jumbles: ``sentences`` are listed in the CORRECT order.
* Odd sentence out: ``core`` sentences form the paragraph; ``odd`` does not belong.
* Para summary: ``correct`` is the best summary; each distractor has a type
  (``narrow``, ``broad`` or ``distort``) used for targeted feedback.
"""

from __future__ import annotations

PARA_JUMBLES: dict[str, list[dict]] = {
    "easy": [
        {
            "sentences": [
                "Tea reached Britain in the seventeenth century as an expensive curiosity sold by apothecaries.",
                "Within a hundred years, falling import duties had made it affordable for working families.",
                "As a result, the drink moved from the medicine shelf to the kitchen table.",
                "Today the afternoon cup is so ordinary that few people remember it was once a luxury.",
            ],
            "structure": "The paragraph follows a story through time, from arrival to the present day.",
            "explanation": "Tea arrives as a luxury, duties fall, it becomes an everyday drink, and the last "
            "sentence looks back from today.",
        },
        {
            "sentences": [
                "Many cities have started lending bicycles the way libraries lend books.",
                "A rider unlocks a bike with a phone, uses it for a short trip and leaves it at any station.",
                "This convenience has persuaded people who would never buy a bicycle to try cycling to work.",
                "Planners hope that, over time, these new cyclists will demand safer lanes and fewer cars.",
            ],
            "structure": "The paragraph moves from what a scheme is, to how it works, to its effects now and later.",
            "explanation": "The idea is introduced, then how it works, then 'this convenience' and its effect, "
            "and finally the planners' longer-term hope about 'these new cyclists'.",
        },
        {
            "sentences": [
                "Scientists once believed that the sleeping brain was simply switched off.",
                "Recordings of brain activity in the 1950s proved them wrong.",
                "They showed that during certain stages of sleep the brain is almost as active as when awake.",
                "These findings opened a new field devoted to understanding what the brain does at night.",
            ],
            "structure": "An old belief is stated, overturned by evidence, and the consequence follows.",
            "explanation": "'Them' refers to the scientists, 'They' refers to the recordings, and 'These "
            "findings' sums up what the recordings showed.",
        },
    ],
    "medium": [
        {
            "sentences": [
                "Schools in several countries have stopped teaching joined-up handwriting, arguing that pupils "
                "will mostly type.",
                "The decision seems practical, but it overlooks what happens in the hand while the mind is learning.",
                "Studies of note-taking suggest that students who write by hand must summarise as they go, because "
                "they cannot copy every word.",
                "That forced summarising, rather than the neatness of the script, may be what helps them remember.",
            ],
            "structure": "A policy is described, questioned, and then the evidence behind the doubt is explained.",
            "explanation": "The policy comes first, 'the decision' questions it, the note-taking studies give the "
            "evidence, and 'that forced summarising' draws the conclusion.",
        },
        {
            "sentences": [
                "On a summer afternoon, the centre of a large city can be several degrees warmer than the "
                "countryside around it.",
                "Concrete and asphalt soak up sunlight during the day and release it slowly after dark.",
                "Add the heat pouring out of air conditioners and car engines, and the effect grows stronger.",
                "Planting trees and painting roofs white are two cheap ways to break this cycle.",
            ],
            "structure": "A phenomenon is described, its causes are added one by one, and a remedy closes it.",
            "explanation": "The warm city centre is the phenomenon, materials are the first cause, machines add to "
            "'the effect', and the remedies break 'this cycle'.",
        },
        {
            "sentences": [
                "A word-for-word translation is rarely a faithful one.",
                "Every language packs meaning differently, so a phrase that is natural in one can sound stiff or "
                "even rude in another.",
                "Good translators therefore aim to recreate the effect of the original rather than its exact words.",
                "In doing so, they sometimes depart from the text precisely in order to stay true to it.",
            ],
            "structure": "A claim is made, a reason supports it, a practical "
            "consequence follows, and a paradox ends it.",
            "explanation": "The claim comes first, the reason second, 'therefore' introduces the consequence, and "
            "'in doing so' builds on what good translators do.",
        },
    ],
    "hard": [
        {
            "sentences": [
                "Every map is an argument about what matters.",
                "To fit a round planet onto a flat sheet, a mapmaker must stretch some regions and shrink others.",
                "The familiar Mercator projection, designed for sailors, preserves direction but greatly enlarges "
                "lands near the poles.",
                "Generations of schoolchildren have consequently grown up picturing Greenland as roughly the size "
                "of Africa.",
                "The distortion was never a secret; it simply served one purpose so well that people forgot it "
                "had a cost.",
            ],
            "structure": "A bold general claim is followed by the reason, a famous "
            "example, its effect and a reflection.",
            "explanation": "The general claim leads, the stretching explains it, Mercator is the example, "
            "'consequently' gives its effect, and 'the distortion' reflects on all of it.",
        },
        {
            "sentences": [
                "When information was scarce, the main challenge was finding it.",
                "Now that information is abundant, the scarce resource is the attention needed to absorb it.",
                "Companies have noticed, and many digital products are designed less to inform users than to hold "
                "their gaze.",
                "Their success is measured in minutes spent, not in anything the user has learned.",
                "Seen this way, the real price of a 'free' app is paid in time.",
            ],
            "structure": "A contrast between past and present sets up how businesses respond and what that costs us.",
            "explanation": "'When... was scarce' pairs with 'Now that... is abundant', 'Companies have noticed' "
            "reacts to it, 'Their success' refers to the products, and 'Seen this way' concludes.",
        },
        {
            "sentences": [
                "For centuries, European merchants kept their accounts in Roman numerals.",
                "The system had no symbol for zero, which made long calculations slow and prone to error.",
                "Hindu-Arabic numerals, which included zero and place value, offered a far quicker method.",
                "Yet many traders resisted them at first, partly because the unfamiliar digits seemed easier to "
                "alter in a ledger.",
                "Only when printed arithmetic manuals spread the new method did it finally win out.",
            ],
            "structure": "An old system, its weakness, a better alternative, "
            "resistance to it, and its eventual victory.",
            "explanation": "The old system comes first, 'the system' names its flaw, the alternative follows, "
            "'Yet... resisted them' needs the alternative before it, and 'Only when' ends the story.",
        },
    ],
}

ODD_SENTENCE_OUT: dict[str, list[dict]] = {
    "easy": [
        {
            "core": [
                "Honeybees tell each other where food is through a movement known as the waggle dance.",
                "The angle of the dance shows other bees the direction of the flowers relative to the sun.",
                "The length of each waggle run indicates how far away the food is.",
                "Decoding the dance revealed one of the most precise signalling systems among animals.",
            ],
            "odd": "Honey has been found in ancient tombs, still edible after thousands of years.",
            "topic": "The paragraph is about how bees share information with one another.",
            "why": "the others explain how the waggle dance communicates; this one is a fact about honey.",
        },
        {
            "core": [
                "Public parks give city residents a place to exercise without paying for a gym.",
                "They also lower stress: even a short walk among trees can calm the heart rate.",
                "For many children, open green space is the only safe place to play outdoors.",
                "For these reasons, many health experts see parks as part of a city's medical infrastructure.",
            ],
            "odd": "The first public park in the world is often said to have opened in the nineteenth century.",
            "topic": "The paragraph is about the health benefits of parks.",
            "why": "the others are about how parks improve health; this one is a point of history.",
        },
        {
            "core": [
                "In much of India, farmers still depend on the monsoon to water their fields.",
                "A late or weak monsoon can delay sowing and reduce harvests.",
                "Smaller harvests, in turn, push up food prices in towns and cities.",
                "That is why economists watch the arrival of the rains as closely as farmers do.",
            ],
            "odd": "Monsoon clouds also make for spectacular photographs over the Western Ghats.",
            "topic": "The paragraph is about the economic effects of the monsoon.",
            "why": "the others trace the monsoon's effect on harvests and prices; this one is about scenery.",
        },
    ],
    "medium": [
        {
            "core": [
                "Forgetting is usually seen as a failure of memory.",
                "Yet a brain that stored every detail with equal weight would struggle to pick out what matters.",
                "By letting unimportant details fade, the mind makes room for patterns and general rules.",
                "In this sense, forgetting is part of how we learn rather than its opposite.",
            ],
            "odd": "Memory competitions reward contestants who can recall the order of a shuffled deck of cards.",
            "topic": "The paragraph argues that forgetting has a useful role in learning.",
            "why": "it shares the keyword 'memory' but is about feats of recall, not the value of forgetting.",
        },
        {
            "core": [
                "Remote work removed the daily commute for millions of office employees.",
                "Many used the saved hours for exercise, family or simply more sleep.",
                "Others found that, without a commute, the line between work time and home time blurred.",
                "The same change, in other words, gave some people time and took boundaries away from others.",
            ],
            "odd": "Video-calling companies saw their share prices rise sharply in the first months of the shift.",
            "topic": "The paragraph is about how remote work changed the way people use their time.",
            "why": "the others describe effects on employees' time; this one is about company share prices.",
        },
        {
            "core": [
                "Only a small share of the plastic ever produced has been recycled.",
                "Many plastics lose quality each time they are melted down, so they cannot be recycled endlessly.",
                "Mixed and dirty plastic waste is also expensive to sort.",
                "Some experts therefore argue that using less plastic matters more than recycling it better.",
            ],
            "odd": "Plastic was first marketed as a cheap substitute for ivory and tortoiseshell.",
            "topic": "The paragraph is about the limits of recycling plastic.",
            "why": "the others explain why recycling falls short; this one is about plastic's early history.",
        },
    ],
    "hard": [
        {
            "core": [
                "A placebo has no active ingredient, yet patients who take one often report feeling better.",
                "Part of the effect comes from expectation: believing a pill "
                "will help can change how we perceive pain.",
                "Remarkably, some studies find that placebos help even when patients are told the pills are inactive.",
                "This suggests that the ritual of treatment, not only belief in a drug, can affect how we feel.",
            ],
            "odd": "Drug trials compare a new medicine with a placebo so that "
            "the medicine's true effect can be measured.",
            "topic": "The paragraph explores why placebos make people feel better.",
            "why": "it mentions placebos but shifts to how trials use them, not why they work.",
        },
        {
            "core": [
                "Linguists estimate that a language falls silent somewhere in the world every few weeks.",
                "When the last fluent speakers die, knowledge held in the language, such as names for local plants, "
                "can vanish with them.",
                "Recording and teaching endangered languages is one way communities try to keep that knowledge alive.",
                "Some revival efforts have succeeded, bringing languages back into daily use after decades of decline.",
            ],
            "odd": "English borrows words freely from other languages, which is one reason its vocabulary is so large.",
            "topic": "The paragraph is about endangered languages and efforts to save them.",
            "why": "it is about language in general, not about languages disappearing or being revived.",
        },
        {
            "core": [
                "Shoppers rarely judge a price in isolation; they compare it with whatever number they saw first.",
                "A jacket marked 'was Rs 6,000, now Rs 3,000' feels like a bargain even if Rs 3,000 was always "
                "its fair price.",
                "Restaurants use the same trick when they place one very expensive dish at the top of the menu.",
                "The other dishes then seem reasonable by comparison, and diners spend more without feeling "
                "extravagant.",
            ],
            "odd": "Online retailers can change their prices many times a day in response to demand.",
            "topic": "The paragraph is about how a first number anchors our sense of what a price is worth.",
            "why": "it concerns pricing but not the anchoring effect that links the other sentences.",
        },
    ],
}

PARA_SUMMARY: dict[str, list[dict]] = {
    "easy": [
        {
            "passage": "Some companies now hold meetings while walking instead of sitting around a table. Supporters "
            "say the habit gets people moving during long working days, and that conversation flows more freely "
            "when colleagues walk side by side rather than face each other. Walking meetings are not suitable for "
            "everything, since it is hard to look at documents or take detailed notes on the move, but for "
            "brainstorming or one-to-one discussions they can be both healthier and more productive.",
            "correct": "Walking meetings can make some discussions healthier and more productive, though they do "
            "not suit every kind of meeting.",
            "distractors": [
                ("narrow", "Walking side by side helps colleagues talk more freely than sitting face to face."),
                ("broad", "Companies should replace all seated meetings with walking meetings to improve health."),
                ("distort", "Walking meetings are popular mainly because they make note-taking easier."),
            ],
            "structure": "The passage weighs a benefit against a limitation.",
        },
        {
            "passage": "Reading aloud to young children does more than entertain them. Hearing stories introduces "
            "words that rarely appear in everyday conversation, and talking about the pictures helps children "
            "connect language with meaning. Children who are read to regularly tend to arrive at school with "
            "larger vocabularies. Just as importantly, shared reading builds an association between books and "
            "comfort, which can make children more willing to read on their own later.",
            "correct": "Regular reading aloud builds young children's vocabulary and makes them more inclined to "
            "read for themselves.",
            "distractors": [
                ("narrow", "Talking about pictures helps children connect words with their meanings."),
                ("broad", "Children who are read to at home always do better at school than those who are not."),
                ("distort", "Reading aloud matters mainly because it keeps young children entertained."),
            ],
            "structure": "The passage names two benefits; the first sentence warns against the obvious one.",
        },
        {
            "passage": "Rooftop solar panels once made sense only for wealthy homeowners willing to wait many years "
            "to recover their cost. Since then, the price of panels has fallen sharply, and in sunny regions a "
            "household system can now pay for itself within a few years through lower electricity bills. The main "
            "obstacles today are less about money than about paperwork, as approvals and grid connections can take "
            "months.",
            "correct": "Rooftop solar has become affordable for many households, and the main barrier is now slow "
            "approvals rather than cost.",
            "distractors": [
                ("narrow", "Solar panels are much cheaper today than they used to be."),
                ("broad", "Every household should install rooftop solar panels to cut its electricity bills."),
                ("distort", "Rooftop solar still makes sense only for wealthy households."),
            ],
            "structure": "The passage contrasts the past with the present and ends on a new obstacle.",
        },
    ],
    "medium": [
        {
            "passage": "Experienced professionals often make good decisions in seconds without being able to explain "
            "how. A firefighter senses that a floor is about to collapse; a nurse notices that a patient is getting "
            "worse before the monitors show it. Such intuition is not magic. It is pattern recognition built from "
            "thousands of past cases, and it is reliable only in settings that give quick, clear feedback. Where "
            "feedback is slow or noisy, as in long-range economic forecasting, confident gut feelings deserve far "
            "less trust.",
            "correct": "Expert intuition is learned pattern recognition that can be trusted where feedback is quick "
            "and clear, but not where it is slow or unclear.",
            "distractors": [
                ("narrow", "Firefighters and nurses can sense danger before instruments detect it."),
                ("broad", "Gut feelings are generally more reliable than careful analysis."),
                ("distort", "Intuition is a mysterious gift that some professionals are simply born with."),
            ],
            "structure": "The passage explains what intuition is and then sets a condition on when to trust it.",
        },
        {
            "passage": "Many museums in Europe hold objects that were taken from other countries during colonial "
            "rule. For decades, curators argued that these collections were safer and more widely seen in major "
            "museums. That argument has weakened as countries of origin have built well-equipped museums of their "
            "own, and as visitors have grown more interested in how objects were acquired. Several institutions "
            "have now returned items, while others are lending them back or sharing ownership.",
            "correct": "As the old case for keeping colonial-era artefacts weakens, museums are increasingly "
            "returning, lending or sharing them.",
            "distractors": [
                ("narrow", "Countries of origin have built well-equipped museums of their own."),
                ("broad", "All museums will soon have to return every object that came from another country."),
                ("distort", "Museums keep colonial-era objects because they are still safer in Europe."),
            ],
            "structure": "The passage describes an old justification, why it has weakened, and what is changing.",
        },
        {
            "passage": "Trials of a four-day working week, with no cut in pay, have been run by companies in several "
            "countries. Many report that output held steady, as employees cut unnecessary meetings and worked with "
            "fewer distractions. Staff said they felt less tired and were less likely to quit. Critics point out "
            "that the trials mostly involved office firms that chose to take part, so the results may not apply to "
            "factories, hospitals or businesses that were reluctant from the start.",
            "correct": "Four-day-week trials showed steady output and happier staff, but the results may not hold "
            "beyond the self-selected office firms that took part.",
            "distractors": [
                ("narrow", "Employees in the trials cut down on unnecessary meetings."),
                ("broad", "A four-day week raises productivity in every kind of workplace."),
                ("distort", "The trials found that output fell sharply when the week was shortened."),
            ],
            "structure": "The passage reports results and then a caution about how far they apply.",
        },
    ],
    "hard": [
        {
            "passage": "When a number is used to judge performance, people learn to improve the number, not always "
            "the thing it was meant to reflect. A hospital rewarded for short waiting times may rush patients "
            "through assessment; a school judged on pass rates may steer weaker students away from difficult exams. "
            "None of this requires dishonesty, only ordinary people responding to incentives. The lesson is not to "
            "abandon measurement but to treat any single indicator with suspicion once it becomes a target.",
            "correct": "Once a single measure becomes a target, people optimise the measure rather than the goal, "
            "so such indicators need caution rather than abandonment.",
            "distractors": [
                ("narrow", "Hospitals judged on waiting times may rush patients through assessment."),
                ("broad", "Measuring performance does more harm than good and should be avoided."),
                ("distort", "Indicators fail mainly because the people being measured are dishonest."),
            ],
            "structure": "The passage states a general tendency, gives examples, rules out one cause and draws a "
            "balanced lesson.",
        },
        {
            "passage": "Public trust in experts is often described as either present or absent, but it is better "
            "understood as conditional. People tend to accept expert advice when it matches what they observe and "
            "when experts admit uncertainty openly. Trust collapses fastest not when experts are wrong, which is "
            "inevitable, but when they appear to have hidden doubts or changed position without explanation. "
            "Restoring trust, therefore, depends less on projecting certainty than on being open about how "
            "conclusions are reached.",
            "correct": "Trust in experts depends on openness about uncertainty and reasoning, so it is rebuilt "
            "through transparency rather than displays of certainty.",
            "distractors": [
                ("narrow", "People accept expert advice when it matches what they observe."),
                ("broad", "The public should trust experts even when their advice is uncertain."),
                ("distort", "Experts lose public trust mainly because they are often wrong."),
            ],
            "structure": "The passage reframes trust as conditional, says what breaks it and what restores it.",
        },
        {
            "passage": "Supply chains were long designed to be lean: companies held little stock and relied on "
            "single, low-cost suppliers, which kept prices down. The arrangement worked well until a disruption at "
            "one point, such as a closed port or a factory fire, left firms with nothing in reserve. Many businesses "
            "now accept slightly higher costs in exchange for spare inventory and multiple suppliers. The shift "
            "reflects a recognition that efficiency and resilience pull in opposite directions, and that the "
            "cheapest system is not always the safest.",
            "correct": "Firms are trading some efficiency for resilience, accepting higher costs to avoid the "
            "fragility of lean supply chains.",
            "distractors": [
                ("narrow", "A factory fire can leave a firm with nothing in reserve."),
                ("broad", "Companies should always choose the most resilient supplier regardless of cost."),
                ("distort", "Lean supply chains became popular because they made firms more resilient."),
            ],
            "structure": "The passage describes an old design, its weakness, a change in behaviour and the "
            "trade-off behind it.",
        },
    ],
}
