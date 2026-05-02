import re
import time
from typing import Optional

BLOCKED_PATTERNS = {
    "insider_trading": {
        "patterns": [
            r"\bus(?:e|ing)\s+(insider|non.?public|private)\s+(info|information|tip|data)\b",
            r"\btrade\s+on\s+(insider|non.?public|confidential)\b",
            r"\bbefore\s+the\s+(announcement|earnings|merger|acquisition)\s+leak\b",
            r"\bi\s+(know|heard|got)\s+.{0,30}(not\s+public|insider|confidential)\b",
            r"\b(unannounced|confidential)\s+(acquisition|merger|news)\b",
            r"\btip\s+about\s+earnings\b",
            r"\bearnings\s+before\s+.+announcement\b",
        ],
        "response": "Trading on material non-public information is illegal under securities law and constitutes insider trading. Valura cannot assist with this request. If you have questions about insider trading regulations for educational purposes, I'm happy to help."
    },
    "market_manipulation": {
        "patterns": [
            r"\bpump\s+and\s+dump\b",
            r"\bpump\s+up\s+the\s+price\b",
            r"\bspread\s+(false|fake|fabricat)\w*\s+(rumor|news|info)\b",
            r"\bmanipulat\w*\s+(the\s+)?(stock|market|price)\b",
            r"\bcoordinat\w*\s+(buy|sell|trade)\w*\s+to\s+(move|pump|drive)\b",
            r"\bcoordinated\s+buying\s+scheme\b",
            r"\bwash\s+trad\w*\b",
        ],
        "response": "Market manipulation is a serious criminal offense. Valura does not support activities that artificially influence asset prices or deceive other market participants. This request cannot be processed."
    },
    "money_laundering": {
        "patterns": [
            r"\blaunder\w*\s+(money|funds|cash|proceeds)\b",
            r"\bhide\s+(the\s+)?(source|origin|trading\s+profits)\b",
            r"\bclean\s+(dirty|illegal|black)\s+(money|funds|cash)\b",
            r"\bstructur\w*\s+(cash|deposits?|transactions?)\s+to\s+avoid\b",
            r"\bsmurfing\b",
            r"\bwithout\s+reporting\s+it\b",
            r"\blayer\s+my\s+trades\b",
        ],
        "response": "Money laundering is a federal crime. Valura is a regulated platform and is legally required to report suspicious financial activity. This request has been flagged and cannot be processed."
    },
    "guaranteed_returns": {
        "patterns": [
            r"\bguarantee[ds]?\s+\d+%?\s+(return|profit|gain|yield)\b",
            r"\b(risk.?free|no.?risk)\s+(return|profit|investment|guarantee)\b",
            r"\b(always|definitely|certainly)\s+(profit|make\s+money|gain)\b",
            r"\b100%\s+(safe|guaranteed|certain|sure)\b",
            r"\bguarantee\s+me\b",
            r"\bpromise\s+me\s+my\s+money\s+will\s+double\b",
            r"\bfoolproof\s+way\b",
        ],
        "response": "No investment can guarantee returns. Making or seeking guaranteed return claims may constitute securities fraud. All investments carry risk. Valura cannot endorse or facilitate such claims."
    },
    "reckless_leverage": {
        "patterns": [
            r"\b(take|use|apply)\s+(maximum|max|full|100%)\s+leverage\b",
            r"\bmortgage\s+(my\s+)?(house|home|property)\s+(to\s+|for\b)?(invest|buy|trade)?\b",
            r"\bborrow\s+.{0,20}(invest|trade|buy\s+stocks|put\s+in)\b",
            r"\ball.?in\s+(on\s+)?(options|calls|puts|crypto|leverage)\b",
            r"\bretirement\s+savings\s+in\s+crypto\b",
            r"\bmargin\s+loan\b",
            r"\bemergency\s+fund\s+into\s+options\b",
        ],
        "response": "This appears to involve extreme leverage or borrowing against primary assets for speculative investment — a pattern associated with severe financial harm. Valura's duty of care prevents us from assisting with this request. Consider speaking with a licensed financial advisor."
    },
    "sanctions_evasion": {
        "patterns": [
            r"\bshell\s+company\s+to\s+bypass\b",
            r"\bsanctioned\s+(russian|entity|company)\b"
        ],
        "response": "Evading international sanctions is a serious offense. This request has been blocked."
    },
    "fraud": {
        "patterns": [
            r"\bfake\s+contract\b"
        ],
        "response": "Fraudulent activities are strictly prohibited."
    }
}

# Educational override patterns — if these match, the query passes even if a blocked pattern also matches
EDUCATIONAL_PATTERNS = [
    r"\b(how\s+does|what\s+is|explain|define|tell\s+me\s+about|what\s+are|history\s+of|example\s+of)\b",
    r"\b(educate|learn|understand|study|research|academic|textbook)\b",
    r"\b(illegal|illegal\w*|crime|criminal|law|regulation|compliance)\s+(surrounding|about|regarding|perspective)\b",
]

def is_educational(query: str) -> bool:
    q = query.lower()
    return any(re.search(p, q, re.IGNORECASE) for p in EDUCATIONAL_PATTERNS)

def check_safety(query: str) -> tuple[bool, Optional[str], Optional[str]]:
    """
    Returns (is_blocked, category, message).
    Runs in <10ms — pure local computation only.
    """
    if is_educational(query):
        return False, None, None
    
    q_lower = query.lower()
    for category, config in BLOCKED_PATTERNS.items():
        for pattern in config["patterns"]:
            if re.search(pattern, q_lower, re.IGNORECASE):
                return True, category, config["response"]
    
    return False, None, None
