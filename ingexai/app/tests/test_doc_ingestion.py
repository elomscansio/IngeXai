import pytest
from app.services import doc_ingestion

def test_extract_text_from_txt():
    text = "Hello world!"
    result = doc_ingestion.extract_text_from_txt(text.encode("utf-8"))
    assert result == text

def test_chunk_text_basic():
    text = "one two three four five six"
    chunks = doc_ingestion.chunk_text(text, chunk_size=2)
    assert chunks == ["one two", "three four", "five six"]

def test_chunk_text_handles_remainder():
    text = "one two three"
    chunks = doc_ingestion.chunk_text(text, chunk_size=2)
    assert chunks == ["one two", "three"]

def test_chunk_text_empty():
    chunks = doc_ingestion.chunk_text("", chunk_size=2)
    assert chunks == []

def test_chunk_text_large_chunk_size():
    text = "one two three"
    chunks = doc_ingestion.chunk_text(text, chunk_size=10)
    assert chunks == ["one two three"]

def test_chunk_text_single_word():
    chunks = doc_ingestion.chunk_text("hello", chunk_size=2)
    assert chunks == ["hello"]

def test_chunk_text_negative_chunk_size():
    with pytest.raises(ValueError):
        doc_ingestion.chunk_text("one two", chunk_size=-1)

def test_chunk_text_zero_chunk_size():
    with pytest.raises(ValueError):
        doc_ingestion.chunk_text("one two", chunk_size=0)

def test_extract_text_from_pdf(monkeypatch):
    class DummyPage:
        def extract_text(self):
            return "PDF page text"
    class DummyReader:
        pages = [DummyPage(), DummyPage()]
    monkeypatch.setattr("app.services.doc_ingestion.PdfReader", lambda _: DummyReader())
    result = doc_ingestion.extract_text_from_pdf(b"dummy")
    assert result == "PDF page textPDF page text"

def test_extract_text_from_pdf_empty(monkeypatch):
    class DummyPage:
        def extract_text(self):
            return ""
    class DummyReader:
        pages = [DummyPage()]
    monkeypatch.setattr("app.services.doc_ingestion.PdfReader", lambda _: DummyReader())
    result = doc_ingestion.extract_text_from_pdf(b"dummy")
    assert result == ""

def test_extract_text_from_docx(monkeypatch):
    class DummyPara:
        def __init__(self, text):
            self.text = text
    class DummyDoc:
        paragraphs = [DummyPara("First"), DummyPara("Second")]
    monkeypatch.setattr("app.services.doc_ingestion.docx.Document", lambda _: DummyDoc())
    result = doc_ingestion.extract_text_from_docx(b"dummy")
    assert result == "First\nSecond"

def test_extract_text_from_docx_empty(monkeypatch):
    class DummyDoc:
        paragraphs = []
    monkeypatch.setattr("app.services.doc_ingestion.docx.Document", lambda _: DummyDoc())
    result = doc_ingestion.extract_text_from_docx(b"dummy")
    assert result == ""

def test_extract_text_from_txt_non_utf8():
    # Should raise UnicodeDecodeError for non-UTF-8 bytes
    with pytest.raises(UnicodeDecodeError):
        doc_ingestion.extract_text_from_txt(b"\xff\xfe\xfd")

def test_extract_text_from_txt_empty():
    assert doc_ingestion.extract_text_from_txt(b"") == ""

def test_extract_text_from_pdf_non_text_page(monkeypatch):
    class DummyPage:
        def extract_text(self):
            return None
    class DummyReader:
        pages = [DummyPage()]
    monkeypatch.setattr("app.services.doc_ingestion.PdfReader", lambda _: DummyReader())
    result = doc_ingestion.extract_text_from_pdf(b"dummy")
    assert result == ""

def test_extract_text_from_docx_non_utf8(monkeypatch):
    class DummyDoc:
        paragraphs = [type("DummyPara", (), {"text": "áéíóú"})()]
    monkeypatch.setattr("app.services.doc_ingestion.docx.Document", lambda _: DummyDoc())
    result = doc_ingestion.extract_text_from_docx(b"dummy")
    assert result == "áéíóú"

def test_chunk_text_unicode():
    text = "áéí óú üñ"
    chunks = doc_ingestion.chunk_text(text, chunk_size=2)
    assert chunks == ["áéí óú", "üñ"]

def test_chunk_text_mixed_languages():
    text = "hello 你好 привет"
    chunks = doc_ingestion.chunk_text(text, chunk_size=2)
    assert chunks == ["hello 你好", "привет"]

def test_chunk_text_with_punctuation():
    text = "Hello, world! This is a test."
    chunks = doc_ingestion.chunk_text(text, chunk_size=3)
    assert chunks == ["Hello, world! This", "is a test."]
