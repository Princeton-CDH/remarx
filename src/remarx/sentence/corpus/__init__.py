"""
Functionality for loading and chunking input files for sentence corpus creation.
"""

from remarx.sentence.corpus.alto_input import ALTOInput
from remarx.sentence.corpus.base_input import FileInput
from remarx.sentence.corpus.tei_input import TEI_TAG, TEIDocument, TEIinput
from remarx.sentence.corpus.text_input import TextInput

__all__ = [
    "TEI_TAG",
    "ALTOInput",
    "FileInput",
    "TEIDocument",
    "TEIPage",
    "TEIinput",
    "TextInput",
]
