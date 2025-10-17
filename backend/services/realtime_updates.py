# Real-time Document Updates and Incremental Indexing
import logging
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import asyncio
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


class DocumentChangeType:
    """Types of document changes"""

    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"


class RealtimeUpdateService:
    """
    Real-time document update service.

    Features:
    - Watch for document changes
    - Incremental re-indexing
    - Automatic vector updates
    - Change notifications

    Benefits:
    - Always up-to-date index
    - No manual re-indexing needed
    - Minimal downtime
    """

    def __init__(
        self, document_processor, embedding_service, milvus_manager, bm25_indexer
    ):
        self.document_processor = document_processor
        self.embedding_service = embedding_service
        self.milvus_manager = milvus_manager
        self.bm25_indexer = bm25_indexer

        # Track document states
        self.document_hashes: Dict[str, str] = {}
        self.watched_directories: Set[str] = set()

        # Update queue
        self.update_queue: asyncio.Queue = asyncio.Queue()
        self.is_running = False

        # Statistics
        self.stats = {
            "documents_watched": 0,
            "updates_processed": 0,
            "creates": 0,
            "modifications": 0,
            "deletions": 0,
        }

    async def start_watching(
        self, directories: List[str], file_extensions: Optional[List[str]] = None
    ):
        """
        Start watching directories for changes.

        Args:
            directories: List of directories to watch
            file_extensions: File extensions to watch (e.g., ['.pdf', '.docx'])
        """
        try:
            self.watched_directories.update(directories)
            self.is_running = True

            # Start watcher task
            asyncio.create_task(self._watch_directories(directories, file_extensions))

            # Start processor task
            asyncio.create_task(self._process_updates())

            logger.info(f"Started watching {len(directories)} directories")

        except Exception as e:
            logger.error(f"Failed to start watching: {e}")

    async def stop_watching(self):
        """Stop watching for changes"""
        self.is_running = False
        logger.info("Stopped watching for changes")

    async def _watch_directories(
        self, directories: List[str], file_extensions: Optional[List[str]]
    ):
        """Watch directories for file changes"""
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler

            class ChangeHandler(FileSystemEventHandler):
                def __init__(self, update_service):
                    self.update_service = update_service

                def on_created(self, event):
                    if not event.is_directory:
                        asyncio.create_task(
                            self.update_service._handle_change(
                                event.src_path, DocumentChangeType.CREATED
                            )
                        )

                def on_modified(self, event):
                    if not event.is_directory:
                        asyncio.create_task(
                            self.update_service._handle_change(
                                event.src_path, DocumentChangeType.MODIFIED
                            )
                        )

                def on_deleted(self, event):
                    if not event.is_directory:
                        asyncio.create_task(
                            self.update_service._handle_change(
                                event.src_path, DocumentChangeType.DELETED
                            )
                        )

            observer = Observer()
            handler = ChangeHandler(self)

            for directory in directories:
                observer.schedule(handler, directory, recursive=True)

            observer.start()

            # Keep watching
            while self.is_running:
                await asyncio.sleep(1)

            observer.stop()
            observer.join()

        except ImportError:
            logger.warning("watchdog not installed, using polling instead")
            await self._poll_directories(directories, file_extensions)
        except Exception as e:
            logger.error(f"Directory watching failed: {e}")

    async def _poll_directories(
        self,
        directories: List[str],
        file_extensions: Optional[List[str]],
        interval: int = 60,
    ):
        """Poll directories for changes (fallback)"""
        while self.is_running:
            try:
                for directory in directories:
                    await self._scan_directory(directory, file_extensions)

                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"Polling failed: {e}")
                await asyncio.sleep(interval)

    async def _scan_directory(
        self, directory: str, file_extensions: Optional[List[str]]
    ):
        """Scan directory for changes"""
        try:
            path = Path(directory)

            for file_path in path.rglob("*"):
                if not file_path.is_file():
                    continue

                # Check extension
                if file_extensions and file_path.suffix not in file_extensions:
                    continue

                # Check if file changed
                file_hash = self._calculate_file_hash(str(file_path))
                stored_hash = self.document_hashes.get(str(file_path))

                if stored_hash is None:
                    # New file
                    await self._handle_change(
                        str(file_path), DocumentChangeType.CREATED
                    )
                elif stored_hash != file_hash:
                    # Modified file
                    await self._handle_change(
                        str(file_path), DocumentChangeType.MODIFIED
                    )

        except Exception as e:
            logger.debug(f"Directory scan failed: {e}")

    async def _handle_change(self, file_path: str, change_type: str):
        """Handle file change"""
        try:
            # Add to update queue
            await self.update_queue.put(
                {
                    "file_path": file_path,
                    "change_type": change_type,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            logger.info(f"Detected {change_type}: {file_path}")

        except Exception as e:
            logger.error(f"Failed to handle change: {e}")

    async def _process_updates(self):
        """Process updates from queue"""
        while self.is_running:
            try:
                # Get update from queue
                update = await asyncio.wait_for(self.update_queue.get(), timeout=1.0)

                # Process update
                await self._process_single_update(update)

                self.stats["updates_processed"] += 1

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Update processing failed: {e}")

    async def _process_single_update(self, update: Dict[str, Any]):
        """Process a single update"""
        try:
            file_path = update["file_path"]
            change_type = update["change_type"]

            if change_type == DocumentChangeType.CREATED:
                await self._handle_create(file_path)
                self.stats["creates"] += 1

            elif change_type == DocumentChangeType.MODIFIED:
                await self._handle_modify(file_path)
                self.stats["modifications"] += 1

            elif change_type == DocumentChangeType.DELETED:
                await self._handle_delete(file_path)
                self.stats["deletions"] += 1

            logger.info(f"Processed {change_type} for {file_path}")

        except Exception as e:
            logger.error(f"Failed to process update: {e}")

    async def _handle_create(self, file_path: str):
        """Handle new document"""
        try:
            # Generate document ID
            document_id = self._generate_document_id(file_path)

            # Process document
            text = await self._extract_text(file_path)
            chunks = self.document_processor.chunk_text(text, document_id)

            # Generate embeddings
            chunk_texts = [chunk.text for chunk in chunks]
            embeddings = await self.embedding_service.embed_batch(chunk_texts)

            # Store in Milvus
            metadata_list = [
                {
                    "id": chunk.chunk_id,
                    "document_id": document_id,
                    "text": chunk.text,
                    "file_path": file_path,
                    "chunk_index": chunk.chunk_index,
                }
                for chunk in chunks
            ]

            await self.milvus_manager.insert_embeddings(
                embeddings=embeddings, metadata=metadata_list
            )

            # Index in BM25
            bm25_chunks = [
                {"id": chunk.chunk_id, "text": chunk.text} for chunk in chunks
            ]
            await self.bm25_indexer.index_chunks(bm25_chunks)

            # Update hash
            file_hash = self._calculate_file_hash(file_path)
            self.document_hashes[file_path] = file_hash

            logger.info(f"Indexed new document: {file_path} ({len(chunks)} chunks)")

        except Exception as e:
            logger.error(f"Failed to handle create: {e}")

    async def _handle_modify(self, file_path: str):
        """Handle modified document"""
        try:
            # Delete old version
            await self._handle_delete(file_path)

            # Index new version
            await self._handle_create(file_path)

            logger.info(f"Re-indexed modified document: {file_path}")

        except Exception as e:
            logger.error(f"Failed to handle modify: {e}")

    async def _handle_delete(self, file_path: str):
        """Handle deleted document"""
        try:
            document_id = self._generate_document_id(file_path)

            # Delete from Milvus
            expr = f'document_id == "{document_id}"'
            await self.milvus_manager.delete(expr)

            # Remove from hash tracking
            if file_path in self.document_hashes:
                del self.document_hashes[file_path]

            logger.info(f"Deleted document from index: {file_path}")

        except Exception as e:
            logger.error(f"Failed to handle delete: {e}")

    def _generate_document_id(self, file_path: str) -> str:
        """Generate consistent document ID from file path"""
        return hashlib.md5(file_path.encode()).hexdigest()

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate file hash"""
        try:
            with open(file_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.debug(f"Hash calculation failed: {e}")
            return ""

    async def _extract_text(self, file_path: str) -> str:
        """Extract text from file"""
        # Use existing document processor
        try:
            extension = Path(file_path).suffix.lower()

            if extension == ".txt":
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
            elif extension == ".pdf":
                # Use PDF extraction
                import fitz

                doc = fitz.open(file_path)
                text = ""
                for page in doc:
                    text += page.get_text()
                doc.close()
                return text
            else:
                return ""
        except Exception as e:
            logger.debug(f"Text extraction failed: {e}")
            return ""

    def get_stats(self) -> Dict[str, Any]:
        """Get update statistics"""
        return {
            **self.stats,
            "is_running": self.is_running,
            "watched_directories": len(self.watched_directories),
            "queue_size": self.update_queue.qsize(),
        }


def create_realtime_update_service(
    document_processor, embedding_service, milvus_manager, bm25_indexer
) -> RealtimeUpdateService:
    """Factory function"""
    return RealtimeUpdateService(
        document_processor, embedding_service, milvus_manager, bm25_indexer
    )
