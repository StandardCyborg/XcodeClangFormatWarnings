#!/usr/bin/env python3

import os
import subprocess
import sys
import xml.etree.ElementTree as ElementTree

SUPPORTED_FILE_EXTENSIONS = [".h", ".hpp", ".c", ".cpp", ".m", ".mm"]

def run_clang_format(directory):
    modified_files = get_git_modified_files()
    
    for file in modified_files:
        absolute_path = os.path.join(os.getcwd(), file)
        _, extension = os.path.splitext(file)
        if extension in SUPPORTED_FILE_EXTENSIONS:
            run_clang_format_on_file(absolute_path)
    
    # Recursively walk the directory and run for all supported files
    # for root, subdirectories, files in os.walk(directory):
    #     for filename in files:
    #         name, extension = os.path.splitext(filename)
    #         if extension in SUPPORTED_FILE_EXTENSIONS:
    #             run_clang_format_on_file(os.path.join(root, filename))


def run_clang_format_on_file(absolute_filename):
    args = ["clang-format", "-output-replacements-xml", "-style=WebKit", absolute_filename]
    process_result = subprocess.run(args, stdout=subprocess.PIPE)
    
    replacements_xml_tree = ElementTree.fromstring(process_result.stdout)
    
    file_string = ""
    with open(absolute_filename, 'r', encoding="utf-8") as file:
        file_string = file.read()
    
    for replacement in replacements_xml_tree:
        replacement_offset = int(replacement.attrib["offset"])
        replacement_length = int(replacement.attrib["length"])
        replacement_line_number, replacement_column = line_number_from_offset(file_string, replacement_offset)
        replacement_text = replacement.text or ""
        
        # Special rule: avoid trimming trailing whitespace from empty lines
        # http://clang-developers.42468.n3.nabble.com/clang-format-leading-whitespace-td4058643.html
        if replacement_text.startswith("\n\n    ") and file_string[replacement_offset-1] == '\n':
            continue
        
        # Make the replacement text easier to read
        replacement_text = replacement_text.replace("\n", "\\n")
        
        warning_header = "{}:{}:{}: warning: Style nit at col {}: ".format(
            absolute_filename,
            replacement_line_number,
            replacement_column,
            replacement_column
        )
        
        warning_message = build_warning_message(replacement_text, replacement_length, replacement_offset, file_string)
        
        print(warning_header + warning_message)


def line_number_from_offset(file_string, offset):
    line_number = 1
    column = 0
    
    for i in range(offset):
        if file_string[i] == '\n':
            line_number += 1
            column = 0
        else:
            column += 1
    
    return line_number, column

def build_warning_message(replacement_text, replacement_length, replacement_offset, file_string):
    if not replacement_text:
        if replacement_length == 1:
            return "remove space" if file_string[replacement_offset-1] == ' ' else "remove character"
        else:
            return "remove next {} chars".format(replacement_length)
    else:
        if replacement_length == 0:
            return "add space" if replacement_text == ' ' else "add \"{}\"".format(replacement_text)
        elif replacement_length == 1:
            return "replace char with \"{}\"".format(replacement_text)
        elif replacement_length == 2 and replacement_text == ' ': # Not necessarily accurate, but most likely
            return "remove a space"
        else:
            return "replace next {} chars with \"{}\"".format(replacement_length, replacement_text)


def get_git_modified_files():
    result = []
    
    status_text = subprocess.check_output("git status --short", encoding="UTF-8", shell=True)
    
    for line in status_text.splitlines():
        if line.startswith("A") or line.startswith(" M ") or line.startswith("??"):
            result.append(line[3:])
    
    return result        


if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = sys.argv[1]
        # Turn into an absolute path if needed
        if not path.startswith("/"):
            path = os.path.join(os.getcwd(), path)
    else:
        path = os.getcwd()
    
    run_clang_format(path)