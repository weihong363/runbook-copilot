from pathlib import Path

from app.core.config import PROJECT_ROOT, _resolveProjectPath


def testResolveProjectPathUsesProjectRootForRelativePath() -> None:
    resolved = _resolveProjectPath("knowledge")

    assert resolved == PROJECT_ROOT / "knowledge"


def testResolveProjectPathKeepsAbsolutePath() -> None:
    absolute = Path("/tmp/runbook-copilot-test")

    assert _resolveProjectPath(str(absolute)) == absolute
