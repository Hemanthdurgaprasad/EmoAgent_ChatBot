"""
Crisis detection middleware — multi-layer approach.
Layer 1: Direct keyword matching (fast, catches obvious cases)
Layer 2: Pattern matching (catches indirect expressions)
Layer 3: Context scoring (weighs multiple weak signals together)
"""

import re

# ── Layer 1: Direct high-confidence keywords ──────────────────────────────────
# These alone are enough to trigger the safety response

HIGH_CONFIDENCE_KEYWORDS = [
    # Suicidal ideation
    "suicide", "suicidal", "kill myself", "end my life",
    "take my own life", "take my life", "end it all",
    "don't want to live", "dont want to live",
    "want to die", "wanna die", "wish i was dead",
    "better off dead", "better off without me",
    "no reason to live", "not worth living",
    # Self harm
    "self harm", "self-harm", "selfharm",
    "cut myself", "cutting myself", "hurt myself",
    "hurting myself", "harm myself",
    # Crisis
    "overdose", "od myself", "pills to die",
    "jump off", "hang myself", "hanging myself",
]

# ── Layer 2: Indirect patterns (regex) ────────────────────────────────────────
# Catches phrasing that doesn't use direct keywords

INDIRECT_PATTERNS = [
    r"don['\']?t want to (be here|exist|wake up|continue)",
    r"can['\']?t (go on|do this anymore|keep going|take it anymore)",
    r"(no|nothing) (left|to live for|matters anymore)",
    r"(world|everyone) (would be )?better (off )?without me",
    r"(tired|done) (of|with) (living|life|everything|fighting)",
    r"(thinking about|thought about|planning to) (end|ending) (it|my life|everything)",
    r"(feel|feeling) (like|as if) (i['\']?m )?dying inside",
    r"(make|making) (it|the pain) stop (forever|permanently)",
    r"(been|started) (cutting|hurting|harming) (myself|my)",
    r"(took|taking|swallowed) (too many|all my|a bunch of) (pills|medication|tablets)",
    r"(gave|giving) (away|up) (everything|my stuff|my things|my belongings)",
    r"(wrote|writing|left) (a )?( goodbye |suicide )?note",
    r"(last|final) (time|day|night|message|goodbye)",
    r"nobody (cares|would notice|would miss) (if i|me)",
    r"(completely|totally|absolutely) (alone|hopeless|worthless|empty)",
]

# ── Layer 3: Weak signals — need multiple to trigger ─────────────────────────
# These alone are NOT enough but combined raise concern

WEAK_SIGNALS = [
    "hopeless", "worthless", "useless", "meaningless",
    "empty", "numb", "hollow", "broken",
    "burden", "pointless", "exhausted",
    "give up", "giving up", "can't anymore",
    "hate myself", "hate my life",
    "disappear", "run away", "escape",
    "nobody cares", "no one cares", "all alone",
    "trapped", "stuck", "no way out",
    "dark thoughts", "bad thoughts",
    "so tired", "done with everything",
]

# Weak signal threshold — how many needed to trigger
WEAK_SIGNAL_THRESHOLD = 3

# ── Safety message ────────────────────────────────────────────────────────────

SAFETY_MESSAGE = """I want to pause and check in with you. What you just shared is important, and I want to make sure you're safe right now.

If you're having thoughts of hurting yourself or ending your life, please reach out to someone who can help immediately:

**India crisis helplines (free, confidential):**
- iCall: 9152987821 — Mon to Sat, 8am–10pm
- Vandrevala Foundation: 1860-2662-345 — 24/7
- AASRA: 9820466627 — 24/7
- iCall WhatsApp: +91 9152987821

You don't have to carry this alone. A real person is ready to listen right now.

---

"""


# ── Detection function ────────────────────────────────────────────────────────

def check_for_crisis(text: str) -> bool:
    """
    Multi-layer crisis detection.
    Returns True if the message contains crisis signals.
    """
    if not text or len(text.strip()) < 3:
        return False

    text_lower = text.lower().strip()

    # Layer 1: Direct keywords — any single match triggers
    for keyword in HIGH_CONFIDENCE_KEYWORDS:
        if keyword in text_lower:
            return True

    # Layer 2: Indirect patterns — any single match triggers
    for pattern in INDIRECT_PATTERNS:
        if re.search(pattern, text_lower):
            return True

    # Layer 3: Weak signals — need WEAK_SIGNAL_THRESHOLD matches
    weak_count = sum(1 for signal in WEAK_SIGNALS if signal in text_lower)
    if weak_count >= WEAK_SIGNAL_THRESHOLD:
        return True

    return False


def get_crisis_level(text: str) -> str:
    """
    Returns crisis severity: "none", "low", "medium", "high"
    Useful for logging and future analytics.
    """
    if not text:
        return "none"

    text_lower = text.lower().strip()

    # High — direct keyword
    for keyword in HIGH_CONFIDENCE_KEYWORDS:
        if keyword in text_lower:
            return "high"

    # Medium — indirect pattern
    for pattern in INDIRECT_PATTERNS:
        if re.search(pattern, text_lower):
            return "medium"

    # Low — multiple weak signals
    weak_count = sum(1 for signal in WEAK_SIGNALS if signal in text_lower)
    if weak_count >= WEAK_SIGNAL_THRESHOLD:
        return "low"

    return "none"


def prepend_safety_message(response: str) -> str:
    """Prepends the safety message before the AI response."""
    return SAFETY_MESSAGE + response