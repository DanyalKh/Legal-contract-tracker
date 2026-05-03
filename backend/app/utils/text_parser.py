"""
Text Processing Utility
Handles text parsing and sentence segmentation using spaCy.
"""

import os
import re
from pathlib import Path
import spacy
from fastapi import HTTPException

# Load spaCy model once at module level for efficiency
# Using en_core_web_lg with custom heading detection for legal documents
try:
    nlp = spacy.load("en_core_web_lg")
    print("✓ Loaded spaCy model: en_core_web_lg")
except OSError:
    print("✗ spaCy model not found. Run: python -m spacy download en_core_web_lg")
    nlp = None
    """
    Detect if a sentence is likely a heading/title rather than actual content.
    
    Heading characteristics:
    - Very short (< 5 words)
    - All uppercase
    - Title Case Without Punctuation
    - Starts with section/article numbers (e.g., "1.", "Article 5", "Section III")
    - No ending punctuation (. ! ?)
    - Contains only numbers and punctuation (e.g., "1.2.3")
    - Starts with all-caps words followed by regular text (merged heading + sentence)
    - Contains heading pattern with double newlines before content
    - Short title case phrases that look like section headers
    """
    # text = text.strip()
    
    # # Very short text (likely a heading)
    # word_count = len(text.split())
    # if word_count == 0:
    #     return True
    # if word_count <= 2 and not text.endswith(('.', '!', '?')):
    #     return True
    
    # # All caps (common in legal headings)
    # if text.isupper() and word_count <= 8:
    #     return True
    
    # # Check for heading pattern with double newlines: "Heading Title\n\nSentence starts..."
    # # This catches cases where spaCy merges heading and following paragraph
    # if '\n\n' in text:
    #     parts = text.split('\n\n', 1)
    #     if len(parts) == 2:
    #         heading_part = parts[0].strip()
    #         content_part = parts[1].strip()
            
    #         # If first part looks like a heading (short, title case or caps, no period)
    #         heading_words = heading_part.split()
    #         if 1 <= len(heading_words) <= 8 and not heading_part.endswith(('.', '!', '?')):
    #             # And content part starts with a capital letter (new sentence)
    #             if content_part and content_part[0].isupper():
    #                 return True
    
    # # Check if sentence STARTS with all-caps heading followed by regular text
    # # Example: "BUSINESS PARTNERSHIP AGREEMENT This Business Partnership..."
    # words = text.split()
    # if len(words) >= 2:
    #     # Check first 2-5 words - if they're all caps and form a heading pattern
    #     for heading_length in range(2, min(6, len(words) + 1)):
    #         potential_heading = ' '.join(words[:heading_length])
    #         remaining_text = ' '.join(words[heading_length:]) if heading_length < len(words) else ''
            
    #         # If first few words are all caps and there's more text after
    #         if potential_heading.isupper() and remaining_text and remaining_text[0].isupper():
    #             return True
    
    # # Check if sentence STARTS with Title Case heading followed by regular text
    # # Example: "Partnership Formation The Partners agree..."
    # if len(words) >= 3:
    #     first_two_words = ' '.join(words[:2])
    #     rest = ' '.join(words[2:]) if len(words) > 2 else ''
        
    #     # If first 2-3 words are title case and followed by "The " or "This " pattern
    #     if first_two_words.istitle() and rest.startswith(('The ', 'This ', 'Each ', 'All ', 'Any ', 'No ')):
    #         return True
    
    # # Numbered sections (e.g., "1.", "1.1", "Article 5", "Section III")
    # numbered_pattern = r'^(Article|Section|Chapter|Part|Clause|Exhibit|Appendix|Schedule)?\s*[IVXivx\d]+[\.\):]?\s*[-–—]?\s*[A-Z]?(\s+[A-Z][a-z]+)*$'
    # if re.match(numbered_pattern, text, re.IGNORECASE):
    #     # But allow if it's a longer sentence with ending punctuation
    #     if word_count <= 6 or not text.endswith(('.', '!', '?')):
    #         return True
    
    # # Title Case without ending punctuation (e.g., "Confidentiality Agreement")
    # # But be more restrictive - only if very short
    # if text.istitle() and not text.endswith(('.', '!', '?')) and word_count <= 4:
    #     return True
    
    # # Only numbers and punctuation (e.g., "1.2.3")
    # if re.match(r'^[\d\.\)\s]+$', text):
    #     return True
    
    # # Common legal section headers
    # common_headers = [
    #     'formation', 'purpose', 'term', 'contributions', 'allocation', 'management', 
    #     'decision.making', 'accounts', 'financial', 'salaries', 'distributions', 
    #     'partners', 'transfers', 'dissolution', 'exit', 'strategy', 'resolution', 
    #     'governing', 'law', 'miscellaneous', 'provisions', 'signatures'
    # ]
    
    # text_lower = text.lower()
    # if any(header in text_lower for header in common_headers) and word_count <= 6 and not text.endswith(('.', '!', '?')):
    #     return True
    
    # return False

def _is_likely_heading(text: str) -> bool:
    text = text.strip()
    
    if not text:
        return True
    
    if text.isupper() and len(text.split()) <= 8:
        return True
    
    if len(text.split()) <= 2 and not text.endswith(('.', '!', '?')):
        return True
    
    return False

def filter_sentences(sentences: list[str]) -> list[str]:
    """Cleanup of bad sentences."""
    cleaned = []

    for s in sentences:
        s = s.strip()
        if not s:
            continue

        if re.fullmatch(r'[_\-\s]{5,}', s):
            continue

        if re.match(r'^(AND|BY)\b[: ]', s):
            continue

        if re.search(r'signature|print name|date', s, re.IGNORECASE):
            if len(s.split()) < 10:
                continue

        if not _is_likely_heading(s):
            cleaned.append(s)

    return cleaned

def clean_section_text(text: str) -> str:
    import re

    text = re.sub(r'_+', ' ', text)
    text = re.sub(r'\s+', ' ', text)

    return text.strip()

def is_signature_section(title: str, content: str) -> bool:
    """Generic detection of signature blocks."""
    content_lower = content.lower()

    return (
        len(content.split()) < 40 and
        any(word in content_lower for word in ["signature", "signed", "print name", "date"])
    )

def parse_sentences(text: str) -> list[str]:
    """
    Parse text into individual sentences using spaCy's sentence segmentation.
    Automatically filters out headings, titles, and section numbers.
    
    Args:
        text: Raw text content to parse (contract text, document content, etc.)
        
    Returns:
        List of sentence strings, cleaned and stripped of extra whitespace.
        Headings and titles are automatically excluded.
        
    Raises:
        HTTPException: If spaCy model is not loaded (500 error)
    """
    if not text or not text.strip():
        return []
    
    if nlp is None:
        raise HTTPException(
            status_code=500,
            detail="spaCy model not loaded. Run: python -m spacy download en_core_web_lg"
        )
    
   
    if len(text) > 1_000_000:  # 1MB text limit
        raise HTTPException(
            status_code=400,
            detail="Text is too long. Maximum 1,000,000 characters allowed."
        )
    
    processed_text = _preprocess_text_for_segmentation(text)
    
    try:
        doc = nlp(processed_text)
        raw_sentences = [
            sent.text.strip() 
            for sent in doc.sents 
            if sent.text.strip()
            # if sent.text.strip() and not _is_likely_heading(sent.text.strip())
        ]
    
        sentences = _merge_incomplete_sentences(raw_sentences)
        
        return sentences
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error parsing text: {str(e)}"
        )


def _preprocess_text_for_segmentation(text: str) -> str:
    """
    Preserve structure. Only normalize spacing.
    """
    text = text.replace('\r\n', '\n')
    text = re.sub(r'[ \t]+', ' ', text)
    
    return text.strip()

def _merge_incomplete_sentences(sentences: list[str]) -> list[str]:
    """
    Post-process sentences to merge incomplete ones that were incorrectly split.
    
    Merges sentences that:
    - Start with lowercase words (continuations)
    - Are very short fragments (≤3 words)
    - Start with coordinating conjunctions (and, or, but, etc.)
    - Start with list continuations (a), b), c), etc.)
    - Continue list items when previous sentence ends with list markers
    """
    if not sentences:
        return sentences
    
    merged = []
    current = sentences[0]
    
    for next_sent in sentences[1:]:
        next_sent = next_sent.strip()
        if not next_sent:
            continue
            
        # Merge if:
        # 1. Starts with lowercase (continuation)
        # 2. Very short (≤3 words)
        # 3. Starts with coordinating conjunction
        # 4. Starts with list continuation (a), b), c), etc.)
        # 5. Previous sentence ends with list marker like "a)", "b)", "c)"
        should_merge = (
            next_sent[0].islower() or
            len(next_sent.split()) <= 3 or
            next_sent.lower().startswith(('and ', 'or ', 'but ', 'nor ', 'for ', 'so ', 'yet ')) or
            re.match(r'^[a-z]\)\s', next_sent.lower()) or
            re.search(r'[a-z]\)$', current.lower())
        )
        
        if should_merge:
            current += " " + next_sent
        else:
            if current.strip():
                merged.append(current)
            current = next_sent
    
    if current.strip():
        merged.append(current)
    
    return merged


def preprocess_text(text: str) -> str:
    """Keep structure, only normalize whitespace."""
    text = re.sub(r'\r\n', '\n', text)
    return text.strip()


def extract_sections(text: str) -> dict:
    import re

    sections = {}
    current_section = None
    buffer = []

    lines = text.split("\n")

    for line in lines:
        stripped = line.strip()

        if (
            stripped
            and stripped == stripped.upper()
            and len(stripped) > 3
            and not stripped.startswith("_")
        ):
            if current_section:
                sections[current_section] = " ".join(buffer).strip()
                buffer = []

            current_section = stripped
        else:
            buffer.append(line)

    if current_section:
        sections[current_section] = " ".join(buffer).strip()

    return sections

def test_parser(contract_name=None):
    """
    Updated test function:
    - DOES NOT remove headings
    - Uses section-based parsing instead of sentence parsing
    """

    print("\n" + "="*80)
    print("TESTING SECTION-AWARE CONTRACT PARSER")
    print("="*80 + "\n")

    # Path setup (unchanged)
    current_dir = Path(__file__).resolve().parent
    backend_dir = current_dir.parent.parent
    project_dir = backend_dir.parent
    contracts_dir = project_dir / "contracts"

    if not contracts_dir.exists():
        print(f"✗ Contracts folder not found at: {contracts_dir}")
        return False

    contract_files = sorted(contracts_dir.glob("*.txt"))

    if not contract_files:
        print(f"✗ No .txt files found in: {contracts_dir}")
        return False

    # Select contract
    if contract_name:
        contract_file = next((cf for cf in contract_files if cf.stem == contract_name or cf.name == contract_name), None)
        if not contract_file:
            print(f"✗ Contract '{contract_name}' not found.")
            print(f"Available: {[cf.name for cf in contract_files]}")
            return False
    else:
        contract_file = contract_files[0]

    print(f"Testing with: {contract_file.name}")
    print("=" * 80)

    try:
        # Read file
        with open(contract_file, 'r', encoding='utf-8') as f:
            content = f.read()

        print(f"\nFile size: {len(content)} characters")

        # Preview original
        print("\nORIGINAL CONTENT (first 500 chars):")
        print("-" * 80)
        print(content[:500])
        print("...\n" if len(content) > 500 else "")
        print("-" * 80)

        # ✅ NEW PIPELINE
        processed = preprocess_text(content)
        sections = extract_sections(processed)
        # remove signature sections (generic)
        sections = {
            k: v for k, v in sections.items()
            if not is_signature_section(k, v)
        }
        print(f"\n✓ EXTRACTED {len(sections)} SECTIONS (headings preserved)\n")
        
        section_sentences = {}
        for section, section_text in sections.items():
            section_text = clean_section_text(section_text)
            raw_sentences = parse_sentences(section_text)   # spaCy here
            clean_sentences = filter_sentences(raw_sentences)

            section_sentences[section] = clean_sentences

        # Print sections
        for i, (section, sentences) in enumerate(section_sentences.items(), 1):
            print(f"{i}. [{section}]")

            for j, sentence in enumerate(sentences, 1):
                print(f"   {j}. {sentence}")

            print()

        # Debug preview
        print("=" * 80)
        print("PROCESSED TEXT (first 800 chars, structure preserved):")
        print("=" * 80)
        print(processed[:800])
        print("...\n" if len(processed) > 800 else "")
        print("=" * 80)

        print("\nSUMMARY")
        print("=" * 80)
        print(f"Total text: {len(content)} chars")
        print(f"Processed text: {len(processed)} chars")
        print(f"Sections extracted: {len(sections)}")
        print("Headings preserved ✓")
        print()

        return True

    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False

if __name__ == "__main__":
    import sys
    # Run test when file is executed directly
    # Accept contract name as command line argument
    contract_name = sys.argv[1] if len(sys.argv) > 1 else None
    test_parser(contract_name)
