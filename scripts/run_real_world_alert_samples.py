import argparse
import json
from pathlib import Path
from typing import Any
from urllib import request


def main() -> None:
    parser = argparse.ArgumentParser(description="调用 /api/incidents/events 回放公开事故告警样本")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--dataset", default="app/evaluation/real_world_alert_samples.jsonl")
    parser.add_argument("--post-feedback", action="store_true")
    args = parser.parse_args()
    samples = _loadSamples(Path(args.dataset))
    results = [_postSample(args.base_url, sample, args.post_feedback) for sample in samples]
    lowScore = [item for item in results if item["rating"] <= 2 or item["useful"] is False]
    print(
        json.dumps(
            {
                "total": len(results),
                "useful": sum(1 for item in results if item["useful"]),
                "notUseful": len(lowScore),
                "lowScoreCases": lowScore,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def _loadSamples(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"样本文件不存在: {path}")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _postSample(baseUrl: str, sample: dict[str, Any], postFeedback: bool) -> dict[str, Any]:
    response = _postJson(f"{baseUrl}/api/incidents/events", sample["input"])
    rating, useful, matchedTerms = _rateAnswer(response, sample["expectedTerms"])
    if postFeedback:
        _postJson(
            f"{baseUrl}/api/feedback",
            {
                "incidentId": response["incidentId"],
                "rating": rating,
                "useful": useful,
                "reason": "topic_match" if useful else "missing_knowledge",
                "comment": f"公开样本回放: {sample['name']}; matchedTerms={matchedTerms}",
            },
        )
    return {
        "name": sample["name"],
        "incidentId": response["incidentId"],
        "rating": rating,
        "useful": useful,
        "matchedTerms": matchedTerms,
        "topCitationPaths": [citation["path"] for citation in response["answer"]["citations"][:3]],
        "summary": response["answer"]["summary"],
        "sourceUrl": sample["sourceUrl"],
    }


def _rateAnswer(response: dict[str, Any], expectedTerms: list[str]) -> tuple[int, bool, list[str]]:
    haystack = " ".join(
        [
            response["answer"]["summary"],
            response["answer"]["nextAction"],
            " ".join(response["answer"]["likelyCauses"]),
            " ".join(response["answer"]["steps"]),
            " ".join(
                f"{citation['title']} {citation['heading']} {citation['excerpt']}"
                for citation in response["answer"]["citations"]
            ),
        ]
    ).lower()
    matched = [term for term in expectedTerms if term.lower() in haystack]
    coverage = len(matched) / max(1, len(expectedTerms))
    if coverage >= 0.5:
        return 4, True, matched
    if coverage >= 0.25:
        return 2, False, matched
    return 1, False, matched


def _postJson(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    httpRequest = request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with request.urlopen(httpRequest, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


if __name__ == "__main__":
    main()
