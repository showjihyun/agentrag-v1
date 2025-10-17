# Korean Text Processor
"""
한글 텍스트 특화 처리

Features:
- 형태소 분석 (KoNLPy)
- 한자 → 한글 변환
- 특수 문자 정규화
- 띄어쓰기 교정
- 키워드 추출
"""

import logging
import re
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)


class KoreanTextProcessor:
    """
    한글 텍스트 특화 처리기
    
    KoNLPy가 설치되어 있으면 형태소 분석을 수행하고,
    없으면 기본 처리만 수행합니다.
    """
    
    def __init__(self, use_morpheme_analysis: bool = True):
        self.use_morpheme_analysis = use_morpheme_analysis
        self.morpheme_analyzer = None
        
        # KoNLPy 확인
        if use_morpheme_analysis:
            try:
                from konlpy.tag import Okt
                self.morpheme_analyzer = Okt()
                logger.info("KoNLPy available - using morpheme analysis")
            except ImportError:
                logger.warning(
                    "KoNLPy not available - skipping morpheme analysis. "
                    "Install with: pip install konlpy"
                )
        
        # 한자-한글 매핑 (자주 사용되는 한자)
        self.hanja_to_hangul = self._load_hanja_mapping()
    
    def process_korean_text(self, text: str) -> Dict:
        """
        한글 텍스트 종합 처리
        
        Args:
            text: 원본 텍스트
        
        Returns:
            {
                'original': str,           # 원본
                'normalized': str,         # 정규화된 텍스트
                'morphemes': List[Tuple],  # (형태소, 품사)
                'keywords': List[str],     # 키워드
                'nouns': List[str],        # 명사
                'has_hanja': bool          # 한자 포함 여부
            }
        """
        result = {
            'original': text,
            'normalized': text,
            'morphemes': [],
            'keywords': [],
            'nouns': [],
            'has_hanja': False
        }
        
        # 1. 한자 변환
        if self._contains_hanja(text):
            result['has_hanja'] = True
            text = self._convert_hanja_to_hangul(text)
        
        # 2. 특수 문자 정규화
        text = self._normalize_special_chars(text)
        
        # 3. 띄어쓰기 정규화
        text = self._normalize_spacing(text)
        
        result['normalized'] = text
        
        # 4. 형태소 분석 (KoNLPy 사용 가능 시)
        if self.morpheme_analyzer:
            try:
                # 형태소 분석
                result['morphemes'] = self.morpheme_analyzer.pos(text)
                
                # 명사 추출
                result['nouns'] = self.morpheme_analyzer.nouns(text)
                
                # 키워드 추출 (명사 + 동사 + 형용사)
                result['keywords'] = self._extract_keywords(result['morphemes'])
                
            except Exception as e:
                logger.warning(f"Morpheme analysis failed: {e}")
        
        return result
    
    def _contains_hanja(self, text: str) -> bool:
        """한자 포함 여부 확인"""
        # 한자 유니코드 범위: U+4E00 ~ U+9FFF
        hanja_pattern = re.compile(r'[\u4E00-\u9FFF]')
        return bool(hanja_pattern.search(text))
    
    def _convert_hanja_to_hangul(self, text: str) -> str:
        """한자를 한글로 변환"""
        # 자주 사용되는 한자만 변환
        for hanja, hangul in self.hanja_to_hangul.items():
            text = text.replace(hanja, hangul)
        
        # 남은 한자는 괄호로 표시
        hanja_pattern = re.compile(r'[\u4E00-\u9FFF]+')
        text = hanja_pattern.sub(lambda m: f"({m.group()})", text)
        
        return text
    
    def _normalize_special_chars(self, text: str) -> str:
        """특수 문자 정규화"""
        # 전각 문자 → 반각 문자
        text = text.replace('　', ' ')  # 전각 공백
        text = text.replace('（', '(')
        text = text.replace('）', ')')
        text = text.replace('［', '[')
        text = text.replace('］', ']')
        text = text.replace('｛', '{')
        text = text.replace('｝', '}')
        
        # 특수 따옴표 정규화
        text = text.replace('"', '"')
        text = text.replace('"', '"')
        text = text.replace(''', "'")
        text = text.replace(''', "'")
        
        # 특수 대시 정규화
        text = text.replace('—', '-')
        text = text.replace('–', '-')
        text = text.replace('―', '-')
        
        # 연속된 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _normalize_spacing(self, text: str) -> str:
        """띄어쓰기 정규화"""
        # 1. 단어 중간의 불필요한 공백 제거
        # 예: "대구광역시  북구" → "대구광역시 북구"
        # 예: "최지현" → "최지현" (이미 정상)
        # 예: "메이커스페이스동 )" → "메이커스페이스동)"
        # 예: "cs @bigvalue. co. kr" → "cs@bigvalue.co.kr"
        text = self._remove_intra_word_spaces(text)
        
        # 2. 문장 부호 앞뒤 공백 정리 (단, 이메일/URL 제외)
        # 쉼표, 느낌표, 물음표, 세미콜론만 처리 (점과 콜론은 이메일/URL에서 사용)
        text = re.sub(r'\s*([,!?;])\s*', r'\1 ', text)
        
        # 3. 괄호 앞뒤 공백 정리
        text = re.sub(r'\s*\(\s*', ' (', text)
        text = re.sub(r'\s*\)\s*', ') ', text)
        
        # 4. 연속된 공백 제거 (단, 이메일/URL 내부는 이미 처리됨)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _remove_intra_word_spaces(self, text: str) -> str:
        """
        단어 중간의 불필요한 공백 제거
        
        규칙:
        - 한글/영문/숫자 사이의 과도한 공백(2개 이상)을 1개로 축소
        - 이메일, URL, 전화번호 등 특수 패턴은 보호
        - 하이픈 앞뒤 공백 제거
        
        예시:
        - "대구광역시  북구" → "대구광역시 북구"
        - "최  지  현" → "최 지 현"
        - "070-7762-9364" → "070-7762-9364" (변경 없음)
        - "110111 -5729186" → "110111-5729186" (하이픈 앞 공백 제거)
        - "cs@bigvalue.co.kr" → "cs@bigvalue.co.kr" (변경 없음)
        """
        # 패턴 1: 하이픈(-) 앞뒤의 공백 제거
        # 예: "110111 -5729186" → "110111-5729186"
        # 예: "207호- 210호" → "207호-210호"
        text = re.sub(r'\s*-\s*', '-', text)
        
        # 패턴 2: @ 앞뒤의 공백 제거 (이메일)
        # 예: "cs @bigvalue.co.kr" → "cs@bigvalue.co.kr"
        text = re.sub(r'\s*@\s*', '@', text)
        
        # 패턴 3: 점(.) 앞뒤의 공백 제거 (이메일, URL, 도메인)
        # 예: "bigvalue. co. kr" → "bigvalue.co.kr"
        # 단, 문장 끝 점은 제외 (뒤에 공백 + 대문자가 오는 경우)
        text = re.sub(r'\.\s+(?=[a-z0-9])', '.', text)
        text = re.sub(r'(?<=[a-z0-9])\s+\.', '.', text)
        
        # 패턴 4: 한글/영문/숫자 사이의 2개 이상 공백을 1개로
        # [\uAC00-\uD7A3]: 한글
        # [a-zA-Z]: 영문
        # [0-9]: 숫자
        text = re.sub(
            r'([\uAC00-\uD7A3a-zA-Z0-9])\s{2,}([\uAC00-\uD7A3a-zA-Z0-9])',
            r'\1 \2',
            text
        )
        
        # 패턴 5: 괄호/문장부호 바로 앞의 공백 제거
        # 예: "동 )" → "동)"
        text = re.sub(r'\s+([)\]},.!?;:])', r'\1', text)
        
        # 패턴 6: 괄호 바로 뒤의 공백 제거
        # 예: "(  침산동" → "(침산동"
        text = re.sub(r'([(\[{])\s+', r'\1', text)
        
        return text
    
    def _extract_keywords(self, morphemes: List[Tuple[str, str]]) -> List[str]:
        """키워드 추출 (명사, 동사, 형용사)"""
        keywords = []
        
        # 키워드로 사용할 품사
        keyword_pos = ['Noun', 'Verb', 'Adjective']
        
        for word, pos in morphemes:
            # 품사 확인
            if any(kp in pos for kp in keyword_pos):
                # 길이 필터 (1글자 제외)
                if len(word) > 1:
                    keywords.append(word)
        
        # 중복 제거 및 빈도순 정렬
        from collections import Counter
        keyword_counts = Counter(keywords)
        sorted_keywords = [word for word, count in keyword_counts.most_common()]
        
        return sorted_keywords
    
    def _load_hanja_mapping(self) -> Dict[str, str]:
        """자주 사용되는 한자-한글 매핑"""
        return {
            # 숫자
            '一': '일', '二': '이', '三': '삼', '四': '사', '五': '오',
            '六': '육', '七': '칠', '八': '팔', '九': '구', '十': '십',
            '百': '백', '千': '천', '萬': '만', '億': '억',
            
            # 자주 사용되는 한자
            '大': '대', '小': '소', '中': '중', '高': '고', '低': '저',
            '新': '신', '舊': '구', '前': '전', '後': '후', '上': '상',
            '下': '하', '內': '내', '外': '외', '東': '동', '西': '서',
            '南': '남', '北': '북', '左': '좌', '右': '우', '正': '정',
            '副': '부', '主': '주', '次': '차', '第': '제', '各': '각',
            '全': '전', '半': '반', '多': '다', '少': '소', '長': '장',
            '短': '단', '廣': '광', '狹': '협', '深': '심', '淺': '천',
            '强': '강', '弱': '약', '輕': '경', '重': '중', '明': '명',
            '暗': '암', '淸': '청', '濁': '탁', '冷': '냉', '溫': '온',
            '乾': '건', '濕': '습', '軟': '연', '硬': '경', '粗': '조',
            '細': '세', '厚': '후', '薄': '박', '遠': '원', '近': '근',
            '早': '조', '晩': '만', '速': '속', '遲': '지', '急': '급',
            '緩': '완', '直': '직', '曲': '곡', '平': '평', '險': '험',
            
            # 단위
            '年': '년', '月': '월', '日': '일', '時': '시', '分': '분',
            '秒': '초', '個': '개', '名': '명', '人': '인', '件': '건',
            '回': '회', '次': '차', '番': '번', '號': '호', '級': '급',
            '等': '등', '類': '류', '種': '종', '式': '식', '型': '형',
            
            # 기타 자주 사용
            '國': '국', '民': '민', '政': '정', '府': '부', '會': '회',
            '社': '사', '團': '단', '體': '체', '部': '부', '課': '과',
            '係': '계', '員': '원', '長': '장', '理': '리', '事': '사',
            '業': '업', '務': '무', '所': '소', '室': '실', '館': '관',
            '院': '원', '校': '교', '科': '과', '學': '학', '敎': '교',
            '授': '수', '生': '생', '徒': '도', '師': '사', '門': '문',
            '家': '가', '店': '점', '場': '장', '市': '시', '道': '도',
            '區': '구', '洞': '동', '里': '리', '街': '가', '路': '로',
        }
    
    def extract_noun_phrases(self, text: str) -> List[str]:
        """명사구 추출"""
        if not self.morpheme_analyzer:
            return []
        
        try:
            # 형태소 분석
            morphemes = self.morpheme_analyzer.pos(text)
            
            # 명사구 패턴: 명사 + 명사, 관형사 + 명사
            noun_phrases = []
            current_phrase = []
            
            for word, pos in morphemes:
                if 'Noun' in pos or 'Determiner' in pos:
                    current_phrase.append(word)
                else:
                    if len(current_phrase) >= 2:
                        noun_phrases.append(''.join(current_phrase))
                    current_phrase = []
            
            # 마지막 구
            if len(current_phrase) >= 2:
                noun_phrases.append(''.join(current_phrase))
            
            return noun_phrases
            
        except Exception as e:
            logger.warning(f"Noun phrase extraction failed: {e}")
            return []
    
    def is_korean_text(self, text: str) -> bool:
        """한글 텍스트 여부 확인"""
        # 한글 유니코드 범위: U+AC00 ~ U+D7A3
        korean_pattern = re.compile(r'[\uAC00-\uD7A3]')
        korean_chars = len(korean_pattern.findall(text))
        total_chars = len(re.findall(r'\w', text))
        
        # 한글이 50% 이상이면 한글 텍스트로 판단
        return total_chars > 0 and (korean_chars / total_chars) >= 0.5


# Global instance
_korean_text_processor: Optional[KoreanTextProcessor] = None


def get_korean_text_processor(
    use_morpheme_analysis: bool = True
) -> KoreanTextProcessor:
    """Get global Korean text processor instance"""
    global _korean_text_processor
    if _korean_text_processor is None:
        _korean_text_processor = KoreanTextProcessor(
            use_morpheme_analysis=use_morpheme_analysis
        )
    return _korean_text_processor
