#!/usr/bin/env python3

import os
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ElementTree

SUPPORTED_FILE_EXTENSIONS = [".h", ".hpp", ".c", ".cpp", ".m", ".mm"]

def find_clang_format_file(directory):
    if os.path.exists(os.path.join(directory, ".clang-format")):
        return directory
    
    if Path(directory).parent == Path(directory):
        return None
    
    # Keep searching up a level
    return find_clang_format_file(Path(directory).parent)


def run_clang_format(directory, should_apply_fixes):
    if not shutil.which("clang-format"):
        print("Error: clang-format is not installed. Please install clang-format, such as by using HomeBrew:\nbrew install clang-format")
        exit(-1)
    
    if not find_clang_format_file(directory):
        print("Error: No .clang-format file found. Please generate one, such as by using the following command:\nclang-format -style=llvm -dump-config > .clang-format\n")
        exit(-1)
    
    git_modified_files = get_git_modified_files()
    modified_files_in_directory = [filename for filename in git_modified_files if os.path.basename(directory) in filename]
        
    for file in modified_files_in_directory:
        absolute_path = os.path.join(os.getcwd(), file)
        _, extension = os.path.splitext(file)
        if extension in SUPPORTED_FILE_EXTENSIONS:
            if should_apply_fixes:
                apply_clang_format_fixes_on_file(absolute_path)
            else:
                run_clang_format_on_file(absolute_path)
    
    # Recursively walk the directory and run for all supported files
    # for root, subdirectories, files in os.walk(directory):
    #     for filename in files:
    #         name, extension = os.path.splitext(filename)
    #         if extension in SUPPORTED_FILE_EXTENSIONS:
    #             run_clang_format_on_file(os.path.join(root, filename))

def apply_clang_format_fixes_on_file(absolute_filename):
    args = ["clang-format", "-style=file", absolute_filename]
    process_result = subprocess.run(args, stdout=subprocess.PIPE)
    
    if process_result.stderr:
        print("Error applying fixes to {}: {}".format(absolute_filename, process_result.stderr))
    else:
        print("Applying fixes to {}".format(absolute_filename))
        stdout_as_string = process_result.stdout.decode("utf-8")
        
        with open(absolute_filename, 'w') as file:
            file.write(stdout_as_string)


def run_clang_format_on_file(absolute_filename):
    args = ["clang-format", "-output-replacements-xml", "-style=file", absolute_filename]
    process_result = subprocess.run(args, stdout=subprocess.PIPE)
    
    replacements_xml_tree = ElementTree.fromstring(process_result.stdout)
    
    file_string = ""
    with open(absolute_filename, 'r', encoding="utf-8") as file:
        file_string = file.read()
    
    for replacement in replacements_xml_tree:
        replacement_offset_bytes = int(replacement.attrib["offset"])
        replacement_length = int(replacement.attrib["length"])
        replacement_line_number, replacement_column, replacement_offset = line_number_from_offset(file_string, replacement_offset_bytes)
        replacement_text = replacement.text or ""
        original_text = file_string[replacement_offset:replacement_offset+replacement_length]
        
        if should_ignore_replacement(original_text, replacement_text):
            continue
        
        # Make the replacement text easier to read
        replacement_text = replacement_text.replace("\n", "\\n")
        
        warning_header = "{}:{}:{}: warning: Style nit @ col {}: ".format(
            absolute_filename,
            replacement_line_number,
            replacement_column,
            replacement_column
        )
        
        warning_message = build_warning_message(replacement_text, replacement_length, replacement_offset, file_string)
        
        warning_message_details = build_warning_message_details(replacement_text, replacement_length, replacement_offset, file_string)
        
        print(warning_header + warning_message + warning_message_details)


def should_ignore_replacement(original_text, replacement_text):
    # Special rule: avoid trimming trailing whitespace from empty lines
    # http://clang-developers.42468.n3.nabble.com/clang-format-leading-whitespace-td4058643.html
    if original_text.startswith("\n    ") and replacement_text.startswith("\n\n"):
        return True
    
    return False


def line_number_from_offset(file_string, byte_offset):
    line_number = 1
    column = 0
    i = 0
    # clang-format uses bytes, not characters, as offsets and lengths, so we'll
    # keep track of the difference here
    character_offset = byte_offset
    
    while i < character_offset:
        character = file_string[i]
        character_byte_count = len(bytes(character, 'utf8'))
        
        if character == '\n':
            line_number += 1
            column = 0
        else:
            column += 1
        
        character_offset -= character_byte_count - 1
        i += 1
    
    return line_number, column, character_offset


def build_warning_message(replacement_text, replacement_length, replacement_offset, file_string):
    if not replacement_text:
        if replacement_length == 1:
            return "remove space" if file_string[replacement_offset] == ' ' else "remove character"
        else:
            return "remove next {} chars".format(replacement_length)
    else:
        if replacement_length == 0:
            return "add space" if replacement_text == ' ' else "add \"{}\"".format(replacement_text)
        elif replacement_length == 1:
            return "replace {} with \"{}\"".format("newline" if file_string[replacement_offset] == '\n' else  "char", replacement_text)
        elif replacement_length == 2 and replacement_text == ' ': # Not necessarily accurate, but most likely
            return "remove a space"
        elif file_string[replacement_offset] == "\n" and replacement_length == 1:
            return "remove a newline"
        elif replacement_text.find("#include") != -1 and replacement_length > len("#include "):
            return "alphabetize headers"
        else:
            return "replace next {} chars with \"{}\"".format(replacement_length, replacement_text)

def build_warning_message_details(replacement_text, replacement_length, replacement_offset, file_string):
    surrounding_character_count = 15
    surrounding_text_start = max(0, replacement_offset - surrounding_character_count)
    surrounding_text_end = min(len(file_string), replacement_offset + surrounding_character_count)
    
    surrounding_text_with_replacement = \
        file_string[surrounding_text_start:replacement_offset] + \
        replacement_text + \
        file_string[replacement_offset+replacement_length:surrounding_text_end+replacement_length]
    
    return "  ➡️  …" + surrounding_text_with_replacement.replace("\n", "\\n")

def get_git_modified_files():
    result = []
    
    status_text = subprocess.check_output("git status --short", encoding="UTF-8", shell=True)
    
    for line in status_text.splitlines():
        if line.startswith("A  ") or line.startswith("AM ") or line.startswith("M  ") or line.startswith(" M ") or line.startswith("MM ") or line.startswith("?? "):
            result.append(line[3:])
    
    return result        


if __name__ == "__main__":
    should_apply_fixes = False
    path_argument_index = 1
    
    if "--apply-fixes" in sys.argv:
        should_apply_fixes = True
        path_argument_index += 1
    
    if len(sys.argv) > path_argument_index:
        path = sys.argv[path_argument_index]
        # Turn into an absolute path if needed
        if not path.startswith("/"):
            path = os.path.join(os.getcwd(), path)
    else:
        path = os.getcwd()
    
    run_clang_format(path, should_apply_fixes)

