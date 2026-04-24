import re

TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_\-.]+|[\u4e00-\u9fff]")


def tokenize(text: str) -> list[str]:
    if text is None:
        raise ValueError("text 不能为 None")
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]
