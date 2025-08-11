"base text input class with common functionality"

import pathlib
from collections.abc import Generator
from dataclasses import dataclass
from functools import cached_property

from remarx.sentence.segment import segment_text


@dataclass
class TextInput:
    """base class for file input for sentence corpus creation"""

    input_file: pathlib.Path

    @cached_property
    def file_id(self) -> str:
        """
        Identifier for this file, to be associated with sentences in
        generated corpus. Default implementation is filename.
        """
        return self.input_file.name

    def field_names(self) -> str:
        """
        List of field names for sentences from this format input.
        """
        # should this be a class method? static class variable ?
        return ["file_id", "offset", "text"]

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
            chunk_text = chunk_info.pop("text")
            for char_idx, sentence in segment_text(chunk_text):
                sentence_info = {
                    "text": sentence,
                    "offset": char_idx,
                    "file_id": self.file_id,
                }
                # if the text dictionary includes anything other than text,
                # (e.g., page number), add to each sentence result
                if chunk_info:
                    sentence_info.update(chunk_info)
                yield sentence_info
