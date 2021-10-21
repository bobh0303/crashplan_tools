# crashplan_tools
Tools related to using Code42 CrashPlan

## `scripts/CheckExcludes.py`
Searches a directory tree for files or folders that would be excluded from the new (Oct 2021) CrashPlan backup, outputing resultant list to STDOUT.

The exclusion rules are built into the script but can be overridden with an external file. The file `data/exclusions_new.txt` contains the new global exclusion rules and matches the built-in list. `data/exclusions_8.2.txt` contains the previous global exclusion rules.

NB: This script does not following symlinks.

```
usage: CheckExclusions.py [-h] [-x EXCLUSIONS] folder

positional arguments:
  folder                File folder to search

optional arguments:
  -h, --help            show this help message and exit
  -x EXCLUSIONS, --exclusions EXCLUSIONS
                        Path to input file containing exclusion rules.
```

Output is a series of lines of the following form:
```
X lineno: pathname
```
where `lineno` is the line number within the exclusion rules that the pathname matched.
