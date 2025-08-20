"Base text input class with common functionality"

import pathlib
from collections.abc import Generator
from dataclasses import dataclass
from functools import cached_property

from remarx.sentence.segment import segment_text


@dataclass
class TextInput:
    """Base class for file input for sentence corpus creation"""

    input_file: pathlib.Path

    #: List of field names for sentences from text input files
    field_names: tuple[str] = ("file", "offset", "text")

    @cached_property
    def file_name(self) -> str:
        """
        Input file name. Associated with sentences in generated corpus.
        """
        return self.input_file.name

    def get_text(self) -> Generator[dict[str, str]]:
        """
        Get plain-text contents for this file with any desired chunking (e.g.
        pages or other semantic unit). Returns a dictionary of
        text and any other metadata appropriate to this unit of text.
        Default implementation does no chunking, no additional metadata.
        """
        yield {"text": self.input_file.read_text(encoding="utf-8")}

    def get_sentences(self) -> Generator[dict]:
        """
        Get sentences for this file, with any associated metadata.
        """
        for chunk_info in self.get_text():
            # each chunk of text is a dictionary that at minimum
            # contains text for that chunk; it may include other metadata
            for char_idx, sentence in segment_text(chunk_info):
                # for each sentence, yield text, offset, and filename
                # with any other metadata included in chunk_info
                sentence_info = {
                    "text": sentence,
                    "offset": char_idx,
                    "file": self.file_name,
                } | chunk_info
                yield sentence_info
