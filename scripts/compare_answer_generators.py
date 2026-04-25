import argparse
import json
import os
from pathlib import Path

from app.core.config import getSettings
from app.evaluation.evaluate import evaluate


def main() -> None:
    parser = argparse.ArgumentParser(description="比较 template / LLM answer generator 的离线评测结果")
    parser.add_argument("--dataset", default="app/evaluation/sample_dataset.jsonl")
    parser.add_argument("--generators", default="template,openai")
    args = parser.parse_args()
    reports = []
    for generator in [item.strip() for item in args.generators.split(",") if item.strip()]:
        reports.append(_evaluateGenerator(generator, Path(args.dataset)))
    print(json.dumps({"reports": reports}, ensure_ascii=False, indent=2))


def _evaluateGenerator(generator: str, datasetPath: Path) -> dict:
    previousGenerator = os.environ.get("ANSWER_GENERATOR")
    os.environ["ANSWER_GENERATOR"] = generator
    getSettings.cache_clear()
    try:
        report = evaluate(datasetPath)
        return {
            "generator": generator,
            "status": "ok",
            "summary": report["summary"],
        }
    except Exception as error:
        return {
            "generator": generator,
            "status": "skipped",
            "reason": str(error),
        }
    finally:
        _restoreEnv("ANSWER_GENERATOR", previousGenerator)
        getSettings.cache_clear()


def _restoreEnv(name: str, value: str | None) -> None:
    if value is None:
        os.environ.pop(name, None)
        return
    os.environ[name] = value


if __name__ == "__main__":
    main()
