"""
Translation Services for PP-DocTranslation

Supports multiple translation providers:
- Google Translate (free)
- DeepL (high quality, requires API key)
- Papago (Korean-optimized, requires API key)
- Simple (fallback, no actual translation)
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class BaseTranslator(ABC):
    """Base translator interface"""
    
    @abstractmethod
    def translate(self, text: str, target_lang: str, source_lang: str = 'auto') -> str:
        """
        Translate text from source language to target language.
        
        Args:
            text: Text to translate
            target_lang: Target language code
            source_lang: Source language code ('auto' for auto-detection)
            
        Returns:
            Translated text
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if translator is available"""
        pass


class GoogleTranslator(BaseTranslator):
    """Google Translate (free, no API key required)"""
    
    def __init__(self):
        self.translator = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Google Translator"""
        try:
            from googletrans import Translator
            self.translator = Translator()
            logger.info("Google Translator initialized successfully")
        except ImportError:
            logger.warning("googletrans not installed. Install with: pip install googletrans==4.0.0-rc1")
            self.translator = None
        except Exception as e:
            logger.warning(f"Google Translator initialization failed: {e}")
            self.translator = None
    
    def is_available(self) -> bool:
        """Check if Google Translator is available"""
        return self.translator is not None
    
    def translate(self, text: str, target_lang: str, source_lang: str = 'auto') -> str:
        """Translate text using Google Translate"""
        if not self.is_available():
            raise RuntimeError("Google Translator not available")
        
        try:
            result = self.translator.translate(text, dest=target_lang, src=source_lang)
            return result.text
        except Exception as e:
            logger.error(f"Google translation failed: {e}")
            raise


class DeepLTranslator(BaseTranslator):
    """DeepL Translator (high quality, requires API key)"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.translator = None
        self._initialize()
    
    def _initialize(self):
        """Initialize DeepL Translator"""
        try:
            import deepl
            from backend.config import settings
            
            # Get API key from settings if not provided
            if not self.api_key:
                self.api_key = getattr(settings, 'DEEPL_API_KEY', None)
            
            if not self.api_key:
                logger.warning("DeepL API key not found")
                return
            
            self.translator = deepl.Translator(self.api_key)
            logger.info("DeepL Translator initialized successfully")
        except ImportError:
            logger.warning("deepl not installed. Install with: pip install deepl")
            self.translator = None
        except Exception as e:
            logger.warning(f"DeepL Translator initialization failed: {e}")
            self.translator = None
    
    def is_available(self) -> bool:
        """Check if DeepL Translator is available"""
        return self.translator is not None
    
    def translate(self, text: str, target_lang: str, source_lang: str = 'auto') -> str:
        """Translate text using DeepL"""
        if not self.is_available():
            raise RuntimeError("DeepL Translator not available")
        
        try:
            # Convert to DeepL language codes
            target_lang_code = self._convert_lang_code(target_lang)
            
            result = self.translator.translate_text(
                text,
                target_lang=target_lang_code
            )
            return result.text
        except Exception as e:
            logger.error(f"DeepL translation failed: {e}")
            raise
    
    def _convert_lang_code(self, lang: str) -> str:
        """Convert to DeepL language codes"""
        mapping = {
            'en': 'EN-US',
            'ko': 'KO',
            'ja': 'JA',
            'zh': 'ZH',
            'de': 'DE',
            'fr': 'FR',
            'es': 'ES',
            'it': 'IT',
            'pt': 'PT-BR',
            'ru': 'RU',
            'nl': 'NL',
            'pl': 'PL'
        }
        return mapping.get(lang.lower(), 'EN-US')


class PapagoTranslator(BaseTranslator):
    """Naver Papago Translator (Korean-optimized, requires API key)"""
    
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self._initialize()
    
    def _initialize(self):
        """Initialize Papago Translator"""
        try:
            from backend.config import settings
            
            # Get credentials from settings if not provided
            if not self.client_id:
                self.client_id = getattr(settings, 'PAPAGO_CLIENT_ID', None)
            if not self.client_secret:
                self.client_secret = getattr(settings, 'PAPAGO_CLIENT_SECRET', None)
            
            if not self.client_id or not self.client_secret:
                logger.warning("Papago API credentials not found")
                return
            
            logger.info("Papago Translator initialized successfully")
        except Exception as e:
            logger.warning(f"Papago Translator initialization failed: {e}")
    
    def is_available(self) -> bool:
        """Check if Papago Translator is available"""
        return bool(self.client_id and self.client_secret)
    
    def translate(self, text: str, target_lang: str, source_lang: str = 'auto') -> str:
        """Translate text using Papago"""
        if not self.is_available():
            raise RuntimeError("Papago Translator not available")
        
        try:
            import requests
            
            url = "https://openapi.naver.com/v1/papago/n2mt"
            
            # Convert language codes
            source_code = 'ko' if source_lang == 'auto' else source_lang
            target_code = self._convert_lang_code(target_lang)
            
            headers = {
                "X-Naver-Client-Id": self.client_id,
                "X-Naver-Client-Secret": self.client_secret
            }
            
            data = {
                "source": source_code,
                "target": target_code,
                "text": text
            }
            
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            
            result = response.json()
            return result['message']['result']['translatedText']
            
        except Exception as e:
            logger.error(f"Papago translation failed: {e}")
            raise
    
    def _convert_lang_code(self, lang: str) -> str:
        """Convert to Papago language codes"""
        mapping = {
            'en': 'en',
            'ko': 'ko',
            'ja': 'ja',
            'zh': 'zh-CN',
            'zh-tw': 'zh-TW',
            'es': 'es',
            'fr': 'fr',
            'de': 'de',
            'ru': 'ru',
            'pt': 'pt',
            'it': 'it',
            'vi': 'vi',
            'th': 'th',
            'id': 'id'
        }
        return mapping.get(lang.lower(), 'en')


class SimpleTranslator(BaseTranslator):
    """Simple fallback translator (no actual translation)"""
    
    def __init__(self):
        logger.info("Simple Translator initialized (fallback mode)")
    
    def is_available(self) -> bool:
        """Simple translator is always available"""
        return True
    
    def translate(self, text: str, target_lang: str, source_lang: str = 'auto') -> str:
        """Returns original text with language tag"""
        return f"[{target_lang}] {text}"


def get_translator(service: str = 'auto') -> BaseTranslator:
    """
    Get translator instance based on service name.
    
    Args:
        service: Translation service name
            - 'auto': Best available (DeepL > Papago > Google > Simple)
            - 'google': Google Translate (free)
            - 'deepl': DeepL (requires API key)
            - 'papago': Papago (requires API key)
            - 'simple': Simple fallback
            
    Returns:
        Translator instance
    """
    if service == 'auto':
        return get_best_available_translator()
    elif service == 'google':
        translator = GoogleTranslator()
        if translator.is_available():
            return translator
        raise RuntimeError("Google Translator not available")
    elif service == 'deepl':
        translator = DeepLTranslator()
        if translator.is_available():
            return translator
        raise RuntimeError("DeepL Translator not available (API key required)")
    elif service == 'papago':
        translator = PapagoTranslator()
        if translator.is_available():
            return translator
        raise RuntimeError("Papago Translator not available (API credentials required)")
    elif service == 'simple':
        return SimpleTranslator()
    else:
        raise ValueError(f"Unknown translation service: {service}")


def get_best_available_translator() -> BaseTranslator:
    """
    Get the best available translator.
    
    Priority: DeepL > Papago > Google > Simple
    
    Returns:
        Best available translator instance
    """
    # Try DeepL (highest quality)
    try:
        translator = DeepLTranslator()
        if translator.is_available():
            logger.info("Using DeepL Translator (best quality)")
            return translator
    except Exception as e:
        logger.debug(f"DeepL not available: {e}")
    
    # Try Papago (Korean-optimized)
    try:
        translator = PapagoTranslator()
        if translator.is_available():
            logger.info("Using Papago Translator (Korean-optimized)")
            return translator
    except Exception as e:
        logger.debug(f"Papago not available: {e}")
    
    # Try Google (free)
    try:
        translator = GoogleTranslator()
        if translator.is_available():
            logger.info("Using Google Translator (free)")
            return translator
    except Exception as e:
        logger.debug(f"Google not available: {e}")
    
    # Fallback to Simple
    logger.warning("No translation service available, using Simple fallback")
    return SimpleTranslator()
