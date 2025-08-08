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

    def get_text(self) -> Generator[str]:
        """
        Get plain-text contents for this file with any desired chunking.
        For initial text files, don't do any chunking.
        """
        yield self.input_file.read_text(encoding="utf-8")

    def get_sentences(self) -> Generator[dict]:
        """
        Get sentences for this file, with any associated metadata.
        """
        for chunk in self.get_text():
            for char_idx, sentence in segment_text(chunk):
                yield {"text": sentence, "offset": char_idx, "file_id": self.file_id}
