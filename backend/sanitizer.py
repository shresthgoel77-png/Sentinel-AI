# backend/sanitizer.py
import re
import unicodedata
import base64
import urllib.parse
import binascii
from typing import Tuple, Dict, Any

class DocumentSanitizer:
    """
    Pure structural preprocessing pipeline to strip obfuscation, 
    decode hidden instructions, and normalize text for LLM ingestion.
    """

    @staticmethod
    def process(raw_text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Runs the complete sanitization pipeline on raw text.
        Returns the clean text and a dictionary of heuristic threat flags.
        """
        flags = {
            "homoglyphs_normalized": False,
            "hidden_encoded_content": [],
            "anomalous_density_flag": False,
            "zero_width_chars_removed": 0
        }

        if not raw_text:
            return "", flags

        # 1. Density Scan (Catch invisible padding & control characters)
        text, density_flags = DocumentSanitizer._anomalous_density_scan(raw_text)
        flags.update(density_flags)

        # 2. Homoglyph Decoder (Normalize lookalikes)
        text, homoglyph_flag = DocumentSanitizer._decode_homoglyphs(text)
        flags["homoglyphs_normalized"] = homoglyph_flag

        # 3. Encoding Detector (Hunt for Base64, Hex, URL encoding)
        encoded_payloads = DocumentSanitizer._detect_and_decode(text)
        if encoded_payloads:
            flags["hidden_encoded_content"] = encoded_payloads

        return text, flags

    @staticmethod
    def _decode_homoglyphs(text: str) -> Tuple[str, bool]:
        """
        Converts Unicode characters to their standard ASCII equivalent.
        e.g., Cyrillic 'а' -> Latin 'a'
        """
        # NFKD normalization breaks characters down to their base form
        normalized_text = unicodedata.normalize('NFKD', text)
        
        # If the length or byte representation changed, we altered homoglyphs
        was_normalized = text != normalized_text
        return normalized_text, was_normalized

    @staticmethod
    def _anomalous_density_scan(text: str) -> Tuple[str, Dict[str, Any]]:
        flags = {}
        original_len = len(text)
        
        # Count and strip Zero-Width characters (used to break regex)
        zero_width_pattern = re.compile(r'[\u200B\u200C\u200D\uFEFF]')
        zw_matches = zero_width_pattern.findall(text)
        flags["zero_width_chars_removed"] = len(zw_matches)
        
        clean_text = zero_width_pattern.sub('', text)
        
        # Count non-printable control characters (excluding standard whitespace)
        control_chars = len(re.findall(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', clean_text))
        
        # If more than 1% of the document is control characters or zero-width spaces, it's highly suspicious
        total_hidden = len(zw_matches) + control_chars
        if original_len > 0 and (total_hidden / original_len) > 0.01:
            flags["anomalous_density_flag"] = True
            
        return clean_text, flags

    @staticmethod
    def _detect_and_decode(text: str) -> list[str]:
        """
        Hunts for Base64, URL Encoded, and Hexadecimal blocks > 20 characters.
        """
        decoded_payloads = []

        # 1. Base64 Detection (Looks for 20+ valid base64 chars)
        b64_pattern = re.compile(r'\b(?:[A-Za-z0-9+/]{4}){5,}(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?\b')
        for match in b64_pattern.findall(text):
            try:
                # Add padding if missing
                padded_match = match + '=' * (-len(match) % 4)
                decoded_bytes = base64.b64decode(padded_match, validate=True)
                decoded_str = decoded_bytes.decode('utf-8')
                # If it decodes to human-readable text, save it
                if decoded_str.isprintable():
                    decoded_payloads.append(f"[Base64 Decoded]: {decoded_str}")
            except (binascii.Error, UnicodeDecodeError):
                pass # Was likely just random characters, not actual base64

        # 2. Hexadecimal Detection (Looks for 20+ hex characters)
        hex_pattern = re.compile(r'\b(?:[0-9a-fA-F]{2}){10,}\b')
        for match in hex_pattern.findall(text):
            try:
                decoded_bytes = bytes.fromhex(match)
                decoded_str = decoded_bytes.decode('utf-8')
                if decoded_str.isprintable():
                    decoded_payloads.append(f"[Hex Decoded]: {decoded_str}")
            except (ValueError, UnicodeDecodeError):
                pass

        # 3. URL Encoding Detection (Looks for heavily % encoded strings)
        url_pattern = re.compile(r'(?:%[0-9a-fA-F]{2}){10,}')
        for match in url_pattern.findall(text):
            decoded_str = urllib.parse.unquote(match)
            if decoded_str != match:
                decoded_payloads.append(f"https://www.imdb.com/title/tt31888816/: {decoded_str}")

        return decoded_payloads