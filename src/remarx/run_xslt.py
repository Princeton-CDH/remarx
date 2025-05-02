import argparse
import pathlib
import sys

from saxonche import PySaxonProcessor


def main():
    parser = argparse.ArgumentParser(
        description="Transform an XML file with XSLT",
    )
    parser.add_argument(
        "xml_file",
        type=pathlib.Path,
        help="Path to XML file to be transformed",
    )
    parser.add_argument(
        "xsl_file",
        type=pathlib.Path,
        help="Path to XSL file to apply",
    )
    parser.add_argument(
        "output",
        help="Filename where the transformed output should be saved",
        type=pathlib.Path,
    )
    args = parser.parse_args()

    # Check input paths exist when they should and don't when they shouldn't
    if not args.xml_file.is_file():
        print(f"Error: XML file {args.xml_file} does not exist", file=sys.stderr)
        sys.exit(1)
    if not args.xsl_file.is_file():
        print(f"Error: XSL file {args.xml_file} does not exist", file=sys.stderr)
        sys.exit(1)
    if args.output.is_file():
        print(
            f"Error: output file {args.output} exists. Will not overwrite.",
            file=sys.stderr,
        )
        sys.exit(1)

    with PySaxonProcessor(license=False) as proc:
        xsltproc = proc.new_xslt30_processor()
        document = proc.parse_xml(xml_file_name=str(args.xml_file))
        executable = xsltproc.compile_stylesheet(stylesheet_file=str(args.xsl_file))
        output = executable.transform_to_string(xdm_node=document)
        with open(args.output, "w") as outfile:
            outfile.write(output)


if __name__ == "__main__":
    main()
