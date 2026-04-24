from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class DocumentMetadata:
    title: str
    docType: str
    path: str
    tags: list[str]


@dataclass(frozen=True)
class MarkdownChunk:
    id: str
    documentId: str
    metadata: DocumentMetadata
    heading: str
    content: str


HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$")


def extractMetadata(markdown: str, path: Path) -> DocumentMetadata:
    if not markdown.strip():
        raise ValueError(f"{path} 内容为空")
    lines = markdown.splitlines()
    title = next((line.lstrip("# ").strip() for line in lines if line.startswith("# ")), path.stem)
    docType = _inferDocType(path, markdown)
    tags = _extractTags(markdown)
    return DocumentMetadata(title=title, docType=docType, path=str(path), tags=tags)


def chunkMarkdown(markdown: str, path: Path) -> list[MarkdownChunk]:
    metadata = extractMetadata(markdown, path)
    sections = _splitByHeadings(markdown)
    documentId = str(path)
    chunks: list[MarkdownChunk] = []
    for index, (heading, body) in enumerate(sections):
        content = body.strip()
        if not content:
            continue
        chunkId = f"{documentId}#{index}"
        chunks.append(
            MarkdownChunk(
                id=chunkId,
                documentId=documentId,
                metadata=metadata,
                heading=heading,
                content=content,
            )
        )
    return chunks


def _splitByHeadings(markdown: str) -> list[tuple[str, str]]:
    currentHeading = "文档概览"
    currentLines: list[str] = []
    sections: list[tuple[str, str]] = []
    for line in markdown.splitlines():
        match = HEADING_PATTERN.match(line)
        if match:
            _appendSection(sections, currentHeading, currentLines)
            currentHeading = match.group(2).strip()
            currentLines = [line]
            continue
        currentLines.append(line)
    _appendSection(sections, currentHeading, currentLines)
    return sections


def _appendSection(sections: list[tuple[str, str]], heading: str, lines: list[str]) -> None:
    content = "\n".join(lines).strip()
    if content:
        sections.append((heading, content))


def _inferDocType(path: Path, markdown: str) -> str:
    lowered = f"{path.name}\n{markdown[:500]}".lower()
    for docType in ["runbook", "incident", "service", "faq"]:
        if docType in lowered:
            return docType
    return "doc"


def _extractTags(markdown: str) -> list[str]:
    for line in markdown.splitlines()[:20]:
        if line.lower().startswith("tags:"):
            return [tag.strip() for tag in line.split(":", 1)[1].split(",") if tag.strip()]
    return []
