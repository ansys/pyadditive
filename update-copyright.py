# (c) 2022 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
import argparse
import codecs
from datetime import date
import glob
import os
import tempfile

copyright_substr = "ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited."


def get_args():
    parser = argparse.ArgumentParser(
        description="Update copyright in python files or add copyright if it is missing."
    )
    parser.add_argument("directory", help="root directory of project")
    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()
    source_files = glob.glob(os.path.join(args.directory, "**", "*.py"), recursive=True)
    for f in source_files:
        lines = []
        with open(f, "r") as file:
            lines = file.readlines()
            if copyright_substr in lines[0]:
                del lines[0]
            lines[0] = lines[0].strip(codecs.BOM_UTF8.decode(file.encoding))

        tmp_name = ""
        with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
            tmp.write("# (c) {} ".format(date.today().year) + copyright_substr + "\n")
            tmp.writelines(lines)
            tmp_name = tmp.name

        os.replace(tmp_name, f)
