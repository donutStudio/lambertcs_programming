import unittest
from club.markdown_math import render_markdown

class MarkdownMathTests(unittest.TestCase):
    def test_inline_math_preserves_latex(self):
        html = render_markdown(r'Use $x_i + \frac{1}{2}$ and **bold**.')
        self.assertIn('data-math="x_i + \\frac{1}{2}"', html)
        self.assertIn('<strong>bold</strong>', html)

    def test_all_delimiters(self):
        for expression in [r'$x^2$', r'$$x^2$$', r'\(x^2\)', r'\[x^2\]']:
            html = render_markdown(expression)
            self.assertIn('data-math="x^2"', html)
        self.assertIn('data-display="true"', render_markdown('$$\nx^2\n$$'))

    def test_code_and_escaped_dollars_are_literal(self):
        for source in ['`$x$`', '```python\nprint("$x$")\n```', r'Price: \$5 and \$10']:
            self.assertNotIn('math-expression', render_markdown(source))

    def test_math_in_table_and_safe_attributes(self):
        html = render_markdown('| Value |\n| --- |\n| $x_i$ |')
        self.assertIn('<table>', html)
        self.assertIn('math-expression', html)
        html = render_markdown('$x < y$')
        self.assertIn('x &lt; y', html)

if __name__ == '__main__':
    unittest.main()
