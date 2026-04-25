from app.core.config import getSettings
from app.rag.embedding_provider import createEmbeddingProvider
from app.rag.factory import createVectorStore
from app.rag.ingestion import ingestKnowledge


def main() -> None:
    settings = getSettings()
    store = createVectorStore(settings)
    embeddingProvider = createEmbeddingProvider(settings.embeddingProvider, settings.vectorDimension, settings.embeddingModel)
    stats = ingestKnowledge(settings.knowledgeDir, store, settings.vectorDimension, embeddingProvider)
    print(
        "已导入文档 {documents} 份，chunk {chunks} 个，合并短小节 {merged} 个，按类型统计 {docTypes}".format(
            documents=stats["indexedDocuments"],
            chunks=stats["indexedChunks"],
            merged=stats["emptySectionsMerged"],
            docTypes=stats["indexedByDocType"],
        )
    )
    for path in stats["indexedFiles"]:
        print(f"- {path}")


if __name__ == "__main__":
    main()
