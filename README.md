# crashplan_tools
Tools related to using Code42 CrashPlan

## `scripts/CheckExcludes.py`
Searches a directory tree for files or folders that would be excluded from the new (Oct 2021) CrashPlan backup, outputing resultant list to STDOUT.

The exclusion rules are built into the script but can be overridden with an external file. The file `data/exclusions_new.txt` contains the new global exclusion rules and matches the built-in list. `data/exclusions_8.2.txt` contains the previous global exclusion rules.

## Examples
```
CheckExclusions.py . output.txt
```
recursively searches the current folder for files or folders that would be excluded by the default rules, writing results to `output.txt`. 

```
CheckExclusions.py --csv -x ../data/exclusions_8.2.txt plugh ouput.csv 
```
Matches pathnames against exclusion rules defined in `../data/exclusions_8.2.txt`. If `plugh` is a file, looks to see if that file would be excluded. If `plugh` is a folder, recursively searches it for files or folders that would be excluded. Writes the resut, in CSV format, to `outfile.csv`

## Usage

```
usage: CheckExclusions.py [-h] [-x EXCLUSIONS] [--csv] folder outfile

Searches a directory tree for files or folders that would be excluded
from the new (Oct 2021) CrashPlan backup. 

positional arguments:
  folder                File folder to search
  outfile               Name of output file

optional arguments:
  -h, --help            show this help message and exit
  -x EXCLUSIONS, --exclusions EXCLUSIONS
                        Optional path to input file containing exclusion rules
  --csv                 format output as CSV
```

Notes:

This tool is not aware of file selection settings for any particular back sets.
For example your backup set might not include %APPDATA% but this program doesn't
know that so will gladly look down through %APPDATA% for files that match the
global exclusion patterns.'

Exclusions are platform-dependent: the exclusions used are the ones applicable
to the platform on which the script is running. See comments in sample exclusion
files for details.

When traversing the designated directory tree, symlinks are not followed.

By default, output is a series of lines of the following form:
```
X lineno: pathname [s,e] = "match"
```
where 
- lineno is the line number within the exclusion rules that the pathname matched.
- pathname identifies a file or folder that would be excluded
- [s,e] are the start and end positions of the substring that matched
- "match" is the substring that matched

When `--csv` is supplied, output is in CSV format of the following form:
```
lineno,pathname,s,e,match
```
