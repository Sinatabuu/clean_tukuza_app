# modules/gifts_engine.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

GIFTS: List[str] = [
    "Teaching",
    "Exhortation",
    "Evangelism",
    "Mercy",
    "Helps",
    "Giving",
    "Leadership",
    "Wisdom",
    "Discernment",
    "Intercession",
]

# 50 core questions in the exact order you present them in the UI.
QUESTIONS_EN: List[str] = [
    # Teaching (1-5)
    "I feel compelled to clarify Scripture when others misunderstand it.",
    "I am dissatisfied when biblical teaching lacks depth or accuracy.",
    "I naturally organize biblical ideas into clear explanations.",
    "I regularly study Scripture beyond what is required of me.",
    "People often tell me they understand the Bible better after I explain it.",

    # Exhortation (6-10)
    "I feel driven to help people take their next step of obedience.",
    "I am burdened when believers remain stagnant in their growth.",
    "I naturally motivate others toward spiritual action.",
    "I often speak words that help people regain confidence and direction.",
    "People frequently act on their faith after conversations with me.",

    # Evangelism (11-15)
    "I feel urgency when I am around people who do not know Christ.",
    "I think often about how to explain the gospel clearly to others.",
    "I initiate faith conversations outside church settings.",
    "I willingly share Christ even when it feels uncomfortable.",
    "People have taken meaningful steps toward Christ through my influence.",

    # Mercy (16-20)
    "I feel deep compassion when others are suffering emotionally or physically.",
    "I am troubled when people feel unseen or forgotten.",
    "I naturally move toward people in pain rather than away from them.",
    "I willingly invest time in helping people recover from hardship.",
    "People often experience comfort or healing through my care.",

    # Helps/Service (21-25)
    "I feel responsible to support ministry needs in practical ways.",
    "I am concerned when important tasks are neglected.",
    "I consistently follow through on responsibilities others depend on.",
    "I quietly step in when something needs to be done.",
    "My support enables others to minister more effectively.",

    # Giving (26-30)
    "I feel joy when I can resource God’s work financially or materially.",
    "I am burdened when meaningful ministry lacks funding.",
    "I give strategically and intentionally rather than impulsively.",
    "I am willing to sacrifice comfort to support kingdom work.",
    "My generosity has significantly strengthened ministries or individuals.",

    # Leadership/Administration (31-35)
    "I feel responsible to bring order when things lack direction.",
    "I am concerned when vision and structure are unclear.",
    "I naturally organize people and processes to accomplish goals.",
    "I take initiative to coordinate efforts toward shared outcomes.",
    "When I lead or organize, effectiveness noticeably increases.",

    # Wisdom (36-40)
    "I feel drawn to help people apply biblical truth to real-life decisions.",
    "I am troubled when people make avoidable mistakes.",
    "I often see practical solutions others overlook.",
    "I help others weigh consequences before making decisions.",
    "My counsel has helped others make sound and balanced choices.",

    # Discernment (41-45)
    "I feel compelled to evaluate teaching or situations carefully.",
    "I am unsettled when something appears spiritually inconsistent.",
    "I can identify error or unhealthy influence quickly.",
    "I test ideas against Scripture before accepting them.",
    "My discernment has helped protect others from deception or harm.",

    # Intercession (46-50)
    "I feel a strong and ongoing burden to pray for people or situations.",
    "I am concerned when prayer is neglected.",
    "I consistently spend extended time in focused prayer.",
    "I return repeatedly to prayer about specific needs.",
    "My prayers have resulted in visible spiritual breakthrough or change.",
]

# For scoring: each gift has 5 items with types (Burden, Behavior, Fruit)
# Weights are chosen for stability: Behavior > Burden > Fruit
TYPE_WEIGHTS = {
    "burden": 0.35,
    "behavior": 0.40,
    "fruit": 0.25,
}

# Map gift -> list of (question_index, type)
# question_index is 0-based into QUESTONS_EN
GIFT_ITEMS: Dict[str, List[Tuple[int, str]]] = {
    "Teaching": [(0, "burden"), (1, "burden"), (2, "behavior"), (3, "behavior"), (4, "fruit")],
    "Exhortation": [(5, "burden"), (6, "burden"), (7, "behavior"), (8, "behavior"), (9, "fruit")],
    "Evangelism": [(10, "burden"), (11, "burden"), (12, "behavior"), (13, "behavior"), (14, "fruit")],
    "Mercy": [(15, "burden"), (16, "burden"), (17, "behavior"), (18, "behavior"), (19, "fruit")],
    "Helps": [(20, "burden"), (21, "burden"), (22, "behavior"), (23, "behavior"), (24, "fruit")],
    "Giving": [(25, "burden"), (26, "burden"), (27, "behavior"), (28, "behavior"), (29, "fruit")],
    "Leadership": [(30, "burden"), (31, "burden"), (32, "behavior"), (33, "behavior"), (34, "fruit")],
    "Wisdom": [(35, "burden"), (36, "burden"), (37, "behavior"), (38, "behavior"), (39, "fruit")],
    "Discernment": [(40, "burden"), (41, "burden"), (42, "behavior"), (43, "behavior"), (44, "fruit")],
    "Intercession": [(45, "burden"), (46, "burden"), (47, "behavior"), (48, "behavior"), (49, "fruit")],
}

# Tie-breaker pools (3 per gift)
TIEBREAKER: Dict[str, List[str]] = {
    "Teaching": [
        "I would rather teach truth thoroughly than motivate people emotionally.",
        "I feel uneasy when biblical teaching sacrifices accuracy for inspiration.",
        "I prioritize understanding Scripture correctly over quick spiritual results.",
    ],
    "Exhortation": [
        "I am more focused on helping people act than helping them analyze.",
        "I prefer urging people forward over explaining concepts in detail.",
        "I measure spiritual success by visible obedience and growth.",
    ],
    "Evangelism": [
        "I feel more energized around unbelievers than in long-term discipleship settings.",
        "I am comfortable redirecting conversations toward Christ quickly.",
        "I feel spiritually restless if I am not reaching new people.",
    ],
    "Mercy": [
        "I am more drawn to healing wounded people than building new initiatives.",
        "I value emotional restoration over strategic advancement.",
        "I prefer relational depth over large public influence.",
    ],
    "Helps": [
        "I prefer supporting a vision rather than defining it.",
        "I find satisfaction in execution more than direction-setting.",
        "I am comfortable staying behind the scenes long-term.",
    ],
    "Giving": [
        "I strategically evaluate where resources will produce maximum impact.",
        "I often think in terms of multiplying influence through provision.",
        "I am willing to reduce personal lifestyle to increase kingdom impact.",
    ],
    "Leadership": [
        "I naturally assume responsibility when a group lacks direction.",
        "I feel compelled to define structure rather than adapt to it.",
        "I am comfortable making decisions that affect many people.",
    ],
    "Wisdom": [
        "I am more drawn to advising others than leading them directly.",
        "I often see consequences before others recognize them.",
        "I prefer solving complex problems over managing people.",
    ],
    "Discernment": [
        "I instinctively question motives before accepting appearances.",
        "I feel tension when truth is diluted, even subtly.",
        "I would rather slow momentum than allow spiritual compromise.",
    ],
    "Intercession": [
        "I would rather pray about a situation than immediately act on it.",
        "I feel sustained burden for specific needs over long periods.",
        "I sense breakthrough often comes through persistent prayer.",
    ],
}

@dataclass
class GiftResult:
    scores: Dict[str, float]
    top3: List[Tuple[str, float]]
    primary: str
    secondary: str
    margin: float
    needs_tiebreak: bool

def _center(responses: List[int]) -> List[float]:
    mean = sum(responses) / len(responses)
    return [r - mean for r in responses]

def score_gifts(responses_1to5: List[int]) -> GiftResult:
    if len(responses_1to5) != 50:
        raise ValueError("Expected 50 responses for the core gifts assessment.")

    centered = _center(responses_1to5)

    scores: Dict[str, float] = {}
    for gift, items in GIFT_ITEMS.items():
        total = 0.0
        wsum = 0.0
        for idx, t in items:
            w = TYPE_WEIGHTS[t]
            total += centered[idx] * w
            wsum += w
        scores[gift] = total / wsum if wsum else 0.0

    ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    primary, pscore = ordered[0]
    secondary, sscore = ordered[1]
    margin = pscore - sscore

    # margin threshold can be tuned; start conservative
    needs_tiebreak = margin < 0.12

    return GiftResult(
        scores=scores,
        top3=ordered[:3],
        primary=primary,
        secondary=secondary,
        margin=margin,
        needs_tiebreak=needs_tiebreak,
    )

def apply_tiebreak(
    base: GiftResult,
    primary_tie: List[int],
    secondary_tie: List[int],
) -> GiftResult:
    """Re-score only the top2 gifts using tie-break items (3 each)."""
    if len(primary_tie) != 3 or len(secondary_tie) != 3:
        raise ValueError("Expected 3 tie-break responses for each of primary/secondary.")

    # Tie-breaker uses plain average (already discriminative), lightly blended in.
    p_tie = sum(primary_tie) / 3.0
    s_tie = sum(secondary_tie) / 3.0

    # Blend: 70% base, 30% tie (tunable)
    new_scores = dict(base.scores)
    new_scores[base.primary] = 0.7 * base.scores[base.primary] + 0.3 * (p_tie - 3.0) / 2.0
    new_scores[base.secondary] = 0.7 * base.scores[base.secondary] + 0.3 * (s_tie - 3.0) / 2.0

    ordered = sorted(new_scores.items(), key=lambda kv: kv[1], reverse=True)
    primary, pscore = ordered[0]
    secondary, sscore = ordered[1]
    margin = pscore - sscore

    return GiftResult(
        scores=new_scores,
        top3=ordered[:3],
        primary=primary,
        secondary=secondary,
        margin=margin,
        needs_tiebreak=False,
    )
