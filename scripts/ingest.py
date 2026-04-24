from app.core.config import getSettings
from app.rag.ingestion import ingestKnowledge
from app.rag.vector_store import SQLiteVectorStore


def main() -> None:
    settings = getSettings()
    store = SQLiteVectorStore(settings.databasePath)
    stats = ingestKnowledge(settings.knowledgeDir, store, settings.vectorDimension)
    print(
        "已导入文档 {documents} 份，chunk {chunks} 个，按类型统计 {docTypes}".format(
            documents=stats["indexedDocuments"],
            chunks=stats["indexedChunks"],
            docTypes=stats["indexedByDocType"],
        )
    )


if __name__ == "__main__":
    main()
