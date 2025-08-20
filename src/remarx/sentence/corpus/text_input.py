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

    def get_sentences(self) -> Generator[dict[str, any]]:
        """
        Get sentences for this file, with any associated metadata.
        """
        # zero-based sentence index for this file, across all chunks
        sentence_index = 0
        for chunk_info in self.get_text():
            # each chunk of text is a dictionary that at minimum
            # contains text for that chunk; it may include other metadata
            for _char_idx, sentence in segment_text(chunk_info):
                # for each sentence, yield text, filename, and sentence index
                # with any other metadata included in chunk_info

                # character index is not included in output,
                # but may be useful for sub-chunk metadata (e.g., line number)

                sentence_info = {
                    "text": sentence,
                    "file": self.file_name,
                    "sent_index": sentence_index,
                } | chunk_info
                yield sentence_info

                # increment sentence index
                sentence_index += 1
