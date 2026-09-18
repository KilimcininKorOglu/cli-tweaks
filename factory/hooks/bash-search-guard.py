#!/usr/bin/env python3
"""
Droid PreToolUse hook for Bash: blocks a shell search that reads files and
points at the ripwire MCP instead.

The target is codebase search, not stream filtering. `grep -rn foo .` and
`sed -n '1,20p' file.go` read files, so they are blocked; `go version | grep gopls`
filters another command's stdout, which ripwire cannot do, so it is allowed. The
rule is the file operand, never the tool name alone. Option values such as the
`3` of `grep -A 3` are skipped, so they are never taken for a file operand.

A command substitution is checked as its own command, also inside double
quotes, and a search run through `xargs` reads the files xargs passes to it.

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
FILE_CMDS = GREP_CMDS | SED_CMDS | WALKER_CMDS | READER_CMDS

# Options that take the next token as their value.
GREP_VALUE_OPTS = {
    "e", "f", "A", "B", "C", "m", "d", "D",
    "regexp", "file", "after-context", "before-context", "context", "max-count",
    "directories", "devices", "include", "exclude", "exclude-dir", "exclude-from",
    "label", "binary-files", "group-separator",
}
WALKER_VALUE_OPTS = {
    "e", "f", "A", "B", "C", "m", "g", "G", "t", "T", "M", "j", "r", "E", "d",
    "regexp", "file", "after-context", "before-context", "context", "max-count",
    "glob", "iglob", "type", "type-not", "type-add", "type-clear", "max-columns",
    "threads", "replace", "encoding", "max-depth", "max-filesize", "sort", "sortr",
    "path-separator", "pre", "pre-glob", "context-separator", "colors", "engine",
    "field-context-separator", "field-match-separator", "ignore-file",
    "file-search-regex", "ignore", "ignore-dir",
}
XARGS_VALUE_OPTS = {"a", "d", "E", "I", "L", "n", "P", "s"}
GIT_VALUE_OPTS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}

# Prefixes that carry another command as their argument.
WRAPPERS = {"sudo", "command", "env", "time", "nice", "nohup", "builtin", "exec", "xargs"}

OPERATORS = {"|", "||", "&&", ";", ";;", "&", "(", ")", "{", "}", "!", "\n"}
OPERATOR_CHARS = set("|&;()")
OPERATOR_RUN = re.compile(r"\|\||&&|;;|[|&;()]")

ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
HEREDOC = re.compile(r"<<-?\s*[\"']?([A-Za-z_][A-Za-z0-9_]*)[\"']?")
BACKTICK = re.compile(r"`([^`]*)`")

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
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError, OSError):
        return True
    if not isinstance(data, dict) or SETTINGS_KEY not in data:
        return True
    value = data.get(SETTINGS_KEY)
    if value is True or value is False:
        return value
    print(
        f"bash-search-guard: {SETTINGS_KEY} must be true or false, got {value!r}; guard stays on",
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


def blankSingleQuoted(command):
    """Return the command with single-quoted text blanked, because the shell
    expands no command substitution inside it."""
    out = []
    quote = ""
    escaped = False
    for char in command:
        if quote == "'":
            quote = "" if char == "'" else quote
            out.append(char if char == "'" else " ")
            continue
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == '"':
            quote = "" if quote == '"' else '"'
        elif char == "'" and not quote:
            quote = "'"
        out.append(char)
    return "".join(out)


def closingParen(text, start):
    """Return the index of the `)` that closes a `$(` whose body starts here."""
    depth = 1
    for index in range(start, len(text)):
        depth += {"(": 1, ")": -1}.get(text[index], 0)
        if depth == 0:
            return index
    return len(text)


def substitutions(command):
    """Return the inner commands of every `$(...)` and backtick pair, also
    inside double quotes."""
    text = blankSingleQuoted(command)
    inner = [match.group(1) for match in BACKTICK.finditer(text)]
    start = text.find("$(")
    while start != -1:
        inner.append(text[start + 2:closingParen(text, start + 2)])
        start = text.find("$(", start + 2)
    return inner


def splitOperators(tokens):
    """Split a run of operator characters that shlex returns as one token.

    shlex joins adjacent punctuation, so `$(cmd); next` yields `);`, which is
    no operator; without the split, `next` would read as an argument of `cmd`.
    """
    out = []
    for token in tokens:
        if token and token not in OPERATORS and set(token) <= OPERATOR_CHARS:
            out.extend(OPERATOR_RUN.findall(token))
        else:
            out.append(token)
    return out


def tokenize(command):
    """Return shell tokens with operators separated, or None when unparseable."""
    # Expose command-substitution boundaries so the inner command is seen.
    normalized = splitStatements(command).replace("$(", " ( ").replace("`", " ( ")
    lexer = shlex.shlex(normalized, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        return splitOperators(list(lexer))
    except ValueError:
        return None


def skipOptions(words, index, valueOpts):
    """Return the index of the first word after a wrapper's own options."""
    while index < len(words) and words[index].startswith("-") and len(words[index]) > 1:
        consumes = classifyOption(words[index], valueOpts, set())[1]
        index += 2 if consumes else 1
    return index


def commandStart(words):
    """Return (index of the real command, whether it runs under xargs)."""
    index = 0
    viaXargs = False
    while index < len(words):
        word = words[index]
        name = os.path.basename(word)
        if not ASSIGNMENT.match(word) and name not in WRAPPERS:
            break
        index += 1
        if name == "xargs":
            viaXargs = True
            index = skipOptions(words, index, XARGS_VALUE_OPTS)
    return index, viaXargs


def segments(tokens):
    """Split tokens into (pipedIn, pipedOut, viaXargs, command, args), one per shell command."""
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
        index, viaXargs = commandStart(words)
        if index >= len(words):
            continue
        parsed.append(
            (wasPiped, terminator == "|", viaXargs, os.path.basename(words[index]), words[index + 1:])
        )
    return parsed


def classifyOption(arg, valueOpts, flagHits):
    """Return (isValueOption, consumesNextToken, hitsFlag) for one option token.

    In a short option cluster the first value letter ends the cluster: its
    value is the rest of the token, or the next token when the letter is last.
    """
    if arg.startswith("--"):
        name = arg[2:].split("=")[0]
        isValue = name in valueOpts
        return isValue, isValue and "=" not in arg, name in flagHits
    letters = arg[1:]
    for index, letter in enumerate(letters):
        if letter in valueOpts:
            hits = any(flag in flagHits for flag in letters[:index])
            return True, index == len(letters) - 1, hits
    return False, False, any(letter in flagHits for letter in letters)


def splitOperands(args, valueOpts, flagHits):
    """Return (operands, sawPatternOpt, hitFlag) for a getopt-style argument list.

    sawPatternOpt is True when -e or -f (or their long forms) supplied the
    pattern, so the first operand is a file rather than the pattern.
    """
    operands = []
    sawPatternOpt = False
    hitFlag = False
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--":
            operands.extend(args[index + 1:])
            break
        if arg.startswith("-") and len(arg) > 1:
            isValue, consumes, hits = classifyOption(arg, valueOpts, flagHits)
            sawPatternOpt = sawPatternOpt or (isValue and isPatternOption(arg))
            hitFlag = hitFlag or hits
            index += 2 if consumes else 1
            continue
        operands.append(arg)
        index += 1
    return operands, sawPatternOpt, hitFlag


def isPatternOption(arg):
    """True when this option supplies the pattern or script instead of an operand."""
    if arg.startswith("--"):
        return arg[2:].split("=")[0] in {"regexp", "file", "expression"}
    return any(letter in "ef" for letter in arg[1:])


def grepReadsFiles(args):
    """grep [opts] PATTERN [FILE...] — a file operand or -r means it reads files."""
    operands, sawPatternOpt, recursive = splitOperands(
        args,
        valueOpts=GREP_VALUE_OPTS,
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
    operands, sawPatternOpt, _ = splitOperands(args, WALKER_VALUE_OPTS, set())
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


def gitSubcommand(args):
    """Return the git subcommand, skipping git's own options and their values."""
    index = 0
    while index < len(args) and args[index].startswith("-"):
        index += 2 if args[index] in GIT_VALUE_OPTS else 1
    return args[index] if index < len(args) else ""


def searchVerdict(pipedIn, command, args):
    """Return the reason a search command must be blocked, else ''."""
    if command == "git" and gitSubcommand(args) == "grep":
        return "`git grep` searches the repository"
    if command in GREP_CMDS and grepReadsFiles(args):
        return f"`{command}` reads files here"
    if command in SED_CMDS and sedReadsFiles(args):
        return f"`{command}` reads or rewrites files here"
    if command in WALKER_CMDS and walkerReadsFiles(args, pipedIn):
        return f"`{command}` walks the working directory"
    return ""


def verdict(segment):
    """Return the reason string when this command must be blocked, else ''."""
    pipedIn, pipedOut, viaXargs, command, args = segment
    if viaXargs and command in FILE_CMDS:
        return f"`xargs {command}` reads the files xargs passes to it"
    reason = searchVerdict(pipedIn, command, args)
    if reason:
        return reason
    if command in READER_CMDS and readerPrintsFile(args, pipedOut):
        return f"`{command}` prints a file, which is the Read tool's job"
    return ""


def collectReasons(command):
    """Return every distinct reason this Bash command must be blocked."""
    stripped = stripHeredocs(command)
    reasons = []
    for text in [stripped] + substitutions(stripped):
        tokens = tokenize(text)
        if tokens is None:
            continue
        for segment in segments(tokens):
            reason = verdict(segment)
            if reason and reason not in reasons:
                reasons.append(reason)
    return reasons


def main():
    try:
        inputData = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return 0
    if not isinstance(inputData, dict) or inputData.get("tool_name") != "Bash":
        return 0

    settingsFile = Path.home() / ".factory" / "settings.json"
    if not isEnabled(settingsFile):
        return 0

    toolInput = inputData.get("tool_input", {})
    command = toolInput.get("command", "") if isinstance(toolInput, dict) else ""
    if not isinstance(command, str) or not command.strip():
        return 0

    reasons = collectReasons(command)
    if not reasons:
        return 0

    print(
        "BLOCKED by bash-search-guard: {}.\n\n{}".format("; ".join(reasons), GUIDANCE),
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
