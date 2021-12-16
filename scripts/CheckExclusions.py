#! /usr/bin/env python3
"""Scan a folder for files excluded by Code42 Global Exclusions"""

import re
import argparse
import sys
import os
import textwrap

# The following exclusion rules were in effect as of 2021-12-15
# To use alternate rules, format them as below in a text file and use the -x option to read them
ruleSource = (
'## Any:',
r'(?i)^.*(\.class|-journal|\.Win386\.SWP|PM_HIBER\.BIN|SAVE2DSK\.BIN|SYSTEM\.DAT|TOSHIBER\.DAT|Thumbs\.db|USER\.DAT|\.bck|\.bkf|\.cdt|\.hdd|\.hds|\.icloud|\.lrprev|\.manifest|\.mum|\.nib|\.nvram|\.ost|\.part|\.pvm|\.pvs|\.rbf|\.tibx?|\.tmp|\.upd|\.avhdx|\.vdi|\.vfd|\.vhd|\.vhdx|\.vmc|\.vmdk|\.vmem|\.vmsd|\.vmsn|\.vmss|\.vmtm|\.vmwarevm|\.vmx|\.vmxf|\.vsv|\.vud|\.xva|memory\.dmp|/Lightroom.*Previews\.lrdata|\.sparsebundle|\.sparseimage|/(cookies|permissions)\.sqlite(-.{3})?)$',
r'(?i)^.*(/Apple.*/Installer Cache/|/Cache/|/Cookies/|/Music/Subscription/|/Plex Media Server/|/Steam/|/Temp/|/\.dropbox\.cache/|/iPod Photo Cache/|/node_modules/|/tmp/|/tsm_images/|\.Trash|\.hdd/|\.pvm/|\.cprestoretmp|\.nvm|\.npm|/\.gradle/).*',
'',
'## Mac:',
r'^.*(\.DS_Store|\.strings)$',
r'(?i)^.*(\.imovielibrary/\.lock)$',
r'^/(Applications/|Desktop DB|Desktop DF|Network/|Previous Systems|System/|Users/.*/\.cisco/vpn/log/|Users/.*/\.dropbox/|\.DocumentRevisions-V100/|\.PKInstallSandboxManager-SystemSoftware|\.adobeTemp/|\.vol/|afs/|automount/|lost\+found/|net/).*',
r'(?i)^.*(/iTunes/Album Artwork/Cache/|/Network Trash Folder/|/Photos Library.*/Thumbnails/|/backups\.backupdb/|/iP.* Software Updates/|/iPhoto Library.*/Thumbnails/|/iPhoto Library/iPod Photo Cache|/migratedphotolibrary/Thumbnails/|\.imovielibrary/.*/Analysis Files/|\.imovielibrary/.*/Render Files/).*',
r'^.*(/Trash/|/\.fcpcache/|MobileBackups/|\.Spotlight-.*/|\.fseventsd|\.hotfiles\.btree|/bin/|/home/|/sbin/|/cores/|/private/|/var/).*',
r'(?i)^/(usr/|opt/|etc/|var/|Users/((?!XCode).)*/Applications/|Users/Shared/|dev/|Library/(?!($|Application Support/$|Application Support/CrashPlan/$|Application Support/CrashPlan/print_job_data/.*))|proc/|/Users/.*/.vscode/extensions/).*',
'',
'## Windows:',
r'(?i)^.:/(Config\.Msi|HIBERFIL\.SYS|HIBRN8\.DAT|autoexec\.bat|boot\.ini|bootmgr|bootnxt|bootsect\.bak|config\.sys|io\.sys|msdos\.sys|ntdetect\.com|ntldr|swapfile\.sys)$',
r'(?i)^.*(/I386|/System Volume Information/|/Temporary Internet Files/|/Windows Update Setup Files/|\$RECYCLE\.BIN/|/NTUSER|/Safari/Library/Caches/|/Windows Defender/|/cygwin(64)?/(bin|dev|etc|lib|sbin|tmp|var|usr)/|UsrClass\.dat).*',
r'^.*(/Local Settings/Temp|/Local.*/History/|/LocalService/|/MSOCache|/NetHood/|/NetworkService/).*',
r'(?i)^.*(/pagefile\.sys|\.etl|\.mui)$',
r'(?i)^.:/(Recovery/|boot/|ESD/|Recycler/|Dell/|Intel/|Oracle/|PerfLogs/|Program Files( \(x86\))?/|Users/All Users/|Users/[^/]+/Apple/MobileSync/|Windows(\.old)?/(?!$|fonts/.*)|\$WINDOWS.~(BT|WS)/|\$SysReset/|\$GetCurrent/|_RESTORE/|_SMSTaskSequence/|safeboot/|swsetup/).*',
'',
'## Linux:',
r'^/(cdrom/|dev/fd/|devices/|dvdrom/|initrd/|kernel/|lost\+found/|proc/|run/|selinux/|srv/|sys/|system/|var/(:?run|lock|spool|tmp|cache)/|proc/).*',
r'^/lib/modules/.*/volatile/\.mounted',
r'(?i)^/(usr/(?!($|local/$|local/crashplan/$|local/crashplan/print_job_data/.*))|opt/|etc/|dev/|home/[^/]+/\.config/google-chrome/|home/[^/]+/\.mozilla/|sbin/).*',
)

# The rule class records info for each exclusion rule read from the source
#   .lineno -- which line number of source
#   .flags -- accumulated regex compilation flags
#   .pattern -- original source pattern sans any leading `(?i)`
#   .regex -- compiled reg-ex

class rule:
    def __init__(self, pattern, lineno, flags=0):
        self.lineno = lineno
        self.flags = flags
        if pattern.startswith('(?i)'):
            self.pattern = pattern[4:]
            self.flags |= re.I
        else:
            self.pattern = pattern
        try:
            self.regex = re.compile(pattern,flags)
        except re.error as err:
            print(f'invalid RE at line {line} ignored: {err}', sys.stderr)
            raise ValueError


parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''\
        Searches a directory tree for files or folders that would be excluded 
        from the new (Oct 2021) CrashPlan backup.'''),
    epilog=textwrap.dedent('''\
        Notes:
            This tool is not aware of file selection settings for any particular back sets.
            For example your backup set might not include %APPDATA% but this program doesn't
            know that so will gladly look down through %APPDATA% for files that match the 
            global exclusion patterns.'    
             
            Exclusions are platform-dependent: the exclusions used are the ones applicable
            to the platform on which the script is running. See comments in sample exclusion 
            files for details.
             
            When traversing the designated directory tree, symlinks are not followed.
        ''')
)
parser.add_argument('folder', help='File folder to search')
parser.add_argument('-x', '--exclusions', help='Optional path to input file containing exclusion rules')
args = parser.parse_args()

# Use sys.platform to compute which platform's rules to use:
try:
    platform = {'linux':'Linux', 'darwin':'Mac', 'win32':'Windows'}[sys.platform]
except KeyError:
    sys.exit(f'current OS {sys.platform} is not supported by the script.')

# Read global exclusions file if provided, overwritting ruleSource
if args.exclusions:
    with open(args.exclusions, 'r') as f:
        ruleSource = f.readlines()

# Compile global exclusions
# States:
#   'init' = initial ... skipping "hidden files" (as code42 calls them) if present
#   'Any'  = processing platform-independent exclusion rules
#   'Mac', 'Windows', 'Linux' = processing platform-specific exclusion rules
# State transitions are triggered by comment lines containing "## Any", "## Mac", "## Linux", etc.
# We skip all rules in states other than 'All' and whichever platform were running on.
state = 'init'
stateRE = re.compile('## *(Any|Mac|Windows|Linux)', re.I)

# Iterate over rule source and create two lists of exclusion rules:
exclusionsCD = list()  # case-dependent pattern
exclusionsCI = list()  # case-independent patterns

for lineno,line in enumerate(ruleSource):
    line = line.rstrip('\r\n')
    if line == '':
        continue
    m = stateRE.match(line)
    if m:
        # State change
        state = m.group(1)
        continue
    if state not in ('Any', platform):
        # Ignore this input line
        continue

    try:
        r = rule(line, lineno+1)
    except ValueError:
        continue

    if r.flags & re.I:
        exclusionsCI.append(r)
    else:
        exclusionsCD.append(r)

# Keep a count of excluded files or folders
excludedCount = 0

def findLine(path):
    """search exclusion rules for the first that matches supplied path; return rule's line number or None"""
    global excludedCount
    for r in exclusionsCI + exclusionsCD:
        if r.regex.match(path):
            print(f'x line {r.lineno}: {path}')
            excludedCount += 1
            return r.lineno
    return None

# The following attempted optimization doesn't speed things up much and loses information 
# about line number so I'm not using it.

### from all the rules, construct 2 composite rules... one case-dependent and one case independent
##
##ciRE = re.compile(f'({"|".join([r.pattern for r in exclusionsCI])})', re.I)
##cdRE = re.compile(f'({"|".join([r.pattern for r in exclusionsCD])})')
##
##def isExcluded(path):
##    """ test path to see if it matches any exclusion rule"""
##    p = path.replace('\\','/') if platform == 'Windows' else path
##    if ciRE.match(p) is None and cdRE.match(p) is None:
##        return False
##    print(f'X: {path}')
##    return True

# NB: All the global exclusion regexes are written using forward-slash path separator, even for Windows.
# Therefore we change \ to / in the results of os.path.abspath() AND we don't use os.path.join() but
# rather simply use '/'.join() when joining path elements.

top = os.path.abspath(args.folder)
if platform == 'Windows':
    top = top.replace('\\', '/')

if os.path.islink(top):
    # We're not following links
    fileCount = dirCount = 0
else:
    fileCount = 1 if os.path.isfile(top) else 0
    dirCount = 1 if os.path.isdir(top) else 0

    if not(findLine(top) or os.path.isfile(top)):
        for dirpath, dirs, files in os.walk(top):
            if platform == 'Windows':
                dirpath = dirpath.replace('\\', '/')
            fileCount += len(files)
            dirCount += len(dirs)
            for f in files:
                findLine('/'.join((dirpath, f)))
            # For directory entries, be sure to include a trailing slash
            dirs[:] = [d for d in dirs if not findLine('/'.join((dirpath, d, '')))]

print(f'\nProcessed {fileCount} {"file" if fileCount==1 else "files"} and {dirCount} {"folder" if dirCount==1 else "folders"}; excluded {excludedCount}')