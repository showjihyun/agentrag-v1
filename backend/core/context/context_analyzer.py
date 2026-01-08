"""Context analyzer for understanding message references and intent."""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

class MessageIntent(Enum):
    """Types of message intents."""
    NEW_QUESTION = "new_question"
    FOLLOW_UP = "follow_up"
    CLARIFICATION = "clarification"
    REFERENCE = "reference"
    ELABORATION = "elaboration"
    CORRECTION = "correction"
    CONFIRMATION = "confirmation"

@dataclass
class ContextReference:
    """Represents a reference to previous context."""
    reference_type: str  # 'number', 'pronoun', 'temporal', 'topic'
    reference_text: str  # Original reference text
    target_index: Optional[int] = None  # Index of referenced message
    confidence: float = 0.0  # Confidence score
    context: str = ""  # Additional context

@dataclass
class MessageAnalysis:
    """Analysis result for a message."""
    intent: MessageIntent
    references: List[ContextReference]
    is_followup: bool
    requires_context: bool
    confidence: float
    keywords: List[str]
    sentiment: str = "neutral"

class ContextAnalyzer:
    """Analyzes messages to understand context references and intent."""
    
    def __init__(self):
        # Korean reference patterns
        self.korean_patterns = {
            'numbers': [
                r'(\d+)번(?:째)?(?:\s*(?:으로|로|에서|에|을|를|의|에서|에게|한테))?',
                r'첫\s*번째', r'두\s*번째', r'세\s*번째', r'네\s*번째', r'다섯\s*번째',
                r'마지막', r'처음', r'끝'
            ],
            'pronouns': [
                r'그것(?:을|를|이|가|에|의)?', r'그거(?:을|를|이|가|에|의)?',
                r'이것(?:을|를|이|가|에|의)?', r'이거(?:을|를|이|가|에|의)?',
                r'저것(?:을|를|이|가|에|의)?', r'저거(?:을|를|이|가|에|의)?',
                r'그(?:분|사람|내용|방법|것)?', r'위(?:의|에서)?(?:\s*(?:것|내용|방법))?'
            ],
            'temporal': [
                r'방금(?:\s*(?:전|말한|한))?', r'아까(?:\s*(?:말한|한))?',
                r'전에(?:\s*(?:말한|한))?', r'앞서(?:\s*(?:말한|한))?',
                r'이전(?:에)?(?:\s*(?:말한|한))?', r'먼저(?:\s*(?:말한|한))?'
            ],
            'elaboration': [
                r'더\s*자세(?:히|하게)', r'더\s*설명', r'더\s*알려',
                r'구체적(?:으로)?', r'세부(?:적으로)?', r'상세(?:히|하게)',
                r'예시(?:를)?', r'예제(?:를)?', r'사례(?:를)?'
            ],
            'clarification': [
                r'무슨\s*(?:말|뜻|의미)', r'어떤\s*(?:말|뜻|의미)',
                r'이해(?:가)?\s*(?:안|못)', r'모르겠', r'헷갈',
                r'다시\s*(?:말해|설명)', r'쉽게\s*(?:말해|설명)'
            ]
        }
        
        # English reference patterns
        self.english_patterns = {
            'numbers': [
                r'(?:number\s*)?(\d+)(?:st|nd|rd|th)?',
                r'first', r'second', r'third', r'fourth', r'fifth',
                r'last', r'previous', r'above'
            ],
            'pronouns': [
                r'that(?:\s+one)?', r'this(?:\s+one)?', r'it',
                r'the\s+(?:above|previous|last|first)'
            ],
            'temporal': [
                r'just\s+(?:now|mentioned)', r'earlier', r'before',
                r'previously', r'above', r'prior'
            ],
            'elaboration': [
                r'more\s+detail(?:s)?', r'explain\s+more', r'elaborate',
                r'specifically', r'in\s+detail', r'examples?',
                r'tell\s+me\s+more'
            ],
            'clarification': [
                r'what\s+do\s+you\s+mean', r'i\s+don\'t\s+understand',
                r'clarify', r'explain\s+again', r'rephrase'
            ]
        }
    
    def analyze_message(
        self, 
        message: str, 
        conversation_history: List[Dict[str, Any]] = None
    ) -> MessageAnalysis:
        """Analyze a message to understand its context and intent."""
        message_lower = message.lower().strip()
        
        # Find references
        references = self._find_references(message, conversation_history or [])
        
        # Determine intent
        intent = self._determine_intent(message_lower, references)
        
        # Check if it's a follow-up
        is_followup = len(references) > 0 or self._is_followup_question(message_lower)
        
        # Check if context is required
        requires_context = is_followup or intent in [
            MessageIntent.FOLLOW_UP, 
            MessageIntent.REFERENCE, 
            MessageIntent.ELABORATION,
            MessageIntent.CLARIFICATION
        ]
        
        # Extract keywords
        keywords = self._extract_keywords(message)
        
        # Calculate confidence
        confidence = self._calculate_confidence(intent, references, message)
        
        return MessageAnalysis(
            intent=intent,
            references=references,
            is_followup=is_followup,
            requires_context=requires_context,
            confidence=confidence,
            keywords=keywords
        )
    
    def _find_references(
        self, 
        message: str, 
        conversation_history: List[Dict[str, Any]]
    ) -> List[ContextReference]:
        """Find references to previous context in the message."""
        references = []
        message_lower = message.lower()
        
        # Find number references (1번, 2번, etc.)
        number_refs = self._find_number_references(message, conversation_history)
        references.extend(number_refs)
        
        # Find pronoun references (그것, 이것, etc.)
        pronoun_refs = self._find_pronoun_references(message_lower)
        references.extend(pronoun_refs)
        
        # Find temporal references (방금, 아까, etc.)
        temporal_refs = self._find_temporal_references(message_lower)
        references.extend(temporal_refs)
        
        return references
    
    def _find_number_references(
        self, 
        message: str, 
        conversation_history: List[Dict[str, Any]]
    ) -> List[ContextReference]:
        """Find numbered references like '1번', '첫번째', etc."""
        references = []
        
        # Korean number patterns
        for pattern in self.korean_patterns['numbers']:
            matches = re.finditer(pattern, message, re.IGNORECASE)
            for match in matches:
                ref_text = match.group(0)
                
                # Extract number
                number_match = re.search(r'(\d+)', ref_text)
                if number_match:
                    number = int(number_match.group(1))
                    target_index = self._find_message_by_number(number, conversation_history)
                    
                    references.append(ContextReference(
                        reference_type='number',
                        reference_text=ref_text,
                        target_index=target_index,
                        confidence=0.9 if target_index is not None else 0.3,
                        context=f"Reference to item #{number}"
                    ))
                
                # Handle ordinal words
                elif any(word in ref_text for word in ['첫', '두', '세', '네', '다섯']):
                    ordinal_map = {'첫': 1, '두': 2, '세': 3, '네': 4, '다섯': 5}
                    for word, num in ordinal_map.items():
                        if word in ref_text:
                            target_index = self._find_message_by_number(num, conversation_history)
                            references.append(ContextReference(
                                reference_type='number',
                                reference_text=ref_text,
                                target_index=target_index,
                                confidence=0.8 if target_index is not None else 0.3,
                                context=f"Reference to {word}번째 item"
                            ))
                            break
        
        return references
    
    def _find_pronoun_references(self, message: str) -> List[ContextReference]:
        """Find pronoun references like '그것', '이것', etc."""
        references = []
        
        for pattern in self.korean_patterns['pronouns']:
            matches = re.finditer(pattern, message, re.IGNORECASE)
            for match in matches:
                references.append(ContextReference(
                    reference_type='pronoun',
                    reference_text=match.group(0),
                    confidence=0.7,
                    context="Pronoun reference to previous context"
                ))
        
        return references
    
    def _find_temporal_references(self, message: str) -> List[ContextReference]:
        """Find temporal references like '방금', '아까', etc."""
        references = []
        
        for pattern in self.korean_patterns['temporal']:
            matches = re.finditer(pattern, message, re.IGNORECASE)
            for match in matches:
                references.append(ContextReference(
                    reference_type='temporal',
                    reference_text=match.group(0),
                    confidence=0.8,
                    context="Temporal reference to recent context"
                ))
        
        return references
    
    def _find_message_by_number(
        self, 
        number: int, 
        conversation_history: List[Dict[str, Any]]
    ) -> Optional[int]:
        """Find message index by number reference."""
        # Filter assistant messages (numbered responses)
        assistant_messages = [
            (i, msg) for i, msg in enumerate(conversation_history)
            if msg.get('role') == 'assistant'
        ]
        
        if 1 <= number <= len(assistant_messages):
            return assistant_messages[number - 1][0]
        
        return None
    
    def _determine_intent(
        self, 
        message: str, 
        references: List[ContextReference]
    ) -> MessageIntent:
        """Determine the intent of the message."""
        
        # Check for elaboration requests
        if any(re.search(pattern, message, re.IGNORECASE) 
               for pattern in self.korean_patterns['elaboration']):
            return MessageIntent.ELABORATION
        
        # Check for clarification requests
        if any(re.search(pattern, message, re.IGNORECASE) 
               for pattern in self.korean_patterns['clarification']):
            return MessageIntent.CLARIFICATION
        
        # Check for references
        if references:
            return MessageIntent.REFERENCE
        
        # Check for follow-up indicators
        if self._is_followup_question(message):
            return MessageIntent.FOLLOW_UP
        
        # Default to new question
        return MessageIntent.NEW_QUESTION
    
    def _is_followup_question(self, message: str) -> bool:
        """Check if message is a follow-up question."""
        followup_indicators = [
            r'그(?:런데|러면|리고)', r'그래서', r'그럼', r'그러니까',
            r'또한', r'그리고', r'추가(?:로)?', r'더불어',
            r'그\s*외에', r'다른', r'또\s*다른'
        ]
        
        return any(re.search(pattern, message, re.IGNORECASE) 
                  for pattern in followup_indicators)
    
    def _extract_keywords(self, message: str) -> List[str]:
        """Extract important keywords from the message."""
        # Simple keyword extraction (can be enhanced with NLP)
        words = re.findall(r'\b\w+\b', message.lower())
        
        # Filter out common stop words
        stop_words = {
            '그', '이', '저', '것', '를', '을', '가', '이', '은', '는',
            '에', '에서', '로', '으로', '의', '와', '과', '하고',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to'
        }
        
        keywords = [word for word in words if word not in stop_words and len(word) > 1]
        return keywords[:10]  # Return top 10 keywords
    
    def _calculate_confidence(
        self, 
        intent: MessageIntent, 
        references: List[ContextReference], 
        message: str
    ) -> float:
        """Calculate confidence score for the analysis."""
        base_confidence = 0.5
        
        # Boost confidence based on clear references
        if references:
            ref_confidence = sum(ref.confidence for ref in references) / len(references)
            base_confidence += ref_confidence * 0.3
        
        # Boost confidence for clear intent indicators
        if intent in [MessageIntent.ELABORATION, MessageIntent.CLARIFICATION]:
            base_confidence += 0.2
        
        # Boost confidence for explicit patterns
        if any(pattern in message.lower() for pattern in ['번', '자세히', '설명', '더']):
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)