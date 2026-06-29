import io
import re
import fitz  # PyMuPDF
import docx2txt
from bs4 import BeautifulSoup
from typing import Tuple, Dict, Any

class SecureDocumentExtractor:
    
    @staticmethod
    async def extract(file_bytes: bytes, filename: str, content_type: str) -> Tuple[str, str, Dict[str, Any]]:
        """
        Routes the file stream to the specialized secure parser based on extension/content-type.
        Returns: (plaintext, metadata_payload, security_flags)
        """
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        
        if content_type == "application/pdf" or ext == "pdf":
            return SecureDocumentExtractor._parse_pdf(file_bytes)
        elif content_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"] or ext in ["docx", "doc"]:
            return SecureDocumentExtractor._parse_docx(file_bytes)
        elif content_type in ["text/html", "application/xhtml+xml"] or ext in ["html", "htm"]:
            return SecureDocumentExtractor._parse_html(file_bytes.decode("utf-8", errors="ignore"))
        elif ext == "md":
            return SecureDocumentExtractor._parse_markdown(file_bytes.decode("utf-8", errors="ignore"))
        else:
            # Fallback for plain text or unknown types (treated as plaintext)
            plaintext = file_bytes.decode("utf-8", errors="ignore")
            return plaintext, "", {"obfuscation_scanned": False, "note": "Raw fallback parsing applied."}

    @staticmethod
    def _parse_pdf(file_bytes: bytes) -> Tuple[str, str, Dict[str, Any]]:
        plaintext_chunks = []
        hidden_chunks = []
        security_flags = {"hidden_text_detected": False, "microfont_detected": False}
        
        # Open PDF directly from the byte stream
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        
        for page_num, page in enumerate(doc):
            # "dict" format exposes precise structural properties (fonts, sizes, colors, bboxes)
            text_page = page.get_text("dict")
            
            for block in text_page.get("blocks", []):
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if not text:
                            continue
                        
                        font_size = span["size"]
                        font_color = span["color"] # Expressed as integer (e.g., 16777215 for 0xFFFFFF / White)
                        
                        # Flag 1: Micro-text/Zero-font anomalies (Common prompt injection hiding vector)
                        if font_size < 2.0:
                            security_flags["microfont_detected"] = True
                            hidden_chunks.append(f"[Page {page_num} Microfont {font_size}pt]: {text}")
                            continue
                        
                        # Flag 2: Invisible/White text (Font matches a standard white background)
                        # 16777215 is RGB(255, 255, 255)
                        if font_color == 16777215:
                            security_flags["hidden_text_detected"] = True
                            hidden_chunks.append(f"[Page {page_num} White-on-White]: {text}")
                            continue
                            
                        plaintext_chunks.append(text)
                        
        return " ".join(plaintext_chunks), "\n".join(hidden_chunks), security_flags

    @staticmethod
    def _parse_docx(file_bytes: bytes) -> Tuple[str, str, Dict[str, Any]]:
        # docx2txt processes file-like objects natively
        file_stream = io.BytesIO(file_bytes)
        plaintext = docx2txt.process(file_stream)
        
        # Word documents lack trivial color extractions through basic zip streams without deep XML structural processing.
        # We flag docx for deep downstream pattern checking rather than layout manipulation checks.
        security_flags = {"structural_scan": "surface_level_docx"}
        return plaintext, "", security_flags

    @staticmethod
    def _parse_html(html_content: str) -> Tuple[str, str, Dict[str, Any]]:
        soup = BeautifulSoup(html_content, "html.parser")
        security_flags = {"hidden_inputs_found": False, "meta_tags_extracted": False}
        metadata_payload_chunks = []
        
        # 1. Capture and isolate explicitly hidden elements
        hidden_elements = soup.find_all(attrs={"type": "hidden"})
        if hidden_elements:
            security_flags["hidden_inputs_found"] = True
            for elem in hidden_elements:
                name = elem.get("name", "unnamed")
                val = elem.get("value", "")
                metadata_payload_chunks.append(f"[Hidden Input - {name}]: {val}")
        
        # 2. Extract Alt text and titles (Prime real estate for hidden system overrides)
        for tag in soup.find_all(True):
            if tag.has_attr("alt"):
                metadata_payload_chunks.append(f"[{tag.name} Alt Text]: {tag['alt']}")
            if tag.has_attr("title"):
                metadata_payload_chunks.append(f"[{tag.name} Title]: {tag['title']}")
                
        # 3. Pull out headers, descriptions, and structural meta properties
        meta_tags = soup.find_all("meta")
        if meta_tags:
            security_flags["meta_tags_extracted"] = True
            for meta in meta_tags:
                attrs = {k: v for k, v in meta.attrs.items()}
                metadata_payload_chunks.append(f"[Meta Property]: {attrs}")
        
        # Extract body plaintext cleanly
        plaintext = soup.get_text(separator=" ")
        # Clean up multi-line whitespace fragmentation
        plaintext = re.sub(r'\s+', ' ', plaintext).strip()
        
        return plaintext, "\n".join(metadata_payload_chunks), security_flags

    @staticmethod
    def _parse_markdown(md_content: str) -> Tuple[str, str, Dict[str, Any]]:
        security_flags = {"front_matter_extracted": False}
        metadata_payload_chunks = []
        
        # Extract Front Matter (YAML blocks demarcated by triple dashes at file start)
        front_matter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', md_content, re.DOTALL)
        clean_markdown = md_content
        
        if front_matter_match:
            security_flags["front_matter_extracted"] = True
            front_matter_content = front_matter_match.group(1)
            metadata_payload_chunks.append(f"[Markdown Front Matter]:\n{front_matter_content}")
            # Strip front matter out of the main plaintext to prevent accidental ingestion pollution
            clean_markdown = md_content[front_matter_match.end():]
            
        # Parse standard Markdown as HTML via BeautifulSoup to pull standard image alt texts or embedded raw HTML hooks
        # HTML strings embedded within markdown documents are dangerous vectors.
        _, html_metadata, html_flags = SecureDocumentExtractor._parse_html(clean_markdown)
        
        if html_metadata:
            metadata_payload_chunks.append(html_metadata)
            security_flags.update(html_flags)
            
        return clean_markdown, "\n".join(metadata_payload_chunks), security_flags