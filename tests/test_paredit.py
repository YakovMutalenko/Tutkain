from inspect import cleandoc
import sublime

from tutkain import tutkain
from unittest import TestCase


from .util import ViewTestCase


class TestOpenRoundCommand(ViewTestCase):
    def test_open_round(self):
        self.set_view_content('(a b c d)')
        self.set_selections((5, 5))
        self.view.run_command('tutkain_paredit_open_round')
        self.assertEquals('(a b () c d)', self.view_content())
        self.assertEquals(self.selections(), [(6, 6)])

    def test_open_round_next_to_whitespace(self):
        self.set_view_content('(a b c d)')
        self.set_selections((9, 9))
        self.view.run_command('tutkain_paredit_open_round')
        self.assertEquals('(a b c d)()', self.view_content())
        self.assertEquals(self.selections(), [(10, 10)])

    def test_open_round_inside_string(self):
        self.set_view_content('(foo "bar baz" quux)')
        self.set_selections((10, 10))
        self.view.run_command('tutkain_paredit_open_round')
        self.assertEquals('(foo "bar (baz" quux)', self.view_content())
        self.assertEquals(self.selections(), [(11, 11)])

    def test_open_round_multiple_cursors(self):
        self.set_view_content('(a b c d) (e f g h)')
        self.set_selections((5, 5), (15, 15))
        self.view.run_command('tutkain_paredit_open_round')
        self.assertEquals('(a b () c d) (e f () g h)', self.view_content())
        self.assertEquals(self.selections(), [(6, 6), (19, 19)])

    def test_open_round_selection(self):
        self.set_view_content('(a b c)')
        self.set_selections((3, 4))
        self.view.run_command('tutkain_paredit_open_round')
        self.assertEquals('(a (b) c)', self.view_content())
        self.assertEquals(self.selections(), [(4, 4)])

    def test_open_round_before_close_paren(self):
        self.set_view_content('(a )')
        self.set_selections((3, 3))
        self.view.run_command('tutkain_paredit_open_round')
        self.assertEquals('(a ())', self.view_content())
        self.assertEquals(self.selections(), [(4, 4)])

    def test_open_round_before_close_paren(self):
        self.set_view_content('(a [b ])')
        self.set_selections((6, 6))
        self.view.run_command('tutkain_paredit_open_round')
        self.assertEquals('(a [b ()])', self.view_content())
        self.assertEquals(self.selections(), [(7, 7)])

    def test_close_round(self):
        self.set_view_content('(a )')
        self.set_selections((2, 2))
        self.view.run_command('tutkain_paredit_close_round')
        self.assertEquals('(a)', self.view_content())
        self.assertEquals(self.selections(), [(3, 3)])

    def test_close_round_multiple_cursors(self):
        self.set_view_content('(a ) (b )')
        self.set_selections((2, 2), (7, 7))
        self.view.run_command('tutkain_paredit_close_round')
        self.assertEquals('(a) (b)', self.view_content())
        self.assertEquals(self.selections(), [(3, 3), (7, 7)])

    def test_open_square(self):
        self.set_view_content('(a b c d)')
        self.set_selections((5, 5))
        self.view.run_command('tutkain_paredit_open_square')
        self.assertEquals('(a b [] c d)', self.view_content())
        self.assertEquals(self.selections(), [(6, 6)])

    def test_close_square(self):
        self.set_view_content('[a ]')
        self.set_selections((2, 2))
        self.view.run_command('tutkain_paredit_close_square')
        self.assertEquals('[a]', self.view_content())
        self.assertEquals(self.selections(), [(3, 3)])

    def test_open_curly(self):
        self.set_view_content('(a b c d)')
        self.set_selections((5, 5))
        self.view.run_command('tutkain_paredit_open_curly')
        self.assertEquals('(a b {} c d)', self.view_content())
        self.assertEquals(self.selections(), [(6, 6)])

    def test_close_curly(self):
        self.set_view_content('{a b }')
        self.set_selections((4, 4))
        self.view.run_command('tutkain_paredit_close_curly')
        self.assertEquals('{a b}', self.view_content())
        self.assertEquals(self.selections(), [(5, 5)])

    def test_double_quote_simple(self):
        self.set_selections((0, 0))
        self.view.run_command('tutkain_paredit_double_quote')
        self.assertEquals('""', self.view_content())
        self.assertEquals(self.selections(), [(1, 1)])

    def test_double_quote_inside_string(self):
        self.set_view_content('" "')
        self.set_selections((1, 1))
        self.view.run_command('tutkain_paredit_double_quote')
        self.assertEquals('"\\" "', self.view_content())
        self.assertEquals(self.selections(), [(3, 3)])

    def test_double_quote_next_to_left_double_quote(self):
        self.set_view_content('""')
        self.set_selections((0, 0))
        self.view.run_command('tutkain_paredit_double_quote')
        self.assertEquals('""', self.view_content())
        self.assertEquals(self.selections(), [(1, 1)])

    def test_double_quote_next_to_right_double_quote(self):
        self.set_view_content('""')
        self.set_selections((1, 1))
        self.view.run_command('tutkain_paredit_double_quote')
        self.assertEquals('""', self.view_content())
        self.assertEquals(self.selections(), [(2, 2)])

    def test_double_quote_inside_comment(self):
        self.set_view_content('; ')
        self.set_selections((2, 2))
        self.view.run_command('tutkain_paredit_double_quote')
        self.assertEquals('; "', self.view_content())
        self.assertEquals(self.selections(), [(3, 3)])

    def test_double_quote_multiple_cursors(self):
        self.set_view_content(' ')
        self.set_selections((0, 0), (1, 1))
        self.view.run_command('tutkain_paredit_double_quote')
        self.assertEquals('"" ""', self.view_content())
        self.assertEquals(self.selections(), [(1, 1), (4, 4)])
        self.view.run_command(('tutkain_paredit_double_quote'))
        self.assertEquals(self.selections(), [(2, 2), (5, 5)])

    def test_forward_slurp_word(self):
        self.set_view_content('(a (b) c)')
        self.set_selections((3, 3))
        self.view.run_command('tutkain_paredit_forward_slurp')
        self.set_view_content('(a (b) c)')
        self.set_selections((5, 5))
        self.view.run_command('tutkain_paredit_forward_slurp')
        self.assertEquals('(a (b c))', self.view_content())
        self.assertEquals(self.selections(), [(5, 5)])
        self.set_view_content('(a (b ) c)')
        self.set_selections((5, 5))
        self.view.run_command('tutkain_paredit_forward_slurp')
        self.assertEquals('(a (b c))', self.view_content())
        self.assertEquals(self.selections(), [(5, 5)])

    def test_forward_slurp_indent(self):
        self.set_view_content('(a (b    ) {:c    :d})')
        self.set_selections((5, 5))
        self.view.run_command('tutkain_paredit_forward_slurp')
        self.assertEquals('(a (b {:c :d}))', self.view_content())
        self.assertEquals(self.selections(), [(5, 5)])

    def test_forward_slurp_set(self):
        self.set_view_content('(a (b) #{1 2 3})')
        self.set_selections((5, 5))
        self.view.run_command('tutkain_paredit_forward_slurp')
        self.assertEquals('(a (b #{1 2 3}))', self.view_content())
        self.assertEquals(self.selections(), [(5, 5)])

    def test_forward_slurp_string(self):
        self.set_view_content('"a" b')
        self.set_selections((2, 2))
        self.view.run_command('tutkain_paredit_forward_slurp')
        self.assertEquals('"a b"', self.view_content())
        self.assertEquals(self.selections(), [(2, 2)])

    def test_forward_slurp_multiple_cursors(self):
        self.set_view_content('(a (b) c) (d (e) f)')
        self.set_selections((5, 5), (15, 15))
        self.view.run_command('tutkain_paredit_forward_slurp')
        self.assertEquals('(a (b c)) (d (e f))', self.view_content())
        self.assertEquals(self.selections(), [(5, 5), (15, 15)])

    def test_forward_barf_word(self):
        self.set_view_content('(a (b c))')
        self.set_selections((4, 4))
        self.view.run_command('tutkain_paredit_forward_barf')
        self.assertEquals('(a (b) c)', self.view_content())
        self.assertEquals(self.selections(), [(4, 4)])
        self.view.run_command('tutkain_paredit_forward_barf')
        self.assertEquals('(a () b c)', self.view_content())
        self.assertEquals(self.selections(), [(4, 4)])
        self.view.run_command('tutkain_paredit_forward_barf')
        self.assertEquals('(a () b c)', self.view_content())
        self.assertEquals(self.selections(), [(4, 4)])

    def test_forward_barf_empty(self):
        self.set_view_content('(a () c)')
        self.set_selections((4, 4))
        self.view.run_command('tutkain_paredit_forward_barf')
        self.assertEquals('(a () c)', self.view_content())
        self.assertEquals(self.selections(), [(4, 4)])

    def test_forward_barf_set(self):
        self.set_view_content('(a (b #{1 2 3}))')
        self.set_selections((4, 4))
        self.view.run_command('tutkain_paredit_forward_barf')
        self.assertEquals('(a (b) #{1 2 3})', self.view_content())
        self.assertEquals(self.selections(), [(4, 4)])

    def test_forward_barf_string(self):
        self.set_view_content('"a b"')
        self.set_selections((1, 1))
        self.view.run_command('tutkain_paredit_forward_barf')
        self.assertEquals('"a" b', self.view_content())
        self.assertEquals(self.selections(), [(1, 1)])
        self.view.run_command('tutkain_paredit_forward_barf')
        self.assertEquals('"" a b', self.view_content())
        self.assertEquals(self.selections(), [(1, 1)])

    def test_forward_barf_multiple_cursors(self):
        self.set_view_content('(a (b c)) (d (e f))')
        self.set_selections((4, 4), (14, 14))
        self.view.run_command('tutkain_paredit_forward_barf')
        self.assertEquals('(a (b) c) (d (e) f)', self.view_content())
        self.assertEquals(self.selections(), [(4, 4), (14, 14)])

    def test_wrap_round(self):
        self.set_view_content('(foo bar baz)')
        self.set_selections((5, 5))
        self.view.run_command('tutkain_paredit_wrap_round')
        self.assertEquals('(foo (bar) baz)', self.view_content())
        self.assertEquals([(6, 6)], self.selections())

        self.set_view_content('(foo [bar] baz)')
        self.set_selections((5, 5))
        self.view.run_command('tutkain_paredit_wrap_round')
        self.assertEquals('(foo ([bar]) baz)', self.view_content())

        self.set_view_content('(foo [bar] baz)')
        self.set_selections((10, 10))
        self.view.run_command('tutkain_paredit_wrap_round')
        self.assertEquals('(foo ([bar]) baz)', self.view_content())

        self.set_view_content('')
        self.set_selections((0, 0))
        self.view.run_command('tutkain_paredit_wrap_round')
        self.assertEquals('()', self.view_content())
        self.assertEquals([(1, 1)], self.selections())

        self.set_view_content('(foo bar baz) (qux quux quuz)')
        self.set_selections((5, 5), (19, 19))
        self.view.run_command('tutkain_paredit_wrap_round')
        self.assertEquals('(foo (bar) baz) (qux (quux) quuz)', self.view_content())
        self.assertEquals([(6, 6), (22, 22)], self.selections())

    def test_wrap_square(self):
        self.set_view_content('(foo bar baz)')
        self.set_selections((5, 5))
        self.view.run_command('tutkain_paredit_wrap_square')
        self.assertEquals('(foo [bar] baz)', self.view_content())
        self.assertEquals([(6, 6)], self.selections())

    def test_backward_delete(self):
        self.set_view_content('("zot" quux)')
        self.set_selections((8, 8))
        self.view.run_command('tutkain_paredit_backward_delete')
        self.assertEquals('("zot" uux)', self.view_content())
        self.assertEquals([(7, 7)], self.selections())

        self.set_view_content('("zot" quux)')
        self.set_selections((6, 6))
        self.view.run_command('tutkain_paredit_backward_delete')
        self.assertEquals('("zot" quux)', self.view_content())
        self.assertEquals([(5, 5)], self.selections())
        self.view.run_command('tutkain_paredit_backward_delete')
        self.assertEquals('("zo" quux)', self.view_content())
        self.assertEquals([(4, 4)], self.selections())

        self.set_view_content('(foo bar) (baz quux)')
        self.set_selections((9, 9), (21, 21))
        self.view.run_command('tutkain_paredit_backward_delete')
        self.assertEquals('(foo bar) (baz quux)', self.view_content())
        self.assertEquals([(8, 8), (19, 19)], self.selections())

        self.set_view_content('("")')
        self.set_selections((2, 2))
        self.view.run_command('tutkain_paredit_backward_delete')
        self.assertEquals('()', self.view_content())
        self.assertEquals([(1, 1)], self.selections())
        self.view.run_command('tutkain_paredit_backward_delete')
        self.assertEquals('', self.view_content())
        self.assertEquals([(0, 0)], self.selections())

        self.set_view_content('(a)')
        self.set_selections((1, 1))
        self.view.run_command('tutkain_paredit_backward_delete')
        self.assertEquals('(a)', self.view_content())
        self.assertEquals([(1, 1)], self.selections())

        self.set_view_content('(a)')
        self.set_selections((0, 3))
        self.view.run_command('tutkain_paredit_backward_delete')
        self.assertEquals('', self.view_content())
        self.assertEquals([(0, 0)], self.selections())

        self.set_view_content('("()")')
        self.set_selections((4, 4))
        self.view.run_command('tutkain_paredit_backward_delete')
        self.assertEquals('("(")', self.view_content())
        self.view.run_command('tutkain_paredit_backward_delete')
        self.assertEquals('("")', self.view_content())