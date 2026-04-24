from app.core.config import getSettings
from app.rag.ingestion import ingestKnowledge
from app.rag.vector_store import SQLiteVectorStore


def main() -> None:
    settings = getSettings()
    store = SQLiteVectorStore(settings.databasePath)
    documents, chunks = ingestKnowledge(settings.knowledgeDir, store, settings.vectorDimension)
    print(f"已导入文档 {documents} 份，chunk {chunks} 个")


if __name__ == "__main__":
    main()
