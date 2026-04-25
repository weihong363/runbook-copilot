from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class DocumentMetadata:
    title: str
    docType: str
    path: str
    tags: list[str]
    service: str


@dataclass(frozen=True)
class MarkdownChunk:
    id: str
    documentId: str
    metadata: DocumentMetadata
    heading: str
    headingLevel: int
    content: str


HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$")


def extractMetadata(markdown: str, path: Path) -> DocumentMetadata:
    if not markdown.strip():
        raise ValueError(f"{path} 内容为空")
    lines = markdown.splitlines()
    title = next((line.lstrip("# ").strip() for line in lines if line.startswith("# ")), path.stem)
    docType = _inferDocType(path, markdown)
    tags = _extractTags(markdown)
    service = _extractService(path, title, tags)
    return DocumentMetadata(title=title, docType=docType, path=str(path), tags=tags, service=service)


def chunkMarkdown(markdown: str, path: Path) -> list[MarkdownChunk]:
    metadata = extractMetadata(markdown, path)
    sections = _splitByHeadings(markdown)
    documentId = str(path)
    chunks: list[MarkdownChunk] = []
    for index, (heading, headingLevel, body) in enumerate(sections):
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
                headingLevel=headingLevel,
                content=content,
            )
        )
    return chunks


def _splitByHeadings(markdown: str) -> list[tuple[str, int, str]]:
    currentHeading = "文档概览"
    currentHeadingLevel = 0
    currentLines: list[str] = []
    sections: list[tuple[str, int, str]] = []
    for line in markdown.splitlines():
        match = HEADING_PATTERN.match(line)
        if match:
            _appendSection(sections, currentHeading, currentHeadingLevel, currentLines)
            currentHeading = match.group(2).strip()
            currentHeadingLevel = len(match.group(1))
            currentLines = [line]
            continue
        currentLines.append(line)
    _appendSection(sections, currentHeading, currentHeadingLevel, currentLines)
    return _mergeShortSections(sections)


def _appendSection(
    sections: list[tuple[str, int, str]],
    heading: str,
    headingLevel: int,
    lines: list[str],
) -> None:
    content = "\n".join(lines).strip()
    if content:
        sections.append((heading, headingLevel, content))


def _mergeShortSections(sections: list[tuple[str, int, str]]) -> list[tuple[str, int, str]]:
    merged: list[tuple[str, int, str]] = []
    for heading, headingLevel, content in sections:
        body = _stripHeadingLine(content).strip()
        if merged and headingLevel >= 3 and len(body) < 20:
            previousHeading, previousLevel, previousContent = merged[-1]
            merged[-1] = (
                previousHeading,
                previousLevel,
                f"{previousContent}\n\n补充小节 {heading}:\n{body}",
            )
            continue
        merged.append((heading, headingLevel, content))
    return merged


def _inferDocType(path: Path, markdown: str) -> str:
    lowered = f"{path.name}\n{markdown[:500]}".lower()
    for docType in ["runbook", "incident", "faq", "service"]:
        if docType in lowered:
            return docType
    return "doc"


def _extractTags(markdown: str) -> list[str]:
    for line in markdown.splitlines()[:20]:
        if line.lower().startswith("tags:"):
            return [tag.strip().lower() for tag in line.split(":", 1)[1].split(",") if tag.strip()]
    return []


def _extractService(path: Path, title: str, tags: list[str]) -> str:
    for tag in tags:
        if any(keyword in tag for keyword in ["service", "api", "worker", "job"]):
            return tag
    normalizedPath = path.stem.lower().replace("_", "-")
    if normalizedPath.startswith(("runbook-", "incident-", "service-", "faq-")):
        candidate = normalizedPath.split("-", 1)[1]
        if candidate:
            return candidate
    loweredTitle = title.lower()
    serviceMatch = re.search(r"([a-z0-9]+(?:[-_][a-z0-9]+)*(?:service|api|worker|job))", loweredTitle)
    if serviceMatch:
        return serviceMatch.group(1).replace("_", "-")
    return ""


def _stripHeadingLine(content: str) -> str:
    lines = content.splitlines()
    if lines and HEADING_PATTERN.match(lines[0]):
        return "\n".join(lines[1:])
    return content
