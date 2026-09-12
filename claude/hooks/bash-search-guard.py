#!/usr/bin/env python3
"""
Claude Code PreToolUse hook for Bash: blocks a shell search that reads files and
points at the ripwire MCP instead.

The target is codebase search, not stream filtering. `grep -rn foo .` and
`sed -n '1,20p' file.go` read files, so they are blocked; `go version | grep gopls`
filters another command's stdout, which ripwire cannot do, so it is allowed. The
rule is the file operand, never the tool name alone.

Exit code 2 with a message on stderr is the documented PreToolUse block path;
a JSON decision object is ignored there. Any parse failure exits 0, because a
guard that blocks on its own confusion is worse than the habit it corrects.
"""
import json
import os
import re
import shlex
import sys
from pathlib import Path

SETTINGS_KEY = "hookBlockBashSearch"

GREP_CMDS = {"grep", "egrep", "fgrep", "rgrep", "zgrep", "zegrep", "zfgrep", "ggrep"}
SED_CMDS = {"sed", "gsed"}
# These default to a recursive walk of the working directory when given no path.
WALKER_CMDS = {"rg", "ripgrep", "ack", "ack-grep", "ag"}
# These only print a file, which is the Read tool's job.
READER_CMDS = {"cat", "head", "tail", "nl", "more", "less", "bat"}

# Prefixes that carry another command as their argument.
WRAPPERS = {"sudo", "command", "env", "time", "nice", "nohup", "builtin", "exec", "xargs"}

OPERATORS = {"|", "||", "&&", ";", ";;", "&", "(", ")", "{", "}", "!", "\n"}

ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
HEREDOC = re.compile(r"<<-?\s*[\"']?([A-Za-z_][A-Za-z0-9_]*)[\"']?")

GUIDANCE = """Use the ripwire MCP for codebase search:
  literal text          -> ripwire grep (pattern=...)
  "where is X / how"    -> ripwire for (task=...) or find_symbol
  who calls X           -> ripwire find_referencing_symbols
  is it safe to change  -> ripwire impact plus ripwire uses
  read one symbol       -> ripwire fetch_body
  read a file or slice  -> the Read tool with offset/limit, never cat/head/sed
Filtering another command's output is still allowed, e.g. `cmd | grep x`, and so
are a redirect (`cat a b > c`) and a live follow (`tail -f app.log`)."""


def isEnabled(settingsFile):
    """Return True unless the settings file explicitly turns the guard off."""
    try:
        data = json.loads(settingsFile.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return True
    if not isinstance(data, dict) or SETTINGS_KEY not in data:
        return True
    value = data.get(SETTINGS_KEY)
    if value is True or value is False:
        return value
    print(
        "bash-search-guard: {} must be true or false, got {!r}; guard stays on".format(
            SETTINGS_KEY, value
        ),
        file=sys.stderr,
    )
    return True


def stripHeredocs(command):
    """Drop heredoc bodies so text written into a file cannot look like a command."""
    lines = command.splitlines()
    out = []
    index = 0
    while index < len(lines):
        line = lines[index]
        out.append(line)
        match = HEREDOC.search(line)
        index += 1
        if not match:
            continue
        delimiter = match.group(1)
        while index < len(lines) and lines[index].strip() != delimiter:
            index += 1
        index += 1  # skip the closing delimiter line
    return "\n".join(out)


def splitStatements(command):
    """Turn unquoted newlines into `;` so each line stays its own command.

    shlex treats a newline as whitespace, which would merge one line's command
    into the previous line's argument list and make a later `echo` look like a
    file operand of an earlier `grep`. Quoted newlines are left alone.
    """
    out = []
    quote = ""
    escaped = False
    for char in command:
        if escaped:
            out.append(char)
            escaped = False
            continue
        if char == "\\" and quote != "'":
            out.append(char)
            escaped = True
            continue
        if quote:
            out.append(char)
            if char == quote:
                quote = ""
            continue
        if char in "'\"":
            quote = char
            out.append(char)
            continue
        out.append(" ; " if char == "\n" else char)
    return "".join(out)


def tokenize(command):
    """Return shell tokens with operators separated, or None when unparseable."""
    # Expose command-substitution boundaries so the inner command is seen.
    normalized = splitStatements(command).replace("$(", " ( ").replace("`", " ( ")
    lexer = shlex.shlex(normalized, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        return list(lexer)
    except ValueError:
        return None


def segments(tokens):
    """Split tokens into (pipedIn, pipedOut, command, args), one per shell command."""
    result = []
    current = []
    pipedIn = False
    for token in tokens:
        if token in OPERATORS:
            if current:
                result.append((pipedIn, current, token))
            # The next command reads a stream only when this operator is a pipe.
            pipedIn = token == "|"
            current = []
            continue
        current.append(token)
    if current:
        result.append((pipedIn, current, ""))

    parsed = []
    for wasPiped, words, terminator in result:
        index = 0
        while index < len(words) and (
            ASSIGNMENT.match(words[index]) or os.path.basename(words[index]) in WRAPPERS
        ):
            index += 1
        if index >= len(words):
            continue
        parsed.append(
            (wasPiped, terminator == "|", os.path.basename(words[index]), words[index + 1:])
        )
    return parsed


def classifyOption(arg, valueOpts, flagHits):
    """Return (isValueOption, consumesNextToken, hitsFlag) for one option token."""
    if arg.startswith("--"):
        name = arg[2:].split("=")[0]
        isValue = name in valueOpts
        return isValue, isValue and "=" not in arg, name in flagHits
    letters = arg[1:]
    isValue = bool(letters) and letters[-1] in valueOpts
    return isValue, isValue, any(letter in flagHits for letter in letters)


def splitOperands(args, valueOpts, flagHits):
    """Return (operands, sawValueOpt, hitFlag) for a getopt-style argument list."""
    operands = []
    sawValueOpt = False
    hitFlag = False
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--":
            operands.extend(args[index + 1:])
            break
        if arg.startswith("-") and len(arg) > 1:
            isValue, consumes, hits = classifyOption(arg, valueOpts, flagHits)
            sawValueOpt = sawValueOpt or isValue
            hitFlag = hitFlag or hits
            index += 2 if consumes else 1
            continue
        operands.append(arg)
        index += 1
    return operands, sawValueOpt, hitFlag


def grepReadsFiles(args):
    """grep [opts] PATTERN [FILE...] — a file operand or -r means it reads files."""
    operands, sawPatternOpt, recursive = splitOperands(
        args,
        valueOpts={"e", "f", "regexp", "file"},
        flagHits={"r", "R", "recursive", "dereference-recursive"},
    )
    if recursive:
        return True
    # Without -e/-f the first operand is the pattern, so a file needs two.
    return len(operands) > (0 if sawPatternOpt else 1)


def sedReadsFiles(args):
    """sed [opts] SCRIPT [FILE...] — a file operand or -i means it touches files."""
    operands, sawScriptOpt, inPlace = splitOperands(
        args,
        valueOpts={"e", "f", "expression", "file"},
        flagHits={"i", "in-place"},
    )
    if inPlace:
        return True
    return len(operands) > (0 if sawScriptOpt else 1)


def walkerReadsFiles(args, pipedIn):
    """rg/ack/ag walk the working directory unless they are fed a stream."""
    operands, sawPatternOpt, _ = splitOperands(
        args, valueOpts={"e", "f", "regexp", "file"}, flagHits=set()
    )
    hasPath = len(operands) > (0 if sawPatternOpt else 1)
    return hasPath or not pipedIn


def readerPrintsFile(args, pipedOut):
    """cat/head/tail only substitute for the Read tool when they just print a file.

    Piping the output onward is data processing, and a redirect is a write, so
    neither is the Read tool's job. `tail -f` follows a live log, which Read
    cannot do at all.
    """
    if pipedOut:
        return False
    if any(">" in arg or "<" in arg for arg in args):
        return False
    operands, _, following = splitOperands(
        args, valueOpts={"n", "c", "lines", "bytes"}, flagHits={"f", "F", "follow"}
    )
    if following:
        return False
    return len(operands) > 0


def searchVerdict(pipedIn, command, args):
    """Return the reason a search command must be blocked, else ''."""
    if command == "git" and "grep" in args[:3]:
        return "`git grep` searches the repository"
    if command in GREP_CMDS and grepReadsFiles(args):
        return "`{}` reads files here".format(command)
    if command in SED_CMDS and sedReadsFiles(args):
        return "`{}` reads or rewrites files here".format(command)
    if command in WALKER_CMDS and walkerReadsFiles(args, pipedIn):
        return "`{}` walks the working directory".format(command)
    return ""


def verdict(pipedIn, pipedOut, command, args):
    """Return the reason string when this command must be blocked, else ''."""
    reason = searchVerdict(pipedIn, command, args)
    if reason:
        return reason
    if command in READER_CMDS and readerPrintsFile(args, pipedOut):
        return "`{}` prints a file, which is the Read tool's job".format(command)
    return ""


def collectReasons(command):
    """Return every distinct reason this Bash command must be blocked."""
    tokens = tokenize(stripHeredocs(command))
    if tokens is None:
        return []
    reasons = []
    for pipedIn, pipedOut, name, args in segments(tokens):
        reason = verdict(pipedIn, pipedOut, name, args)
        if reason and reason not in reasons:
            reasons.append(reason)
    return reasons


def main():
    try:
        inputData = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return 0
    if inputData.get("tool_name") != "Bash":
        return 0

    settingsFile = Path.home() / ".claude" / "settings.json"
    if not isEnabled(settingsFile):
        return 0

    command = inputData.get("tool_input", {}).get("command", "")
    if not isinstance(command, str) or not command.strip():
        return 0

    reasons = collectReasons(command)
    if not reasons:
        return 0

    print(
        "BLOCKED by bash-search-guard: {}.\n\n{}".format(
            "; ".join(reasons),
            GUIDANCE.format(key=SETTINGS_KEY, settings=settingsFile),
        ),
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
