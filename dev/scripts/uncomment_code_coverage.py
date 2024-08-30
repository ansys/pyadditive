# This script is meant to be run from repo root, e.g. pre-commit
code_coverage_search_string = "addopts ="

with open("pyproject.toml", "r") as f:
    filedata = f.read()

if (
    filedata.find("#" + code_coverage_search_string) == -1
    and filedata.find("# " + code_coverage_search_string) == -1
):
    exit(0)

filedata = filedata.replace("#" + code_coverage_search_string, code_coverage_search_string)
filedata = filedata.replace("# " + code_coverage_search_string, code_coverage_search_string)

with open("pyproject.toml", "w") as f:
    f.write(filedata)

exit(1)
