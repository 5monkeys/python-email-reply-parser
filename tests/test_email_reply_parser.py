import os
import re
import unittest
from functools import partial

from email_reply_parser import read, parse_reply

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emails')


def get_fixture(name):
    with open(os.path.join(FIXTURE_DIR, '{}.txt'.format(name))) as f:
        return f.read()


def email(name):
    return read(get_fixture('email_{}'.format(name)))


def attrs(iterable, attr_name):
    return [getattr(f, attr_name) for f in iterable]

l_quoted = partial(attrs, attr_name='quoted')
l_signature = partial(attrs, attr_name='signature')
l_hidden = partial(attrs, attr_name='hidden')


class TestEmailReplyParser(unittest.TestCase):
    def assert_regex(self, text, pattern, msg=None):
        self.assertTrue(bool(re.search(pattern, text, re.M)), msg=msg)

    def test_reads_simple_body(self):
        reply = email('1_1')
        self.assertEqual(3, len(reply.fragments))

        self.assertFalse(any(l_quoted(reply.fragments)))
        self.assertEqual(
            [False, True, True], l_signature(reply.fragments))
        self.assertEqual(
            [False, True, True], l_hidden(reply.fragments))

        self.assertEqual("""Hi folks

What is the best way to clear a Riak bucket of all key, values after
running a test?
I am currently using the Java HTTP API.\n""", str(reply.fragments[0]))

        self.assertEqual("-Abhishek Kona\n\n", str(reply.fragments[1]))

    def test_reads_top_post(self):
        reply = email('1_3')
        self.assertEqual(5, len(reply.fragments))

        self.assertEqual(
            [False, False, True, False, False], l_quoted(reply.fragments))
        self.assertEqual(
            [False, True, True, True, True], l_hidden(reply.fragments))
        self.assertEqual(
            [False, True, False, False, True], l_signature(reply.fragments))

        self.assertTrue(
            str(reply.fragments[0]).startswith("Oh thanks.\n\nHaving"))
        self.assertTrue(
            str(reply.fragments[1]).startswith("-A"))
        self.assertTrue(
            str(reply.fragments[2]).startswith(
                "\nOn 01/03/11 7:07 PM, Russell Brown wrote:"))
        self.assertTrue(
            str(reply.fragments[4]).startswith("_"))

    def test_reads_bottom_post(self):
        reply = email('1_2')
        self.assertEqual(6, len(reply.fragments))

        self.assertEqual(
            [False, True, False, True, False, False], l_quoted(reply.fragments))
        self.assertEqual(
            [False, False, False, False, False, True],
            l_signature(reply.fragments))
        self.assertEqual(
            [False, False, False, True, True, True], l_hidden(reply.fragments))

        self.assertEqual("Hi,", str(reply.fragments[0]))
        self.assertEqual(
            "On Tue, 2011-03-01 at 18:02 +0530, Abhishek Kona wrote:",
            str(reply.fragments[1]).split('\n')[0])
        self.assertTrue(str(reply.fragments[2]).startswith("\nYou can list"))
        self.assertTrue(bool(re.search(r"^> ", str(reply.fragments[3]), re.M)))
        self.assertTrue(str(reply.fragments[5]).startswith('_'))

    def test_reads_inline_replies(self):
        reply = email('1_8')
        self.assertEqual(7, len(reply.fragments))

        self.assertEqual(
            [True, False, True, False, True, False, False],
            l_quoted(reply.fragments))
        self.assertEqual(
            [False, False, False, False, False, False, True],
            l_signature(reply.fragments))
        self.assertEqual(
            [False, False, False, False, True, True, True],
            l_hidden(reply.fragments))

        self.assert_regex(str(reply.fragments[0]), r"^On [^\:]+\:")
        self.assert_regex(str(reply.fragments[1]), r"^I will reply")
        self.assert_regex(str(reply.fragments[2]), r"okay\?")
        self.assert_regex(str(reply.fragments[3]), r"^and under this.")
        self.assert_regex(str(reply.fragments[4]), r"inline")
        self.assertEqual("\n", str(reply.fragments[5]))
        self.assertEqual(
            "--\nHey there, this is my signature\n", str(reply.fragments[6]))

    def test_recognizes_date_string_above_quote(self):
        reply = email('1_4')

        self.assert_regex(str(reply.fragments[0]), r"^Awesome")
        self.assert_regex(str(reply.fragments[1]), r"^On")
        self.assert_regex(str(reply.fragments[1]), r"Loader")

    def test_a_complex_body_with_only_one_fragment(self):
        reply = email('1_5')

        self.assertEqual(1, len(reply.fragments))

    def test_reads_email_with_correct_signature(self):
        reply = read(get_fixture('correct_sig'))

        self.assertEqual(2, len(reply.fragments))
        self.assertEqual([False, False], l_quoted(reply.fragments))
        self.assertEqual([False, True], l_signature(reply.fragments))
        self.assertEqual([False, True], l_hidden(reply.fragments))
        self.assert_regex(str(reply.fragments[1]), r"^-- \nrick")

    def test_deals_with_multiline_reply_headers(self):
        reply = email('1_6')

        self.assert_regex(str(reply.fragments[0]), r"^I get")
        self.assert_regex(str(reply.fragments[1]), r"^On")
        self.assert_regex(str(reply.fragments[1]), r"Was this")

    def test_deals_with_windows_line_endings(self):
        reply = email('1_7')

        self.assert_regex(str(reply.fragments[0]), r":\+1:")
        self.assert_regex(str(reply.fragments[1]), r"^On")
        self.assert_regex(str(reply.fragments[1]), r"Steps 0-2")

    def test_returns_only_the_visible_fragments_as_a_string(self):
        reply = email("2_1")

        visible = '\n'.join([str(f) for f in reply.fragments if not f.hidden])
        self.assertEqual(visible.rstrip(), reply.visible_text())

    def test_parse_out_just_top_for_outlook_reply(self):
        body = get_fixture('email_2_1')
        self.assertEqual("Outlook with a reply", parse_reply(body))

    def test_parse_out_just_top_for_outlook_with_reply_directly_above_line(
            self):
        body = get_fixture("email_2_2")
        self.assertEqual(
            "Outlook with a reply directly above line", parse_reply(body))

    def test_parse_out_sent_from_iPhone(self):
        body = get_fixture("email_iPhone")
        self.assertEqual("Here is another email", parse_reply(body))

    def test_parse_out_sent_from_BlackBerry(self):
        body = get_fixture("email_BlackBerry")
        self.assertEqual("Here is another email", parse_reply(body))

    def test_parse_out_send_from_multiword_mobile_device(self):
        body = get_fixture("email_multi_word_sent_from_my_mobile_device")
        self.assertEqual("Here is another email", parse_reply(body))

    def test_do_not_parse_out_send_from_in_regular_sentence(self):
        body = get_fixture("email_sent_from_my_not_signature")
        self.assertEqual(
            "Here is another email\n\nSent from my desk, is much easier then my"
            " mobile phone.", parse_reply(body))

    def test_retains_bullets(self):
        body = get_fixture("email_bullets")
        self.assertEqual(
            "test 2 this should list second\n\nand have spaces\n\nand retain th"
            "is formatting\n\n\n   - how about bullets\n   - and another",
            parse_reply(body))

    def test_parse_reply(self):
        body = get_fixture("email_1_2")
        self.assertEqual(read(body).visible_text(), parse_reply(body))

    def test_one_is_not_on(self):
        reply = email("one_is_not_on")
        self.assert_regex(str(reply.fragments[0]), r"One outstanding question")
        self.assert_regex(str(reply.fragments[1]), r"^On Oct 1, 2012")

    def test_mulitple_on(self):
        reply = read(get_fixture("greedy_on"))
        self.assert_regex(str(reply.fragments[0]), r"^On your remote host")
        self.assert_regex(str(reply.fragments[1]), r"^On 9 Jan 2014")
        self.assertEqual([False, True, False], l_quoted(reply.fragments))
        self.assertEqual([False, False, False], l_signature(reply.fragments))
        self.assertEqual([False, True, True], l_hidden(reply.fragments))

    def test_doesnt_remove_signature_delimiter_in_mid_line(self):
        reply = read(get_fixture("email_sig_delimiter_in_middle_of_line"))
        self.assertEqual(1, len(reply.fragments))

    def test_complex_reply_chain(self):
        reply = email('3_1')
        self.assertEqual("r4\n", reply.visible_text())
