# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

from plover.dictionary.rtfcre_dict import load_dictionary, TranslationConverter, format_translation, save_dictionary
import mock
import re
import unittest
from StringIO import StringIO

class TestCase(unittest.TestCase):
    
    def test_converter(self):
        styles = {1: 'Normal', 2: 'Continuation'}
        
        convert = TranslationConverter(styles)
        
        cases = (
        
        ('', ''),
        (r'\-', '-'),
        (r'\\', '\\'),
        (r'\{', '{'),
        (r'\}', '}'),
        (r'\~', '{^ ^}'),
        (r'\_', '-'),
        ('\\\r', '{#Return}{#Return}'),
        ('\\\n', '{#Return}{#Return}'),
        (r'\cxds', '{^}'),
        (r'pre\cxds ', '{pre^}'),
        (r'pre\cxds  ', '{pre^} '),
        (r'pre\cxds', '{pre^}'),
        (r'\cxds post', '{^post}'),
        (r'\cxds in\cxds', '{^in^}'),
        (r'\cxds in\cxds ', '{^in^}'),
        (r'\cxfc', '{-|}'),
        (r'\cxfl', '{>}'),
        (r'pre\cxfl', 'pre{>}'),
        (r'{\*\cxsvatdictflags N}', '{-|}'),
        (r'{\*\cxsvatdictflags LN1}', '{-|}'),
        (r'\par', '{#Return}{#Return}'),
        # caseCATalyst declares new styles without a preceding \par so we treat
        # it as an implicit par.
        (r'\s1', '{#Return}{#Return}'),
        # But if the \par is present we don't treat \s as an implicit par.
        (r'\par\s1', '{#Return}{#Return}'),
        # Continuation styles are indented too.
        (r'\par\s2', '{#Return}{#Return}{^    ^}'),
        # caseCATalyst punctuation.
        (r'.', '{.}'),
        (r'. ', '{.} '),
        (r' . ', ' . '),
        (r'{\cxa Q.}.', 'Q..'),
        (r'Mr.', 'Mr.'),  # Don't mess with period that is part of a word.
        (r'.attribute', '.attribute'),
        (r'{\cxstit contents}', 'contents'),
        (r'{\cxfing c}', '{&c}'),
        (r'{\cxp.}', '{.}'),
        (r'{\cxp .}', '{.}'),
        (r'{\cxp . }', '{.}'),
        (r'{\cxp .  }', '{.}'),
        (r'{\cxp !}', '{!}'),
        (r'{\cxp ?}', '{?}'),
        (r'{\cxp ,}', '{,}'),
        (r'{\cxp ;}', '{;}'),
        (r'{\cxp :}', '{:}'),
        ('{\\cxp \'}', '{^\'}'),
        ('{\\cxp -}', '{^-^}'),
        ('{\\cxp /}', '{^/^}'),
        ('{\\cxp...  }', '{^...  ^}'),
        ('{\\cxp ") }', '{^") ^}'),
        ('{\\nonexistant }', ''),
        ('{\\nonexistant contents}', 'contents'),
        ('{\\nonexistant cont\\_ents}', 'cont-ents'),
        ('{\\*\\nonexistant }', ''),
        ('{\\*\\nonexistant contents}', ''),
        ('{eclipse command}', '{eclipse command}'),
        ('test text', 'test text'),
        ('test  text', 'test{^  ^}text'),
        (r'{\cxconf [{\cxc abc}]}', 'abc'),
        (r'{\cxconf [{\cxc abc}|{\cxc def}]}', 'def'),
        (r'{\cxconf [{\cxc abc}|{\cxc def}|{\cxc ghi}]}', 'ghi'),
        (r'{\cxconf [{\cxc abc}|{\cxc {\cxp... }}]}', '{^... ^}'),
        (r'be\cxds{\*\cxsvatdictentrydate\yr2006\mo5\dy10}', '{be^}'),
        
        (r'{\nonexistant {\cxp .}}', '{.}'),
        (r'{\*\nonexistant {\cxp .}}', ''),
        )
        
        failed = []
        for before, after in cases:
            if convert(before) != after:
                failed.append((before, after))
                
        for before, after in failed:
            print 'convert(%s) != %s: %s' % (before, after, convert(before))

        self.assertEqual(len(failed), 0)
    
    def test_load_dict(self):
        """Test the load_dict function.

        This test just tests load_dict so it mocks out the converters and just
        verifies that they are called.

        """
        
        expected_styles = {
            0: 'Normal',
            1: 'Question',
            2: 'Answer',
            3: 'Colloquy',
            4: 'Continuation Q',
            5: 'Continuation A',
            6: 'Continuation Col',
            7: 'Paren',
            8: 'Centered',
        }
        
        header = '\r\n'.join(
            [r'{\rtf1\ansi\cxdict{\*\cxrev100}{\*\cxsystem Fake Software}'] +
            [r'{\s%d %s;}' % (k, v) for k, v in expected_styles.items()] + 
            ['}'])
        footer = '\r\n}'
        
        def make_dict(s):
            d = StringIO(''.join((header, s, footer)))
            d.name = "'%s'" % s
            return d

        def assertEqual(a, b):
            self.assertEqual(a._dict, b)

        this = self

        class Converter(object):
            def __init__(self, styles):
                this.assertEqual(styles, expected_styles)

            def __call__(self, s):
                if s == 'return_none':
                    return None
                return 'converted(%s)' % s
                
        convert = Converter(expected_styles)
        normalize = lambda x: 'normalized(%s)' % x
        
        cases = (
        
        # Empty dictionary.
        ('', {}),
        # Only one translation.
        ('{\\*\\cxs SP}translation', {'SP': 'translation'}),
        # Multiple translations no newlines.
        ('{\\*\\cxs SP}translation{\\*\\cxs S}translation2', 
         {'SP': 'translation', 'S': 'translation2'}),
        # Multiple translations on separate lines.
        ('{\\*\\cxs SP}translation\r\n{\\*\\cxs S}translation2', 
         {'SP': 'translation', 'S': 'translation2'}),
        ('{\\*\\cxs SP}translation\n{\\*\\cxs S}translation2', 
         {'SP': 'translation', 'S': 'translation2'}),
        # Escaped \r and \n handled
        ('{\\*\\cxs SP}trans\\\r\\\n', {'SP': 'trans\\\r\\\n'}),
        # Escaped \r\n handled in mid translation
        ('{\\*\\cxs SP}trans\\\r\\\nlation', {'SP': 'trans\\\r\\\nlation'}),
        # Whitespace is preserved in various situations.
        ('{\\*\\cxs S}t  ', {'S': 't  '}),
        ('{\\*\\cxs S}t   {\\*\\cxs T}t    ', {'S': 't   ', 'T': 't    '}),
        ('{\\*\\cxs S}t   \r\n{\\*\\cxs T}t    ', {'S': 't   ', 'T': 't    '}),
        ('{\\*\\cxs S}t  \r\n{\\*\\cxs T} t \r\n', {'S': 't  ', 'T': ' t '}),
        # Translations are ignored if converter returns None
        ('{\\*\\cxs S}return_none', {}),
        ('{\\*\\cxs T}t t t  ', {'T': 't t t  '}),
        # Conflicts result on only the last one kept.
        ('{\\*\\cxs T}t{\\*\\cxs T}g', {'T': 'g'}),
        ('{\\*\\cxs T}t{\\*\\cxs T}return_none', {'T': 't'}),
        
        )
        
        patch_path = 'plover.dictionary.rtfcre_dict'
        with mock.patch.multiple(patch_path, normalize_steno=normalize, 
                                 TranslationConverter=Converter):
            for s, expected in cases:
                expected = dict((normalize(k), convert(v)) 
                                for k, v in expected.iteritems())
                assertEqual(load_dictionary(make_dict(s)), expected)

    def test_format_translation(self):
        cases = (
        ('', ''),
        ('{^in^}', '\cxds in\cxds '),
        ('{pre^}', 'pre\cxds '),
        ('{pre^} ', 'pre\cxds '),
        ('{pre^}  ', 'pre\cxds ')
        )
        
        failed = False
        format_str = "format({}) != {}: {}"
        for before, expected in cases:
            result = format_translation(before)
            if result != expected:
                failed = True
                print format_str.format(before, expected, result)
            
        self.assertFalse(failed)
        
    def test_save_dictionary(self):
        f = StringIO()
        d = {
        'S/T': '{pre^}',
        }
        save_dictionary(d, f)
        expected = '{\\rtf1\\ansi{\\*\\cxrev100}\\cxdict{\\*\\cxsystem Plover}{\\stylesheet{\\s0 Normal;}}\r\n{\\*\\cxs S///T}pre\\cxds \r\n}\r\n' 
        self.assertEqual(f.getvalue(), expected)


if __name__ == '__main__':
    unittest.main()
