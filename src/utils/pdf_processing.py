"""
PDF Processing Utility Module

"""

import io
import os
import re
from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime

# pdfminer.six imports for reading and analyzing
from pdfminer.high_level import extract_text, extract_pages
# PyPDF2 imports for editing
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from PyPDF2.generic import NameObject, createStringObject, DictionaryObject
from pdfminer.layout import LAParams, LTTextContainer, LTChar, LTPage, LTFigure, LTImage
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.pdftypes import resolve1
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter, PDFPageAggregator
from pdfminer.pdfpage import PDFPage


class PDFProcessor:
    """
    A class for processing PDF files using pdfminer.six.
    
    This class provides methods for extracting text, analyzing structure,
    and working with PDF documents.
    """
    
    def __init__(self, file_path: Optional[str] = None, file_bytes: Optional[bytes] = None):
        """
        Initialize the PDF processor with either a file path or file bytes.
        
        Args:
            file_path: Path to the PDF file
            file_bytes: PDF file as bytes
        
        Raises:
            ValueError: If neither file_path nor file_bytes is provided
        """
        if not file_path and not file_bytes:
            raise ValueError("Either file_path or file_bytes must be provided")
        
        self.file_path = file_path
        self.file_bytes = file_bytes
        self._document = None
        self._metadata = None
    
    def _get_file_object(self) -> Union[io.BytesIO, io.FileIO]:
        """
        Get a file object for the PDF, either from file_path or file_bytes.
        
        Returns:
            A file object (BytesIO or FileIO)
        """
        if self.file_bytes:
            return io.BytesIO(self.file_bytes)
        return open(self.file_path, 'rb')
    
    def extract_text(self, page_numbers: Optional[List[int]] = None) -> str:
        """
        Extract text from the PDF document.
        
        Args:
            page_numbers: List of page numbers to extract (0-based). If None, extract all pages.
        
        Returns:
            Extracted text as a string
        """
        with self._get_file_object() as fp:
            if page_numbers is not None:
                pages = [p for i, p in enumerate(PDFPage.get_pages(fp)) if i in page_numbers]
                fp.seek(0)  # Reset file pointer
            else:
                pages = None
            
            return extract_text(fp, page_numbers=pages)
    
    def extract_text_by_page(self) -> List[str]:
        """
        Extract text from the PDF document, separated by page.
        
        Returns:
            List of strings, where each string is the text from one page
        """
        result = []
        with self._get_file_object() as fp:
            for page_layout in extract_pages(fp):
                page_text = ""
                for element in page_layout:
                    if isinstance(element, LTTextContainer):
                        page_text += element.get_text()
                result.append(page_text)
        return result
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Extract metadata from the PDF document.
        
        Returns:
            Dictionary containing PDF metadata
        """
        if self._metadata is not None:
            return self._metadata
        
        with self._get_file_object() as fp:
            parser = PDFParser(fp)
            doc = PDFDocument(parser)
            metadata = {}
            
            if 'Info' in doc.catalog:
                info = resolve1(doc.catalog['Info'])
                for key, value in info.items():
                    if isinstance(value, bytes):
                        metadata[key.decode('utf-8')] = value.decode('utf-8', errors='replace')
                    else:
                        metadata[key.decode('utf-8')] = value
            
            # Add document structure information
            metadata['PageCount'] = len(list(doc.get_pages()))
            
            self._metadata = metadata
            return metadata
    
    def count_pages(self) -> int:
        """
        Count the number of pages in the PDF.
        
        Returns:
            Number of pages
        """
        return self.get_metadata().get('PageCount', 0)
    
    def extract_images_info(self) -> List[Dict[str, Any]]:
        """
        Extract information about images in the PDF.
        
        Note: This method does not extract the actual image data, just information about them.
        
        Returns:
            List of dictionaries containing image information
        """
        images_info = []
        
        with self._get_file_object() as fp:
            resource_manager = PDFResourceManager()
            laparams = LAParams()
            device = PDFPageAggregator(resource_manager, laparams=laparams)
            interpreter = PDFPageInterpreter(resource_manager, device)
            
            for page_num, page in enumerate(PDFPage.get_pages(fp)):
                interpreter.process_page(page)
                layout = device.get_result()
                
                for element in layout:
                    if isinstance(element, LTFigure) or isinstance(element, LTImage):
                        images_info.append({
                            'page_number': page_num + 1,
                            'x0': element.x0,
                            'y0': element.y0,
                            'x1': element.x1,
                            'y1': element.y1,
                            'width': element.width,
                            'height': element.height,
                            'type': type(element).__name__
                        })
        
        return images_info
    
    def extract_tables(self, page_numbers: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """
        Attempt to identify and extract tabular data from the PDF.
        
        This is a basic implementation that looks for text aligned in columns.
        For more accurate table extraction, consider using specialized libraries
        like tabula-py or camelot-py.
        
        Args:
            page_numbers: List of page numbers to extract tables from (0-based).
                          If None, extract from all pages.
        
        Returns:
            List of dictionaries containing table information
        """
        tables = []
        
        with self._get_file_object() as fp:
            resource_manager = PDFResourceManager()
            laparams = LAParams()
            device = PDFPageAggregator(resource_manager, laparams=laparams)
            interpreter = PDFPageInterpreter(resource_manager, device)
            
            for page_num, page in enumerate(PDFPage.get_pages(fp)):
                if page_numbers is not None and page_num not in page_numbers:
                    continue
                
                interpreter.process_page(page)
                layout = device.get_result()
                
                # Simple table detection based on text alignment
                text_elements = [e for e in layout if isinstance(e, LTTextContainer)]
                
                # Group text elements by y-coordinate (rows)
                rows = {}
                for elem in text_elements:
                    y_key = round(elem.y0)  # Round to group nearby elements
                    if y_key not in rows:
                        rows[y_key] = []
                    rows[y_key].append(elem)
                
                # Sort rows by y-coordinate (top to bottom)
                sorted_rows = [rows[y] for y in sorted(rows.keys(), reverse=True)]
                
                # If we have multiple rows with multiple elements, it might be a table
                if len(sorted_rows) > 2 and all(len(row) > 1 for row in sorted_rows[:3]):
                    table_data = []
                    for row in sorted_rows:
                        # Sort elements in row by x-coordinate (left to right)
                        sorted_row = sorted(row, key=lambda e: e.x0)
                        row_data = [elem.get_text().strip() for elem in sorted_row]
                        table_data.append(row_data)
                    
                    tables.append({
                        'page_number': page_num + 1,
                        'data': table_data
                    })
        
        return tables
    
    def search_text(self, pattern: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """
        Search for text matching a pattern in the PDF.
        
        Args:
            pattern: Regular expression pattern to search for
            case_sensitive: Whether the search should be case-sensitive
        
        Returns:
            List of dictionaries containing match information
        """
        results = []
        flags = 0 if case_sensitive else re.IGNORECASE
        
        pages_text = self.extract_text_by_page()
        for page_num, page_text in enumerate(pages_text):
            for match in re.finditer(pattern, page_text, flags):
                # Get some context around the match
                start = max(0, match.start() - 50)
                end = min(len(page_text), match.end() + 50)
                context = page_text[start:end]
                
                results.append({
                    'page_number': page_num + 1,
                    'match': match.group(),
                    'context': context,
                    'start_pos': match.start(),
                    'end_pos': match.end()
                })
        
        return results
    
    def extract_forms(self) -> List[Dict[str, Any]]:
        """
        Extract form fields from the PDF if present.
        
        Returns:
            List of dictionaries containing form field information
        """
        # Note: This is a basic implementation. For more advanced form extraction,
        # consider using PyPDF2 or pdfrw libraries.
        form_fields = []
        
        with self._get_file_object() as fp:
            parser = PDFParser(fp)
            doc = PDFDocument(parser)
            
            if 'AcroForm' in doc.catalog:
                acroform = resolve1(doc.catalog['AcroForm'])
                if 'Fields' in acroform:
                    fields = resolve1(acroform['Fields'])
                    for i, field_ref in enumerate(fields):
                        field = resolve1(field_ref)
                        field_info = {
                            'index': i,
                            'type': field.get('FT', '').decode('utf-8') if isinstance(field.get('FT', ''), bytes) else '',
                            'name': field.get('T', '').decode('utf-8') if isinstance(field.get('T', ''), bytes) else '',
                            'value': field.get('V', '').decode('utf-8') if isinstance(field.get('V', ''), bytes) else '',
                            'flags': field.get('Ff', 0)
                        }
                        form_fields.append(field_info)
        
        return form_fields
    
    def analyze_document(self) -> Dict[str, Any]:
        """
        Perform a comprehensive analysis of the PDF document.
        
        Returns:
            Dictionary containing analysis results
        """
        analysis = {
            'metadata': self.get_metadata(),
            'page_count': self.count_pages(),
            'text_sample': self.extract_text()[:1000] + '...' if len(self.extract_text()) > 1000 else self.extract_text(),
            'images_count': len(self.extract_images_info()),
            'has_forms': len(self.extract_forms()) > 0,
        }
        
        # Estimate document type based on content
        if analysis['has_forms']:
            analysis['document_type'] = 'form'
        elif analysis['images_count'] > analysis['page_count'] * 2:
            analysis['document_type'] = 'image-heavy'
        elif len(self.extract_tables()) > 0:
            analysis['document_type'] = 'tabular'
        else:
            analysis['document_type'] = 'text'
        
        # Estimate language (very basic)
        text = self.extract_text()
        if re.search(r'[а-яА-Я]', text):
            analysis['language'] = 'Russian'
        elif re.search(r'[一-龯]', text):
            analysis['language'] = 'Chinese'
        elif re.search(r'[あ-んア-ン]', text):
            analysis['language'] = 'Japanese'
        elif re.search(r'[가-힣]', text):
            analysis['language'] = 'Korean'
        else:
            analysis['language'] = 'English/Latin'
        
        return analysis

# PDF Editing Functionality

class PDFEditor:
    """
    A class for editing PDF files using PyPDF2.
    
    This class provides methods for modifying PDF documents, including
    merging, splitting, adding text, rotating pages, and more.
    """
    
    def __init__(self, file_path: str):
        """
        Initialize the PDF editor with a file path.
        
        Args:
            file_path: Path to the PDF file
        """
        self.file_path = file_path
        self._reader = None
    
    @property
    def reader(self) -> PdfReader:
        """
        Get a PdfReader instance for the PDF file.
        
        Returns:
            PdfReader instance
        """
        if self._reader is None:
            self._reader = PdfReader(self.file_path)
        return self._reader
    
    def get_page_count(self) -> int:
        """
        Get the number of pages in the PDF.
        
        Returns:
            Number of pages
        """
        return len(self.reader.pages)
    
    def extract_pages(self, page_numbers: List[int], output_path: str) -> str:
        """
        Extract specific pages from the PDF and save to a new file.
        
        Args:
            page_numbers: List of page numbers to extract (0-based)
            output_path: Path to save the new PDF
        
        Returns:
            Path to the new PDF file
        """
        writer = PdfWriter()
        
        for page_num in page_numbers:
            if 0 <= page_num < len(self.reader.pages):
                writer.add_page(self.reader.pages[page_num])
        
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        return output_path
    
    def merge_pdfs(self, pdf_paths: List[str], output_path: str) -> str:
        """
        Merge multiple PDFs into a single PDF.
        
        Args:
            pdf_paths: List of paths to PDF files to merge
            output_path: Path to save the merged PDF
        
        Returns:
            Path to the merged PDF file
        """
        merger = PdfMerger()
        
        # Add the current PDF first
        merger.append(self.file_path)
        
        # Add the other PDFs
        for pdf_path in pdf_paths:
            merger.append(pdf_path)
        
        # Write the merged PDF to file
        with open(output_path, 'wb') as output_file:
            merger.write(output_file)
        
        return output_path
    
    def rotate_pages(self, page_numbers: List[int], rotation: int, output_path: str) -> str:
        """
        Rotate specific pages in the PDF.
        
        Args:
            page_numbers: List of page numbers to rotate (0-based)
            rotation: Rotation angle in degrees (90, 180, 270)
            output_path: Path to save the modified PDF
        
        Returns:
            Path to the modified PDF file
        """
        writer = PdfWriter()
        
        for i in range(len(self.reader.pages)):
            page = self.reader.pages[i]
            
            if i in page_numbers:
                page.rotate(rotation)
            
            writer.add_page(page)
        
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        return output_path
    
    def add_watermark(self, watermark_pdf: str, output_path: str) -> str:
        """
        Add a watermark to each page of the PDF.
        
        Args:
            watermark_pdf: Path to the PDF containing the watermark
            output_path: Path to save the watermarked PDF
        
        Returns:
            Path to the watermarked PDF file
        """
        watermark_reader = PdfReader(watermark_pdf)
        watermark_page = watermark_reader.pages[0]
        
        writer = PdfWriter()
        
        for page in self.reader.pages:
            page.merge_page(watermark_page)
            writer.add_page(page)
        
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        return output_path
    
    def encrypt_pdf(self, output_path: str, user_password: str, owner_password: Optional[str] = None) -> str:
        """
        Encrypt the PDF with a password.
        
        Args:
            output_path: Path to save the encrypted PDF
            user_password: Password required to open the PDF
            owner_password: Password required to modify the PDF (if None, same as user_password)
        
        Returns:
            Path to the encrypted PDF file
        """
        writer = PdfWriter()
        
        for page in self.reader.pages:
            writer.add_page(page)
        
        writer.encrypt(user_password, owner_password or user_password)
        
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        return output_path
    
    def add_metadata(self, metadata: Dict[str, str], output_path: str) -> str:
        """
        Add or update metadata in the PDF.
        
        Args:
            metadata: Dictionary of metadata to add/update
            output_path: Path to save the modified PDF
        
        Returns:
            Path to the modified PDF file
        """
        writer = PdfWriter()
        
        # Copy all pages
        for page in self.reader.pages:
            writer.add_page(page)
        
        # Update metadata
        writer.add_metadata(metadata)
        
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        return output_path
    
    def split_pdf(self, output_dir: str, prefix: str = "page_") -> List[str]:
        """
        Split the PDF into individual pages.
        
        Args:
            output_dir: Directory to save the individual pages
            prefix: Prefix for the output filenames
        
        Returns:
            List of paths to the individual page files
        """
        os.makedirs(output_dir, exist_ok=True)
        output_paths = []
        
        for i, page in enumerate(self.reader.pages):
            output_path = os.path.join(output_dir, f"{prefix}{i+1}.pdf")
            
            writer = PdfWriter()
            writer.add_page(page)
            
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            output_paths.append(output_path)
        
        return output_paths
    
    def add_text_annotation(self, page_number: int, text: str, rect: Tuple[float, float, float, float], 
                           output_path: str) -> str:
        """
        Add a text annotation to a page in the PDF.
        
        Args:
            page_number: Page number to add the annotation to (0-based)
            text: Text of the annotation
            rect: Rectangle coordinates (x1, y1, x2, y2) for the annotation
            output_path: Path to save the modified PDF
        
        Returns:
            Path to the modified PDF file
        """
        writer = PdfWriter()
        
        # Copy all pages
        for i, page in enumerate(self.reader.pages):
            writer.add_page(page)
            
            # Add annotation to the specified page
            if i == page_number:
                # Create annotation dictionary
                annotation = DictionaryObject()
                annotation.update({
                    NameObject("/Type"): NameObject("/Annot"),
                    NameObject("/Subtype"): NameObject("/Text"),
                    NameObject("/Rect"): [rect[0], rect[1], rect[2], rect[3]],
                    NameObject("/Contents"): createStringObject(text),
                    NameObject("/Open"): NameObject("true"),
                })
                
                # Add annotation to page
                page_object = writer.pages[i]
                if "/Annots" in page_object:
                    page_object[NameObject("/Annots")].append(annotation)
                else:
                    page_object[NameObject("/Annots")] = [annotation]
        
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        return output_path

def extract_text_from_pdf(file_path: str, page_numbers: Optional[List[int]] = None) -> str:
    """
    Extract text from a PDF file.
    
    Args:
        file_path: Path to the PDF file
        page_numbers: List of page numbers to extract (0-based). If None, extract all pages.
    
    Returns:
        Extracted text as a string
    """
    processor = PDFProcessor(file_path=file_path)
    return processor.extract_text(page_numbers=page_numbers)


def extract_text_from_pdf_bytes(file_bytes: bytes, page_numbers: Optional[List[int]] = None) -> str:
    """
    Extract text from PDF bytes.
    
    Args:
        file_bytes: PDF file as bytes
        page_numbers: List of page numbers to extract (0-based). If None, extract all pages.
    
    Returns:
        Extracted text as a string
    """
    processor = PDFProcessor(file_bytes=file_bytes)
    return processor.extract_text(page_numbers=page_numbers)


def get_pdf_metadata(file_path: str) -> Dict[str, Any]:
    """
    Extract metadata from a PDF file.
    
    Args:
        file_path: Path to the PDF file
    
    Returns:
        Dictionary containing PDF metadata
    """
    processor = PDFProcessor(file_path=file_path)
    return processor.get_metadata()


def analyze_pdf(file_path: str) -> Dict[str, Any]:
    """
    Perform a comprehensive analysis of a PDF file.
    
    Args:
        file_path: Path to the PDF file
    
    Returns:
        Dictionary containing analysis results
    """
    processor = PDFProcessor(file_path=file_path)
    return processor.analyze_document()


def search_pdf(file_path: str, pattern: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
    """
    Search for text matching a pattern in a PDF file.
    
    Args:
        file_path: Path to the PDF file
        pattern: Regular expression pattern to search for
        case_sensitive: Whether the search should be case-sensitive
    
    Returns:
        List of dictionaries containing match information
    """
    processor = PDFProcessor(file_path=file_path)
    return processor.search_text(pattern, case_sensitive)

# Helper functions for PDF editing

def merge_pdfs(pdf_paths: List[str], output_path: str) -> str:
    """
    Merge multiple PDFs into a single PDF.
    
    Args:
        pdf_paths: List of paths to PDF files to merge
        output_path: Path to save the merged PDF
    
    Returns:
        Path to the merged PDF file
    """
    merger = PdfMerger()
    
    for pdf_path in pdf_paths:
        merger.append(pdf_path)
    
    with open(output_path, 'wb') as output_file:
        merger.write(output_file)
    
    return output_path


def split_pdf(input_path: str, output_dir: str, prefix: str = "page_") -> List[str]:
    """
    Split a PDF into individual pages.
    
    Args:
        input_path: Path to the input PDF file
        output_dir: Directory to save the individual pages
        prefix: Prefix for the output filenames
    
    Returns:
        List of paths to the individual page files
    """
    editor = PDFEditor(input_path)
    return editor.split_pdf(output_dir, prefix)


def extract_pages(input_path: str, page_numbers: List[int], output_path: str) -> str:
    """
    Extract specific pages from a PDF and save to a new file.
    
    Args:
        input_path: Path to the input PDF file
        page_numbers: List of page numbers to extract (0-based)
        output_path: Path to save the new PDF
    
    Returns:
        Path to the new PDF file
    """
    editor = PDFEditor(input_path)
    return editor.extract_pages(page_numbers, output_path)


def rotate_pdf_pages(input_path: str, page_numbers: List[int], rotation: int, output_path: str) -> str:
    """
    Rotate specific pages in a PDF.
    
    Args:
        input_path: Path to the input PDF file
        page_numbers: List of page numbers to rotate (0-based)
        rotation: Rotation angle in degrees (90, 180, 270)
        output_path: Path to save the modified PDF
    
    Returns:
        Path to the modified PDF file
    """
    editor = PDFEditor(input_path)
    return editor.rotate_pages(page_numbers, rotation, output_path)


def add_watermark(input_path: str, watermark_pdf: str, output_path: str) -> str:
    """
    Add a watermark to each page of a PDF.
    
    Args:
        input_path: Path to the input PDF file
        watermark_pdf: Path to the PDF containing the watermark
        output_path: Path to save the watermarked PDF
    
    Returns:
        Path to the watermarked PDF file
    """
    editor = PDFEditor(input_path)
    return editor.add_watermark(watermark_pdf, output_path)


def encrypt_pdf(input_path: str, output_path: str, user_password: str, owner_password: Optional[str] = None) -> str:
    """
    Encrypt a PDF with a password.
    
    Args:
        input_path: Path to the input PDF file
        output_path: Path to save the encrypted PDF
        user_password: Password required to open the PDF
        owner_password: Password required to modify the PDF (if None, same as user_password)
    
    Returns:
        Path to the encrypted PDF file
    """
    editor = PDFEditor(input_path)
    return editor.encrypt_pdf(output_path, user_password, owner_password)


def add_pdf_metadata(input_path: str, metadata: Dict[str, str], output_path: str) -> str:
    """
    Add or update metadata in a PDF.
    
    Args:
        input_path: Path to the input PDF file
        metadata: Dictionary of metadata to add/update
        output_path: Path to save the modified PDF
    
    Returns:
        Path to the modified PDF file
    """
    editor = PDFEditor(input_path)
    return editor.add_metadata(metadata, output_path)


def add_text_annotation(input_path: str, page_number: int, text: str, 
                       rect: Tuple[float, float, float, float], output_path: str) -> str:
    """
    Add a text annotation to a page in a PDF.
    
    Args:
        input_path: Path to the input PDF file
        page_number: Page number to add the annotation to (0-based)
        text: Text of the annotation
        rect: Rectangle coordinates (x1, y1, x2, y2) for the annotation
        output_path: Path to save the modified PDF
    
    Returns:
        Path to the modified PDF file
    """
    editor = PDFEditor(input_path)
    return editor.add_text_annotation(page_number, text, rect, output_path)
