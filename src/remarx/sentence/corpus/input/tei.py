"""
Functionality related to TEI XML input content for sentence corpora
"""

import pathlib
import re
from collections import namedtuple
from collections.abc import Generator
from dataclasses import dataclass, field
from typing import ClassVar, Self

from neuxml import xmlmap

from remarx.sentence.corpus.input.base import TextInput

# requirements:
# takes one input file
# yields text content in chunks
# combines sentences with metadata;


TEI_NAMESPACE = "http://www.tei-c.org/ns/1.0"

# namespaced tags look like {http://www.tei-c.org/ns/1.0}tagname
# create a named tuple of short tag name -> namespaced tag name
_tei_tags = ["pb", "lb", "note", "add", "label", "ref", "div3"]
TagNames = namedtuple("TagNames", _tei_tags)
TEI_TAG = TagNames(**{tag: f"{{{TEI_NAMESPACE}}}{tag}" for tag in _tei_tags})


class BaseTEIXmlObject(xmlmap.XmlObject):
    """
    Base class for TEI xml objects with TEI namespace included in root namespaces,
    for use in xpath expressions
    """

    ROOT_NAMESPACES: ClassVar[dict[str, str]] = {"t": TEI_NAMESPACE}


class TEIPage(BaseTEIXmlObject):
    """
    Custom :class:`eulxml.xmlmap.XmlObject` instance for a page
    of content within a TEI XML document.
    """

    number = xmlmap.StringField("@n")
    edition = xmlmap.StringField("@ed")
    next_page_number = xmlmap.StringField("following::t:pb[1]/@n")

    # page beginning tags delimit content instead of containing it;
    # use following axis to find all text nodes following this page beginning
    text_nodes = xmlmap.StringListField("following::text()")

    def text_contents(self) -> Generator[str]:
        """
        Generator of text content on this page, between the current
        and following page begin tags.
        """
        # for now, ignore partial content, footnotes, hyphenation, etc
        for text in self.text_nodes:
            parent = text.getparent()
            # stop iterating when we hit the next page break;
            if (
                parent != self.node
                and parent.tag == TEI_TAG.pb
                # ignore alternate edition page breaks (MEGA specific)
                and parent.get("ed") is None
            ):
                # TODO move to docstring
                # mega-specific: there are two sets of page numbers, we want
                # the main pagination, not the editorial manuscript pagination
                break

            # omit editorial content (e.g. original page numbers)
            if (
                parent.tag == TEI_TAG.add
                or (parent.tag == TEI_TAG.label and parent.get("type") == "mpb")
            ) and (text.is_text or (text.is_tail and text.strip() == "")):
                # omit if text is inside an editorial tag (is_text)
                # OR if text comes immediately after (is_tail) and is whitespace only
                continue

            # consolidate whitespace if it includes a newline
            # (i.e., space between indented tags in the XML)
            yield re.sub(r"\s*\n\s*", "\n", text)

    def __str__(self) -> str:
        """
        Page text contents as a string
        """
        return "".join(self.text_contents())


class TEIDocument(BaseTEIXmlObject):
    """
    Custom :class:`eulxml.xmlmap.XmlObject` instance for TEI XML document.
    """

    #: list of page objects, identified by standard (non-editorial) page begin tag (pb)
    pages = xmlmap.NodeListField("..//t:text//t:pb", TEIPage)

    @classmethod
    def init_from_file(cls, path: pathlib.Path) -> Self:
        """
        Class method to initialize a new :class:`TEIDocument` from a file.
        """
        # TODO: handle parse error etc
        return xmlmap.load_xmlobject_from_file(path, cls)


@dataclass
class TEIinput(TextInput):
    """
    Input class for TEI/XML content.
    """

    # inherit filename as file id for now
    # (is there any id in the file we should use instead?)

    #: parsed xml document; initialized from inherited input_file
    xml_doc: TEIDocument = field(init=False)

    def __post_init__(self) -> None:
        """
        After default initialization, parse :attr:`input_file` as
        a :class:`TEIDocument` and store on :attr:`xml_doc`.
        """
        # parse the input file as xml and save the result
        self.xml_doc = TEIDocument.init_from_file(self.input_file)

    def get_text_chunks(self) -> Generator[str]:
        """
        Get document content page by page.
        """
        # get body text content chunked by page
        for page in self.xml_doc.pages:
            if page.edition != "manuscript":
                # maybe yield tuple of page metadata + page text?

                yield (str(page))
