import re

def read_comment_block(stream, start_re, end_re):
    """Read a comment block with start/end markers on their own lines."""
    while True:
        oldpos = stream.tell()
        line = stream.readline()
        # Blank line
        if line and not line.strip():
            pass
        # Start of comment block
        elif re.match(start_re, line):
            lines = []
            while True:
                # End of file:
                if not line:
                    stream.seek(oldpos)
                    return [''.join(lines)]

                # End of block:
                elif end_re is not None and re.match(end_re, line.strip()):
                    lines.append(line)
                    return [''.join(lines)]

                # Anything else is part of the block.
                lines.append(line)

                line = stream.readline()
        # Other line or EOF
        else:
            stream.seek(oldpos)
            return []

def read_regexp_block2(stream, start_re, end_re=None):

    """
    Modification of nltk.corpus.reader.util.read_regexp_block.

    Read a sequence of tokens from a stream, where tokens begin with
    lines that match ``start_re``.  If ``end_re`` is specified, then
    tokens end with lines that match ``end_re``. Tokens also end
    whenever the next line matching ``start_re`` or EOF is found.
    """
    
    # Scan until we find a line matching the start regexp.
    while True:
        line = stream.readline()
        if not line: return [] # end of file.
        if re.match(start_re, line): break

    # Scan until we find another line matching the regexp, or EOF.
    lines = [line]
    while True:
        oldpos = stream.tell()
        line = stream.readline()
        # End of file:
        if not line:
            return [''.join(lines)]
        # End of token:
        if end_re is not None and re.match(end_re, line):
            stream.seek(oldpos)
            return [''.join(lines)]
        # Start of new token: backup to just before it starts, and
        # return the token we've already collected.
        if re.match(start_re, line):
            stream.seek(oldpos)
            return [''.join(lines)]
        # Anything else is part of the token.
        lines.append(line)
