"""技术名词按词边界匹配，避免把 JavaScript 识别成 Java。"""

import re


def contains_skill(text: str, skill: str) -> bool:
    if re.search(r"[a-zA-Z]", skill):
        pattern = rf"(?<![a-zA-Z0-9_]){re.escape(skill)}(?![a-zA-Z0-9_+#])"
        return bool(re.search(pattern, text, re.IGNORECASE))
    return skill.casefold() in text.casefold()
