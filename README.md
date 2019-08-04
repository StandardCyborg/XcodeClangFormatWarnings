# XcodeClangFormatWarnings
Displays clang-format's suggested changes as warning messages within Xcode

## Integration
- Clone this repository to a well-known location for your team or to within your project directory
- In Xcode, select your Xcode project from the project navigator
- Under Build Phases, click +, then choose New Run Script Phase
- Set the contents of the script to the following:
```
python3 /path/to/run-clang-format.py
```
- You may move this phase to any order within the list, but right before Compile Sources is often best
- Build your project!

## Disabling formatting for specific code
See https://clang.llvm.org/docs/ClangFormatStyleOptions.html#disabling-formatting-on-a-piece-of-code
tl;dr: clang-format will read the below comments to turn off formatting for a specific block of code.
```
int formatted_code;
// clang-format off
    void    unformatted_code  ;
// clang-format on
void formatted_code_again;
```

## Helpful Links
- https://clang.llvm.org/docs/ClangFormat.html
- https://clang.llvm.org/docs/ClangFormatStyleOptions.html
- https://zed0.co.uk/clang-format-configurator
- https://github.com/travisjeffery/ClangFormat-Xcode

