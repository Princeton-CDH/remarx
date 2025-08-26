"""
Functionality for loading and chunking input files for sentence corpus creation.
"""

from remarx.sentence.corpus.base_input import FileInput
from remarx.sentence.corpus.tei_input import TEI_TAG, TEIDocument, TEIinput, TEIPage
from remarx.sentence.corpus.text_input import TextInput

__all__ = ["TEI_TAG", "FileInput", "TEIDocument", "TEIPage", "TEIinput", "TextInput"]
