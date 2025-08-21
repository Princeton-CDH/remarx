"""
Functionality for loading and chunking input files for sentence corpus creation.
"""

from remarx.sentence.corpus.base_input import FileInput
from remarx.sentence.corpus.tei_input import TEIinput
from remarx.sentence.corpus.text_input import TextInput

__all__ = ["FileInput", "TEIinput", "TextInput"]
