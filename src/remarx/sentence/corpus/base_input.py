"""
Base file input class with common functionality. Provides a factory
method for initialization of known input classes based on supported
file types.

To initialize the appropriate subclass for a supported file type,
use [FileInput.create()][remarx.sentence.corpus.base_input.FileInput.create].

For a list of supported file types across all registered input classes,
use [FileInput.supported_types()][remarx.sentence.corpus.base_input.FileInput.supported_types].

Subclasses must define a supported `file_type` extension and implement
the `get_text` method. For discovery, input classes must be imported in
`remarx.sentence.corpus.__init__` and included in `__all__` to ensure
they are found as available input classes.

"""

import pathlib
from collections.abc import Generator
from dataclasses import dataclass
from enum import StrEnum
from functools import cached_property
from typing import Any, ClassVar, Self

from remarx.sentence.segment import segment_text


@dataclass
class FileInput:
    """Base class for file input for sentence corpus creation"""

    input_file: pathlib.Path
    "Reference to input file. Source of content for sentences."

    filename_override: str = None
    "Optional filename override, e.g. when using temporary files as input"

    field_names: ClassVar[tuple[str, ...]] = ("sent_id", "file", "sent_index", "text")
    "List of field names for sentences from text input files."

    file_type: ClassVar[str]
    "Supported file extension; subclasses must define"

    @cached_property
    def file_name(self) -> str:
        """
        Input file name. Associated with sentences in generated corpus.
        """
        return self.filename_override or self.input_file.name

    def get_text(self) -> Generator[dict[str, str]]:
        """
        Get plain-text contents for this input file with any desired chunking
        (e.g. pages or other semantic unit).
        Subclasses must implement; no default implementation.

        :returns: Generator with a dictionary of text and any other metadata
        that applies to this unit of text.
        """
        raise NotImplementedError

    def get_extra_metadata(
        self, chunk_info: dict[str, Any], _char_idx: int, sentence: str
    ) -> dict[str, Any]:
        """
        Hook method for subclasses to override to provide extra metadata for a sentence (e.g. line number).

        :returns: Dictionary of additional metadata fields to include, or empty dict
        """
        return {}

    def get_sentences(self) -> Generator[dict[str, Any]]:
        """
        Get sentences for this file, with associated metadata.

        :returns: Generator of one dictionary per sentence; dictionary
        always includes: `text` (text content), `file` (filename),
        `sent_index` (sentence index within the document), and `sent_id`
        (sentence id). It may include other metadata, depending
        on the input file type.
        """
        # zero-based sentence index for this file, across all chunks
        sentence_index = 0
        for chunk_info in self.get_text():
            # each chunk of text is a dictionary that at minimum
            # contains text for that chunk; it may include other metadata
            chunk_text = chunk_info["text"]
            for _char_idx, sentence in segment_text(chunk_text):
                # for each sentence, yield text, filename, and sentence index
                # with any other metadata included in chunk_info

                # character index is not included in output,
                # but may be useful for sub-chunk metadata (e.g., line number)
                # NOTE: we don't allow overriding filename, since it must
                # be unique per input to consolidate quotes correctly
                yield (
                    chunk_info
                    | {
                        "file": self.file_name,
                        "text": sentence,
                        "sent_index": sentence_index,
                        "sent_id": f"{self.file_name}:{sentence_index}",
                    }
                    # Include any extra metadata (subclass specific)
                    | self.get_extra_metadata(chunk_info, _char_idx, sentence)
                )

                # increment sentence index
                sentence_index += 1

    @classmethod
    def subclasses(cls) -> list[type[Self]]:
        """
        List of available file input classes.
        """
        return cls.__subclasses__()

    @classmethod
    def subclass_by_type(cls) -> dict[str, type[Self]]:
        """
        Dictionary of subclass by supported file extension for available
        input classes.
        """
        return {subcls.file_type: subcls for subcls in cls.subclasses()}

    @classmethod
    def supported_types(cls) -> list[str]:
        """
        Unique list of supported file extensions for available input classes.
        """
        return list({subcls.file_type for subcls in cls.subclasses()})

    @classmethod
    def create(
        cls, input_file: pathlib.Path, filename_override: str | None = None
    ) -> Self:
        """
        Instantiate and return the appropriate input class for the specified
        input file.  Takes an optional filename override parameter,
        which is passed through to the input class.

        :raises ValueError: if input_file is not a supported type
        """
        input_cls = cls.subclass_by_type().get(input_file.suffix.lower())
        # for now, check based on file extension
        # NOTE: this will change when we add support for METS-ALTO
        if input_cls is None:
            # include supported types in error to aid debugging
            # sort so display order is reliable
            supported_types = ", ".join(sorted(cls.supported_types()))
            raise ValueError(
                f"{input_file.suffix} is not a supported input type (must be one of {supported_types})"
            )
        return input_cls(input_file=input_file, filename_override=filename_override)


class SectionType(StrEnum):
    """Section types declaration, for distinguishing different text sections within corpus documents."""

    TEXT = "text"
    """Body text content from the document."""

    FOOTNOTE = "footnote"
    """Footnote content extracted from the document."""
