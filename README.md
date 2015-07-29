# python-email-reply-parser

[![Build Status](https://travis-ci.org/antonagestam/python-email-reply-parser.svg?branch=master)](https://travis-ci.org/antonagestam/python-email-reply-parser)

Python port of https://github.com/github/email_reply_parser, including most of the test suite.

## Usage

``` python
>>> from email_reply_parser import  parse_reply
>>> print(parse_reply("""Hi Anton,
...
... I'm totally fine, how are you?
...
... On Tue, Jul 28, 2015 at 11:38 AM, Anton Agestam
... <anton@example.com> wrote:
...
... > Hi there Jane,
... > How are you today?
... > —
... > Anton Agestam
...
... """))
Hi Anton,

I'm totally fine, how are you?

```
