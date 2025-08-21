"Input class for handling basic text file as input for corpus creation."

from collections.abc import Generator
from dataclasses import dataclass

from remarx.sentence.corpus.base_input import FileInput


@dataclass
class TextInput(FileInput):
    """
    Basic text file input handling for sentence corpus creation. Takes
    a single text input file and returns text without chunking.
    """

    file_type = ".txt"
    "Supported file extension for text input"

    def get_text(self) -> Generator[dict[str, str]]:
        """
        Get plain-text contents for this file with any desired chunking (e.g.
        pages or other semantic unit).
        Default implementation does no chunking, no additional metadata.

        :returns: Generator with a dictionary of text and any other metadata
        that applies to this unit of text.
        """
        yield {"text": self.input_file.read_text(encoding="utf-8")}
