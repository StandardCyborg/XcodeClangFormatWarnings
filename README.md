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


