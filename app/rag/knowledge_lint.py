from dataclasses import dataclass
from pathlib import Path

from app.rag.chunking import DocumentMetadata, chunkMarkdown, extractMetadata

SUPPORTED_DOC_TYPES = {"runbook", "incident", "service", "faq"}


@dataclass(frozen=True)
class KnowledgeLintIssue:
    level: str
    path: str
    message: str


def lintKnowledgeDirectory(knowledgeDir: Path) -> list[KnowledgeLintIssue]:
    if not knowledgeDir.exists():
        raise FileNotFoundError(f"知识目录不存在: {knowledgeDir}")
    issues: list[KnowledgeLintIssue] = []
    for path in sorted(knowledgeDir.rglob("*.md")):
        issues.extend(lintKnowledgeDocument(path))
    return issues


def lintKnowledgeDocument(path: Path) -> list[KnowledgeLintIssue]:
    markdown = path.read_text(encoding="utf-8")
    issues: list[KnowledgeLintIssue] = []
    try:
        metadata = extractMetadata(markdown, path)
    except ValueError as error:
        return [KnowledgeLintIssue(level="error", path=str(path), message=str(error))]
    chunks = chunkMarkdown(markdown, path)
    issues.extend(_validateMetadata(path, markdown, metadata))
    issues.extend(_validateChunkStructure(path, metadata, chunks))
    return issues


def _validateMetadata(path: Path, markdown: str, metadata: DocumentMetadata) -> list[KnowledgeLintIssue]:
    issues: list[KnowledgeLintIssue] = []
    if not any(line.startswith("# ") for line in markdown.splitlines()):
        issues.append(KnowledgeLintIssue("error", str(path), "缺少一级标题 `# 标题`。"))
    if not metadata.tags:
        issues.append(KnowledgeLintIssue("error", str(path), "缺少 `tags:` 行，且应放在文档前 20 行内。"))
    if metadata.docType not in SUPPORTED_DOC_TYPES:
        issues.append(
            KnowledgeLintIssue(
                "error",
                str(path),
                "无法识别文档类型，请在文件名、标题或内容中明确包含 runbook / incident / service / faq。",
            )
        )
    if not metadata.service:
        issues.append(
            KnowledgeLintIssue(
                "warning",
                str(path),
                "未识别到 service，建议在文件名、标题或 tags 中包含 service/api/worker/job 名称。",
            )
        )
    if metadata.service and metadata.service not in metadata.tags:
        issues.append(
            KnowledgeLintIssue(
                "warning",
                str(path),
                f"建议把 service `{metadata.service}` 也加入 tags，便于检索和过滤。",
            )
        )
    return issues


def _validateChunkStructure(path: Path, metadata: DocumentMetadata, chunks: list) -> list[KnowledgeLintIssue]:
    issues: list[KnowledgeLintIssue] = []
    if not chunks:
        issues.append(KnowledgeLintIssue("error", str(path), "文档没有可索引的 section。"))
        return issues
    h2Count = sum(1 for chunk in chunks if chunk.headingLevel == 2)
    if metadata.docType in {"runbook", "incident", "service", "faq"} and h2Count == 0:
        issues.append(KnowledgeLintIssue("error", str(path), "至少需要一个二级标题 `## ...`。"))
    if metadata.docType == "runbook":
        expectedHeadings = {"适用场景", "快速判断", "处理步骤"}
        actualHeadings = {chunk.heading for chunk in chunks}
        missing = sorted(expectedHeadings - actualHeadings)
        if missing:
            issues.append(
                KnowledgeLintIssue(
                    "warning",
                    str(path),
                    f"建议补齐 runbook 常用章节：{', '.join(missing)}。",
                )
            )
    return issues
