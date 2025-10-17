"""
HWP to PDF Converter Service

Converts HWP/HWPX files to PDF for better table and chart extraction.
Uses hwp5 library or external conversion tools.
"""

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple
import os

logger = logging.getLogger(__name__)


class HWPConverter:
    """
    Service for converting HWP/HWPX files to PDF.
    
    Supports multiple conversion methods:
    1. hwp5 library (Python-based, best for Linux)
    2. LibreOffice (cross-platform, requires installation)
    3. unoconv (alternative to LibreOffice)
    """

    def __init__(self):
        """Initialize HWP converter with available tools."""
        self.hwp5_available = self._check_hwp5()
        self.libreoffice_available = self._check_libreoffice()
        self.unoconv_available = self._check_unoconv()
        
        logger.info(
            f"HWP Converter initialized - "
            f"hwp5: {self.hwp5_available}, "
            f"LibreOffice: {self.libreoffice_available}, "
            f"unoconv: {self.unoconv_available}"
        )

    def _check_hwp5(self) -> bool:
        """Check if hwp5 library is available."""
        try:
            import hwp5
            return True
        except ImportError:
            return False

    def _check_libreoffice(self) -> bool:
        """Check if LibreOffice is available."""
        try:
            result = subprocess.run(
                ["soffice", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _check_unoconv(self) -> bool:
        """Check if unoconv is available."""
        try:
            result = subprocess.run(
                ["unoconv", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def convert_to_pdf(
        self,
        hwp_content: bytes,
        filename: str
    ) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Convert HWP/HWPX file to PDF.
        
        Args:
            hwp_content: HWP file content as bytes
            filename: Original filename
            
        Returns:
            Tuple of (PDF content as bytes, error message if failed)
        """
        # Try conversion methods in order of preference
        methods = []
        
        if self.libreoffice_available:
            methods.append(("LibreOffice", self._convert_with_libreoffice))
        
        if self.unoconv_available:
            methods.append(("unoconv", self._convert_with_unoconv))
            
        if self.hwp5_available:
            methods.append(("hwp5", self._convert_with_hwp5))
        
        if not methods:
            error_msg = (
                "No HWP conversion tools available. Please install one of: "
                "LibreOffice, unoconv, or hwp5 (pip install hwp5)"
            )
            logger.warning(error_msg)
            return None, error_msg
        
        # Try each method
        for method_name, method_func in methods:
            try:
                logger.info(f"Attempting HWP→PDF conversion with {method_name}")
                pdf_content = method_func(hwp_content, filename)
                
                if pdf_content:
                    logger.info(
                        f"✅ Successfully converted {filename} to PDF using {method_name} "
                        f"({len(pdf_content)} bytes)"
                    )
                    return pdf_content, None
                    
            except Exception as e:
                logger.warning(f"{method_name} conversion failed: {e}")
                continue
        
        error_msg = f"All conversion methods failed for {filename}"
        logger.error(error_msg)
        return None, error_msg

    def _convert_with_libreoffice(
        self,
        hwp_content: bytes,
        filename: str
    ) -> Optional[bytes]:
        """Convert HWP to PDF using LibreOffice."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Write HWP file
            hwp_file = temp_path / filename
            hwp_file.write_bytes(hwp_content)
            
            # Convert to PDF
            result = subprocess.run(
                [
                    "soffice",
                    "--headless",
                    "--convert-to", "pdf",
                    "--outdir", str(temp_path),
                    str(hwp_file)
                ],
                capture_output=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"LibreOffice error: {result.stderr.decode()}")
                return None
            
            # Read PDF
            pdf_file = temp_path / f"{hwp_file.stem}.pdf"
            if pdf_file.exists():
                return pdf_file.read_bytes()
            
            return None

    def _convert_with_unoconv(
        self,
        hwp_content: bytes,
        filename: str
    ) -> Optional[bytes]:
        """Convert HWP to PDF using unoconv."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Write HWP file
            hwp_file = temp_path / filename
            hwp_file.write_bytes(hwp_content)
            
            # Convert to PDF
            result = subprocess.run(
                [
                    "unoconv",
                    "-f", "pdf",
                    "-o", str(temp_path),
                    str(hwp_file)
                ],
                capture_output=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"unoconv error: {result.stderr.decode()}")
                return None
            
            # Read PDF
            pdf_file = temp_path / f"{hwp_file.stem}.pdf"
            if pdf_file.exists():
                return pdf_file.read_bytes()
            
            return None

    def _convert_with_hwp5(
        self,
        hwp_content: bytes,
        filename: str
    ) -> Optional[bytes]:
        """Convert HWP to PDF using hwp5 library."""
        try:
            import hwp5
            from hwp5.hwp5html import main as hwp5html_main
            
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Write HWP file
                hwp_file = temp_path / filename
                hwp_file.write_bytes(hwp_content)
                
                # hwp5 doesn't directly convert to PDF, but to HTML
                # This is a fallback method - not as good as LibreOffice
                logger.warning(
                    "hwp5 library doesn't support direct PDF conversion. "
                    "Consider installing LibreOffice for better results."
                )
                return None
                
        except Exception as e:
            logger.error(f"hwp5 conversion error: {e}")
            return None


# Singleton instance
_hwp_converter: Optional[HWPConverter] = None


def get_hwp_converter() -> HWPConverter:
    """Get or create HWP converter singleton."""
    global _hwp_converter
    if _hwp_converter is None:
        _hwp_converter = HWPConverter()
    return _hwp_converter
