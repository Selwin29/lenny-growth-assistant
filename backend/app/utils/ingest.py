import asyncio
import sys
import logging
from app.services.rag_service import RAGService

# Configure logging to show progress in console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

async def main():
    rag = RAGService()
    print("==================================================")
    print("Lenny Growth Assistant - Ingesting Transcripts")
    print("==================================================")
    try:
        await rag.download_and_ingest()
        print("==================================================")
        print("SUCCESS: Ingestion completed successfully!")
        print("==================================================")
    except Exception as e:
        print(f"ERROR: Ingestion failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
