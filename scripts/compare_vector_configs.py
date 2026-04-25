import argparse
import json
from pathlib import Path

from app.core.config import getSettings
from app.evaluation.evaluate import evaluate


def main() -> None:
    parser = argparse.ArgumentParser(description="比较不同 embedding / vector 配置的离线评测结果")
    parser.add_argument(
        "--dataset",
        default="app/evaluation/sample_dataset.jsonl",
        help="JSONL 评测集路径",
    )
    parser.add_argument(
        "--providers",
        default="hash,sentence-transformers",
        help="逗号分隔的 embedding provider 列表",
    )
    args = parser.parse_args()
    reports = []
    baseSettings = getSettings()
    for provider in [item.strip() for item in args.providers.split(",") if item.strip()]:
        report = _evaluateProvider(provider, Path(args.dataset), baseSettings.embeddingModel)
        reports.append(report)
    print(json.dumps({"reports": reports}, ensure_ascii=False, indent=2))


def _evaluateProvider(provider: str, datasetPath: Path, modelName: str) -> dict:
    import os

    previousProvider = os.environ.get("EMBEDDING_PROVIDER")
    previousModel = os.environ.get("EMBEDDING_MODEL")
    os.environ["EMBEDDING_PROVIDER"] = provider
    os.environ["EMBEDDING_MODEL"] = modelName
    getSettings.cache_clear()
    try:
        report = evaluate(datasetPath)
        return {
            "provider": provider,
            "status": "ok",
            "summary": report["summary"],
        }
    except Exception as error:
        return {
            "provider": provider,
            "status": "skipped",
            "reason": str(error),
        }
    finally:
        _restoreEnv("EMBEDDING_PROVIDER", previousProvider)
        _restoreEnv("EMBEDDING_MODEL", previousModel)
        getSettings.cache_clear()


def _restoreEnv(name: str, value: str | None) -> None:
    import os

    if value is None:
        os.environ.pop(name, None)
        return
    os.environ[name] = value


if __name__ == "__main__":
    main()
