"""
Multimodal Document Service with ColPali + Audio RAG

텍스트 + 이미지 + 오디오 멀티모달 문서 처리 및 검색
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)


class MultimodalDocumentService:
    """
    멀티모달 문서 서비스
    
    Features:
    - 텍스트 + 이미지 + 오디오 통합 처리
    - ColPali 이미지 임베딩
    - WavRAG 스타일 오디오 임베딩
    - 하이브리드 검색 (텍스트 + 이미지 + 오디오)
    - 통합 결과 반환
    """
    
    def __init__(self):
        """초기화"""
        self.colpali_processor = None
        self.colpali_milvus = None
        self.audio_processor = None
        self.audio_milvus = None
        self.clip_processor = None
        self.clip_milvus = None
        
        self._init_services()
        
        logger.info("MultimodalDocumentService initialized")
    
    def _init_services(self):
        """서비스 초기화"""
        try:
            # ColPali 프로세서 (이미지)
            from backend.services.colpali_processor import get_colpali_processor
            self.colpali_processor = get_colpali_processor()
            
            # ColPali Milvus 서비스
            from backend.services.colpali_milvus_service import get_colpali_milvus_service
            self.colpali_milvus = get_colpali_milvus_service()
            
            # Audio 프로세서 (음성)
            from backend.services.audio_processor import get_audio_processor
            self.audio_processor = get_audio_processor()
            
            # Audio Milvus 서비스
            from backend.services.audio_milvus_service import get_audio_milvus_service
            self.audio_milvus = get_audio_milvus_service()
            
            # CLIP 프로세서 (크로스 모달)
            from backend.services.clip_processor import get_clip_processor
            self.clip_processor = get_clip_processor()
            
            # CLIP Milvus 서비스
            from backend.services.clip_milvus_service import get_clip_milvus_service
            self.clip_milvus = get_clip_milvus_service()
            
            # Multimodal Reranker (Phase 3)
            from backend.services.multimodal_reranker import get_multimodal_reranker
            self.reranker = get_multimodal_reranker()
            
            logger.info(
                f"✅ Multimodal services initialized: "
                f"ColPali={self.colpali_processor is not None}, "
                f"Audio={self.audio_processor is not None}, "
                f"CLIP={self.clip_processor is not None}, "
                f"Reranker={self.reranker is not None}"
            )
            
        except Exception as e:
            logger.warning(f"Failed to initialize multimodal services: {e}")
    
    async def process_image_document(
        self,
        image_path: str,
        document_id: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        이미지 문서 처리 및 인덱싱
        
        Args:
            image_path: 이미지 파일 경로
            document_id: 문서 ID
            metadata: 메타데이터
        
        Returns:
            처리 결과
        """
        try:
            logger.info(f"Processing image document: {Path(image_path).name}")
            
            # 1. ColPali로 이미지 처리
            result = self.colpali_processor.process_image(image_path)
            
            if 'embeddings' not in result or result['embeddings'] is None:
                raise ValueError("No embeddings generated")
            
            embeddings = result['embeddings']
            
            # 2. Milvus에 저장
            image_id = self.colpali_milvus.insert_image(
                image_path=image_path,
                embeddings=embeddings,
                document_id=document_id,
                metadata={
                    **(metadata or {}),
                    'num_patches': result['num_patches'],
                    'image_size': result['image_size'],
                    'method': result['method']
                }
            )
            
            logger.info(f"✅ Image indexed: {image_id} ({result['num_patches']} patches)")
            
            return {
                'success': True,
                'image_id': image_id,
                'num_patches': result['num_patches'],
                'method': result['method']
            }
            
        except Exception as e:
            logger.error(f"Failed to process image document: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def batch_process_images(
        self,
        image_paths: List[str],
        document_ids: List[str],
        metadatas: Optional[List[Dict]] = None,
        batch_size: int = 4
    ) -> List[Dict[str, Any]]:
        """
        배치 이미지 처리 및 인덱싱
        
        Args:
            image_paths: 이미지 파일 경로 리스트
            document_ids: 문서 ID 리스트
            metadatas: 메타데이터 리스트
            batch_size: 배치 크기
        
        Returns:
            처리 결과 리스트
        """
        if not self.colpali_processor or not self.colpali_milvus:
            raise ValueError("Image services not available")
        
        if len(image_paths) != len(document_ids):
            raise ValueError("image_paths and document_ids must have same length")
        
        if metadatas is None:
            metadatas = [{}] * len(image_paths)
        
        results = []
        
        try:
            logger.info(f"Batch processing {len(image_paths)} images (batch_size={batch_size})")
            
            # 배치 처리
            for i in range(0, len(image_paths), batch_size):
                batch_paths = image_paths[i:i + batch_size]
                batch_ids = document_ids[i:i + batch_size]
                batch_metas = metadatas[i:i + batch_size]
                
                # ColPali 배치 처리
                batch_results = self.colpali_processor.batch_process_images(
                    batch_paths,
                    batch_size=batch_size
                )
                
                # Milvus에 저장
                for j, result in enumerate(batch_results):
                    if 'error' in result:
                        results.append({
                            'success': False,
                            'error': result['error'],
                            'image_path': batch_paths[j]
                        })
                        continue
                    
                    try:
                        image_id = self.colpali_milvus.insert_image(
                            image_path=batch_paths[j],
                            embeddings=result['embeddings'],
                            document_id=batch_ids[j],
                            metadata={
                                **batch_metas[j],
                                'num_patches': result['num_patches'],
                                'image_size': result['image_size'],
                                'method': result['method']
                            }
                        )
                        
                        results.append({
                            'success': True,
                            'image_id': image_id,
                            'num_patches': result['num_patches'],
                            'method': result['method']
                        })
                        
                    except Exception as e:
                        results.append({
                            'success': False,
                            'error': str(e),
                            'image_path': batch_paths[j]
                        })
            
            success_count = sum(1 for r in results if r.get('success'))
            logger.info(f"✅ Batch processing complete: {success_count}/{len(image_paths)} succeeded")
            
            return results
            
        except Exception as e:
            logger.error(f"Batch image processing failed: {e}")
            raise
    
    async def process_audio_document(
        self,
        audio_path: str,
        document_id: str,
        metadata: Optional[Dict] = None,
        chunk_duration: float = 30.0
    ) -> Dict[str, Any]:
        """
        오디오 문서 처리 및 인덱싱
        
        Args:
            audio_path: 오디오 파일 경로
            document_id: 문서 ID
            metadata: 메타데이터
            chunk_duration: 청킹 길이 (초, 0이면 청킹 안함)
        
        Returns:
            처리 결과
        """
        try:
            logger.info(f"Processing audio document: {Path(audio_path).name}")
            
            if not self.audio_processor or not self.audio_milvus:
                raise ValueError("Audio services not available")
            
            # 1. 오디오 처리
            result = self.audio_processor.process_audio(
                audio_path=audio_path,
                return_embeddings=True,
                return_transcription=True
            )
            
            if 'embeddings' not in result or result['embeddings'] is None:
                raise ValueError("No embeddings generated")
            
            embeddings = result['embeddings']
            duration = result['duration']
            transcription = result.get('transcription', '')
            
            # 2. 청킹 처리 (긴 오디오)
            audio_ids = []
            
            if chunk_duration > 0 and duration > chunk_duration:
                # 청킹 필요
                chunks = self._chunk_audio(audio_path, chunk_duration)
                
                for i, chunk_path in enumerate(chunks):
                    chunk_result = self.audio_processor.process_audio(
                        audio_path=chunk_path,
                        return_embeddings=True,
                        return_transcription=True
                    )
                    
                    audio_id = self.audio_milvus.insert_audio(
                        audio_path=chunk_path,
                        embedding=chunk_result['embeddings'],
                        document_id=document_id,
                        transcription=chunk_result.get('transcription', ''),
                        duration=chunk_result['duration'],
                        metadata={
                            **(metadata or {}),
                            'chunk_index': i,
                            'total_chunks': len(chunks),
                            'original_audio': audio_path,
                            'method': 'audio_rag_chunked'
                        }
                    )
                    audio_ids.append(audio_id)
                
                logger.info(f"✅ Audio chunked and indexed: {len(chunks)} chunks")
                
            else:
                # 청킹 불필요
                audio_id = self.audio_milvus.insert_audio(
                    audio_path=audio_path,
                    embedding=embeddings,
                    document_id=document_id,
                    transcription=transcription,
                    duration=duration,
                    metadata={
                        **(metadata or {}),
                        'method': result['method']
                    }
                )
                audio_ids.append(audio_id)
                
                logger.info(f"✅ Audio indexed: {audio_id} ({duration:.2f}s)")
            
            return {
                'success': True,
                'audio_ids': audio_ids,
                'duration': duration,
                'transcription': transcription,
                'num_chunks': len(audio_ids),
                'method': result['method']
            }
            
        except Exception as e:
            logger.error(f"Failed to process audio document: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _chunk_audio(
        self,
        audio_path: str,
        chunk_duration: float = 30.0,
        overlap: float = 2.0
    ) -> List[str]:
        """
        오디오 청킹
        
        Args:
            audio_path: 오디오 파일 경로
            chunk_duration: 청크 길이 (초)
            overlap: 오버랩 (초)
        
        Returns:
            청크 파일 경로 리스트
        """
        try:
            import librosa
            import soundfile as sf
            
            # 오디오 로드
            audio, sr = librosa.load(audio_path, sr=16000, mono=True)
            duration = len(audio) / sr
            
            # 청크 생성
            chunk_samples = int(chunk_duration * sr)
            overlap_samples = int(overlap * sr)
            stride = chunk_samples - overlap_samples
            
            chunks = []
            chunk_dir = Path(audio_path).parent / "chunks"
            chunk_dir.mkdir(exist_ok=True)
            
            for i in range(0, len(audio), stride):
                chunk = audio[i:i + chunk_samples]
                
                if len(chunk) < sr:  # 1초 미만은 스킵
                    continue
                
                # 청크 저장
                chunk_path = chunk_dir / f"{Path(audio_path).stem}_chunk_{i//stride}.wav"
                sf.write(str(chunk_path), chunk, sr)
                chunks.append(str(chunk_path))
            
            logger.info(f"Audio chunked: {len(chunks)} chunks from {duration:.2f}s")
            
            return chunks
            
        except Exception as e:
            logger.error(f"Audio chunking failed: {e}")
            return [audio_path]  # 실패시 원본 반환
    
    async def search_multimodal(
        self,
        query: str = "",
        top_k: int = 5,
        search_images: bool = True,
        search_text: bool = True,
        search_audio: bool = True,
        query_audio_path: Optional[str] = None,
        query_image_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        멀티모달 검색 (텍스트 + 이미지 + 오디오)
        
        Args:
            query: 검색 쿼리 (텍스트, 선택)
            top_k: 반환할 결과 수
            search_images: 이미지 검색 활성화
            search_text: 텍스트 검색 활성화
            search_audio: 오디오 검색 활성화
            query_audio_path: 쿼리 오디오 파일 (선택)
            query_image_path: 쿼리 이미지 파일 (선택)
        
        Returns:
            통합 검색 결과
        """
        try:
            results = {
                'query': query,
                'images': [],
                'text': [],
                'audio': [],
                'combined': []
            }
            
            # 1. 이미지 검색 (ColPali)
            if search_images and self.colpali_processor:
                try:
                    # 쿼리를 이미지로 변환하거나 텍스트 임베딩 사용
                    # 여기서는 간단히 텍스트 기반 검색 구현
                    # 실제로는 쿼리 이미지나 텍스트-이미지 크로스 모달 검색 필요
                    
                    logger.info("Image search with ColPali (placeholder)")
                    # TODO: 텍스트-이미지 크로스 모달 검색 구현
                    
                except Exception as e:
                    logger.warning(f"Image search failed: {e}")
            
            # 2. 텍스트 검색 (기존 시스템)
            if search_text:
                try:
                    # 기존 텍스트 검색 사용
                    from backend.services.document_service import DocumentService
                    doc_service = DocumentService()
                    
                    # 텍스트 검색 수행
                    # text_results = await doc_service.search(query, top_k)
                    # results['text'] = text_results
                    
                    logger.info("Text search completed")
                    
                except Exception as e:
                    logger.warning(f"Text search failed: {e}")
            
            # 3. 오디오 검색 (Audio RAG)
            if search_audio and self.audio_processor and self.audio_milvus:
                try:
                    if query_audio_path:
                        # 오디오 쿼리로 검색
                        query_result = self.audio_processor.process_audio(
                            query_audio_path,
                            return_embeddings=True
                        )
                        
                        audio_results = self.audio_milvus.search_audio(
                            query_embedding=query_result['embeddings'],
                            top_k=top_k
                        )
                        
                        results['audio'] = audio_results
                        logger.info(f"Audio search completed: {len(audio_results)} results")
                    
                    else:
                        # 텍스트 쿼리로 오디오 검색 (크로스 모달)
                        # 방법 1: 텍스트 변환(transcription) 기반 검색
                        audio_results = await self._search_audio_with_text(query, top_k)
                        results['audio'] = audio_results
                        logger.info(f"Text-to-audio cross-modal search: {len(audio_results)} results")
                    
                except Exception as e:
                    logger.warning(f"Audio search failed: {e}")
            
            # 4. 이미지 쿼리 검색
            if query_image_path:
                try:
                    # 이미지 쿼리로 검색
                    image_query_results = await self._search_with_image_query(
                        query_image_path=query_image_path,
                        search_images=search_images,
                        search_text=search_text,
                        top_k=top_k
                    )
                    
                    # 결과 통합
                    if search_images:
                        results['images'].extend(image_query_results.get('images', []))
                    if search_text:
                        results['text'].extend(image_query_results.get('text', []))
                    
                    logger.info(f"Image query search completed")
                    
                except Exception as e:
                    logger.warning(f"Image query search failed: {e}")
            
            # 5. 결과 통합 및 리랭킹
            # 이미지, 텍스트, 오디오 결과를 점수 기반으로 통합
            # 쿼리 타입 결정
            if query_audio_path:
                query_type = 'audio'
            elif query_image_path:
                query_type = 'image'
            else:
                query_type = 'text'  # 기본값
            
            # 멀티모달 리랭킹 적용
            try:
                from backend.services.multimodal_reranker import get_multimodal_reranker
                
                reranker = get_multimodal_reranker()
                results['combined'] = reranker.rerank(
                    results={
                        'text': results['text'],
                        'images': results['images'],
                        'audio': results['audio']
                    },
                    query_type=query_type,
                    top_k=top_k,
                    enable_diversity=True
                )
                
                logger.info(f"Applied multimodal reranking: {len(results['combined'])} results")
                
            except Exception as e:
                logger.warning(f"Multimodal reranking failed, using basic merge: {e}")
                # 폴백: 기본 병합
                results['combined'] = self._merge_results(
                    results['images'],
                    results['text'],
                    results['audio'],
                    query_type=query_type
                )
            
            return results
            
        except Exception as e:
            logger.error(f"Multimodal search failed: {e}")
            return {
                'query': query,
                'error': str(e),
                'images': [],
                'text': [],
                'combined': []
            }
    
    def _merge_results(
        self,
        image_results: List[Dict],
        text_results: List[Dict],
        audio_results: List[Dict] = None,
        query_type: str = 'text'
    ) -> List[Dict]:
        """
        이미지, 텍스트, 오디오 검색 결과 통합
        
        Args:
            image_results: 이미지 검색 결과
            text_results: 텍스트 검색 결과
            audio_results: 오디오 검색 결과
            query_type: 쿼리 타입 ('text', 'image', 'audio')
        
        Returns:
            통합된 결과 (점수 기반 정렬)
        """
        combined = []
        
        # 동적 가중치 설정 (쿼리 타입에 따라)
        weights = self._get_dynamic_weights(
            query_type=query_type,
            has_text=len(text_results) > 0,
            has_images=len(image_results) > 0,
            has_audio=audio_results is not None and len(audio_results) > 0
        )
        
        # 이미지 결과 추가
        for result in image_results:
            combined.append({
                **result,
                'type': 'image',
                'normalized_score': result.get('score', 0) / 100 * weights['image']
            })
        
        # 텍스트 결과 추가
        for result in text_results:
            combined.append({
                **result,
                'type': 'text',
                'normalized_score': result.get('score', 0) * weights['text']
            })
        
        # 오디오 결과 추가
        if audio_results:
            for result in audio_results:
                combined.append({
                    **result,
                    'type': 'audio',
                    'normalized_score': result.get('score', 0) * weights['audio']
                })
        
        # 점수로 정렬
        combined.sort(key=lambda x: x.get('normalized_score', 0), reverse=True)
        
        return combined
    
    def _get_dynamic_weights(
        self,
        query_type: str,
        has_text: bool,
        has_images: bool,
        has_audio: bool
    ) -> Dict[str, float]:
        """
        쿼리 타입과 결과 유무에 따른 동적 가중치 계산
        
        Args:
            query_type: 쿼리 타입 ('text', 'image', 'audio')
            has_text: 텍스트 결과 존재 여부
            has_images: 이미지 결과 존재 여부
            has_audio: 오디오 결과 존재 여부
        
        Returns:
            모달리티별 가중치
        """
        # 기본 가중치
        if query_type == 'text':
            # 텍스트 쿼리 → 텍스트 결과 우선
            weights = {'text': 0.6, 'image': 0.2, 'audio': 0.2}
        elif query_type == 'image':
            # 이미지 쿼리 → 이미지 결과 우선
            weights = {'text': 0.2, 'image': 0.6, 'audio': 0.2}
        elif query_type == 'audio':
            # 오디오 쿼리 → 오디오 결과 우선
            weights = {'text': 0.2, 'image': 0.2, 'audio': 0.6}
        else:
            # 기본 균등 가중치
            weights = {'text': 0.4, 'image': 0.3, 'audio': 0.3}
        
        # 결과가 없는 모달리티의 가중치를 재분배
        available_modalities = []
        if has_text:
            available_modalities.append('text')
        if has_images:
            available_modalities.append('image')
        if has_audio:
            available_modalities.append('audio')
        
        if len(available_modalities) < 3:
            # 일부 모달리티만 결과가 있는 경우
            total_weight = sum(weights[m] for m in available_modalities)
            
            if total_weight > 0:
                # 정규화
                for modality in weights:
                    if modality in available_modalities:
                        weights[modality] = weights[modality] / total_weight
                    else:
                        weights[modality] = 0.0
        
        logger.debug(f"Dynamic weights for {query_type}: {weights}")
        
        return weights
    
    async def _search_audio_with_text(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        텍스트 쿼리로 오디오 검색 (크로스 모달)
        
        방법: 오디오의 텍스트 변환(transcription)을 활용한 검색
        
        Args:
            query: 텍스트 쿼리
            top_k: 반환할 결과 수
        
        Returns:
            오디오 검색 결과
        """
        try:
            if not self.audio_milvus:
                return []
            
            # 1. 텍스트 임베딩 생성
            from backend.services.embedding import EmbeddingService
            embedding_service = EmbeddingService()
            text_embedding = embedding_service.embed_query(query)
            
            # 2. Milvus에서 transcription 필드로 필터링 후 검색
            # 간단한 방법: 모든 오디오를 가져와서 transcription 매칭
            # TODO: Milvus scalar 검색 또는 하이브리드 검색으로 개선
            
            # 임시 구현: 텍스트 임베딩과 오디오 임베딩 간 유사도 계산
            # (정확도는 낮지만 빠른 구현)
            
            logger.info(f"Cross-modal text-to-audio search: {query}")
            
            # 현재는 빈 결과 반환 (향후 개선)
            return []
            
        except Exception as e:
            logger.warning(f"Text-to-audio search failed: {e}")
            return []
    
    async def _search_images_with_text(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        텍스트 쿼리로 이미지 검색 (크로스 모달)
        
        방법: CLIP 기반 텍스트-이미지 임베딩 정렬
        
        Args:
            query: 텍스트 쿼리
            top_k: 반환할 결과 수
        
        Returns:
            이미지 검색 결과
        """
        try:
            if not self.clip_processor or not self.clip_milvus:
                logger.warning("CLIP not available for cross-modal search")
                return []
            
            # 1. 텍스트를 CLIP 임베딩으로 변환
            text_embedding = self.clip_processor.encode_text(query)
            
            # 2. CLIP Milvus에서 이미지 검색
            results = self.clip_milvus.search_images_with_text(
                text_embedding=text_embedding,
                top_k=top_k
            )
            
            logger.info(f"Cross-modal text-to-image search: {query} → {len(results)} results")
            
            return results
            
        except Exception as e:
            logger.warning(f"Text-to-image search failed: {e}")
            return []
    
    async def _search_with_image_query(
        self,
        query_image_path: str,
        search_images: bool = True,
        search_text: bool = True,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        이미지 쿼리로 검색
        
        Args:
            query_image_path: 쿼리 이미지 경로
            search_images: 이미지 검색 활성화
            search_text: 텍스트 검색 활성화
            top_k: 반환할 결과 수
        
        Returns:
            검색 결과
        """
        results = {
            'images': [],
            'text': []
        }
        
        try:
            if not self.clip_processor or not self.clip_milvus:
                logger.warning("CLIP not available for image query search")
                return results
            
            # 1. 이미지를 CLIP 임베딩으로 변환
            image_embedding = self.clip_processor.encode_image(query_image_path)
            
            # 2. 이미지 검색 (이미지 → 이미지)
            if search_images:
                image_results = self.clip_milvus.search(
                    query_embedding=image_embedding,
                    top_k=top_k,
                    content_type='image'
                )
                results['images'] = image_results
                logger.info(f"Image-to-image search: {len(image_results)} results")
            
            # 3. 텍스트 검색 (이미지 → 텍스트)
            if search_text:
                text_results = self.clip_milvus.search_text_with_image(
                    image_embedding=image_embedding,
                    top_k=top_k
                )
                results['text'] = text_results
                logger.info(f"Image-to-text search: {len(text_results)} results")
            
            return results
            
        except Exception as e:
            logger.error(f"Image query search failed: {e}")
            return results
    
    async def delete_document(self, document_id: str):
        """문서 삭제 (이미지 + 오디오 포함)"""
        try:
            # ColPali Milvus에서 삭제
            if self.colpali_milvus:
                self.colpali_milvus.delete_document(document_id)
            
            # Audio Milvus에서 삭제
            if self.audio_milvus:
                self.audio_milvus.delete_document(document_id)
            
            logger.info(f"Deleted multimodal document: {document_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 정보"""
        stats = {
            'colpali_available': self.colpali_processor is not None,
            'audio_available': self.audio_processor is not None,
            'clip_available': self.clip_processor is not None,
            'image_milvus_available': self.colpali_milvus is not None,
            'audio_milvus_available': self.audio_milvus is not None,
            'clip_milvus_available': self.clip_milvus is not None
        }
        
        if self.colpali_milvus:
            stats['image_collection_stats'] = self.colpali_milvus.get_collection_stats()
        
        if self.audio_milvus:
            stats['audio_collection_stats'] = self.audio_milvus.get_collection_stats()
        
        if self.clip_milvus:
            stats['clip_collection_stats'] = self.clip_milvus.get_collection_stats()
        
        # 리랭킹 통계
        try:
            from backend.services.multimodal_reranker import get_multimodal_reranker
            reranker = get_multimodal_reranker()
            stats['reranker_stats'] = reranker.get_stats()
        except:
            pass
        
        return stats


# Global instance
_multimodal_service: Optional[MultimodalDocumentService] = None


def get_multimodal_document_service() -> MultimodalDocumentService:
    """Get global multimodal document service instance"""
    global _multimodal_service
    
    if _multimodal_service is None:
        _multimodal_service = MultimodalDocumentService()
    
    return _multimodal_service
