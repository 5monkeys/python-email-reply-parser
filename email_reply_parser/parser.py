"""
Ported from https://github.com/github/email_reply_parser

EmailReplyParser is a small library to parse plain text email content.  The
goal is to identify which fragments are quoted, part of a signature, or
original body content.  We want to support both top and bottom posters, so
no simple "REPLY ABOVE HERE" content is used.

Beyond RFC 5322 (which is handled by the [Ruby mail gem][mail]), there aren't
any real standards for how emails are created.  This attempts to parse out
common conventions for things like replies:

    this is some text

    On <date>, <author> wrote:
    > blah blah
    > blah blah

... and signatures:

    this is some text

    --
    Bob
    http://homepage.com/~bob

Each of these are parsed into Fragment objects.

EmailReplyParser also attempts to figure out which of these blocks should
be hidden from users.
"""
import re


class Fragment(object):
    """
    Represents a group of paragraphs in the email sharing common attributes.
    Paragraphs should get their own fragment if they are a quoted area or a
    signature.
    """
    def __init__(self, quoted, first_line):
        self.signature = False
        self.hidden = False
        self.lines = [first_line] if first_line is not None else []
        self.content = None
        self.quoted = quoted

    def finish(self):
        """
        Builds the string content by joining the lines and reversing them.
        """
        self.content = '\n'.join(self.lines)[::-1]
        self.lines = None

    def __str__(self):
        return self.content


class Email(object):
    """An Email instance represents a parsed body String."""

    multiline_pattern = re.compile(
        r"^(?!On.*On\s.+?wrote:)(On\s(?:.+?)wrote:)$", re.M | re.I | re.S)
    underscore_pattern = re.compile(r"([^\n])(?=\n_{7}_+)$", re.M)
    signature_pattern = re.compile(
        r"(?m)(--\s*$|__\s*$|\w-$)|(^(\w+\s*){1,3} ym morf tneS$)")
    header_pattern = re.compile(r"^:etorw.*nO$")
    empty = ""

    def __init__(self):
        self.fragments = []

    def visible_text(self):
        """Gets the combined text of the visible fragments of the email body."""
        visible = '\n'.join([str(f) for f in self.fragments if not f.hidden])
        return visible.rstrip()

    def read(self, text):
        """
        Splits the given text into a list of Fragments.  This is roughly done by
        reversing the text and parsing from the bottom to the top.  This way we
        can check for 'On <date>, <author> wrote:' lines above quoted blocks.
        """

        # Normalize line endings
        text = text.replace("\r\n", "\n")

        # Check for multi-line reply headers. Some clients break up
        # the "On DATE, NAME <EMAIL> wrote:" line into multiple lines.
        text = self.multiline_pattern.sub(
            lambda matchobj: matchobj.group(0).replace("\n", " "), text)

        # Some users may reply directly above a line of underscores.
        # In order to ensure that these fragments are split correctly,
        # make sure that all lines of underscores are preceded by
        # at least two newline characters.
        text = self.underscore_pattern.sub("\\1\n", text)

        # The text is reversed initially due to the way we check for hidden
        # fragments.
        text = text[::-1]

        # This determines if any 'visible' Fragment has been found. Once any
        # visible Fragment is found, stop looking for hidden ones.
        self.found_visible = False

        # This instance variable points to the current Fragment.  If the matched
        # line fits, it should be added to this Fragment.  Otherwise, finish it
        # and start a new Fragment.
        self.fragment = None

        for line in text.split('\n'):
            self.scan_line(line)

        # Finish up the final fragment.  Finishing a fragment will detect any
        # attributes (hidden, signature, reply), and join each line into a
        # string.
        self.finish_fragment()

        self.fragment = None

        # Now that parsing is done, reverse the order.
        self.fragments = self.fragments[::-1]

        return self

    def scan_line(self, line):
        """
        Scans the given line of text and figures out which fragment it belongs
        to.
        """
        line = line.rstrip("\n")
        if not self.signature_pattern.search(line):
            line = line.lstrip()

        # We're looking for leading `>`'s to see if this line is part of a
        # quoted Fragment.
        is_quoted = line.endswith('>')

        # Mark the current Fragment as a signature if the current line is empty
        # and the Fragment starts with a common signature indicator.
        if (self.fragment and line == self.empty
                and self.signature_pattern.search(self.fragment.lines[-1])):
            self.fragment.signature = True
            self.finish_fragment()

        # If the line matches the current fragment, add it.  Note that a common
        # reply header also counts as part of the quoted Fragment, even though
        # it doesn't start with `>`.
        if (self.fragment and
                ((self.fragment.quoted == is_quoted) or
                 self.fragment.quoted and
                 (self.quote_header(line) or line == self.empty))):
            self.fragment.lines.append(line)
        # Otherwise, finish the fragment and start a new one.
        else:
            self.finish_fragment()
            self.fragment = Fragment(is_quoted, line)

    def quote_header(self, line):
        """
        Detects if a given line is a header above a quoted area.  It is only
        checked for lines preceding quoted regions.
        """
        return bool(self.header_pattern.search(line))

    def finish_fragment(self):
        """
        Builds the fragment string and reverses it, after all lines have been
        added.  It also checks to see if this Fragment is hidden.  The hidden
        Fragment check reads from the bottom to the top.

        Any quoted Fragments or signature Fragments are marked hidden if they
        are below any visible Fragments.  Visible Fragments are expected to
        contain original content by the author.  If they are below a quoted
        Fragment, then the Fragment should be visible to give context to the
        reply.

            some original text (visible)

            > do you have any two's? (quoted, visible)

            Go fish! (visible)

            > --
            > Player 1 (quoted, hidden)

            --
            Player 2 (signature, hidden)
        """
        frag = self.fragment
        if frag:
            frag.finish()
            if not self.found_visible:
                if (frag.quoted or frag.signature
                        or str(frag).strip() == self.empty):
                    frag.hidden = True
                else:
                    self.found_visible = True
            self.fragments.append(frag)
        self.fragment = None


def read(text):
    """Splits an email body into a list of Fragments."""
    return Email().read(text)


def parse_reply(text):
    """Get the text of the visible portions of the given email body."""
    return read(text).visible_text()
