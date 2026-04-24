from app.core.config import getSettings
from app.rag.knowledge_lint import lintKnowledgeDirectory


def main() -> None:
    settings = getSettings()
    issues = lintKnowledgeDirectory(settings.knowledgeDir)
    if not issues:
        print(f"知识库检查通过：{settings.knowledgeDir}")
        return
    for issue in issues:
        print(f"[{issue.level}] {issue.path}: {issue.message}")
    errorCount = sum(1 for issue in issues if issue.level == "error")
    warningCount = sum(1 for issue in issues if issue.level == "warning")
    print(f"共发现 {errorCount} 个错误，{warningCount} 个警告。")
    if errorCount:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
