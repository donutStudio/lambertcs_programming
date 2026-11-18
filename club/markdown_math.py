"""Markdown with math protected from Markdown escaping and emphasis parsing."""
import xml.etree.ElementTree as etree
import markdown
from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor


class MathProcessor(InlineProcessor):
    def handleMatch(self, match, data):
        node = etree.Element('span')
        node.set('class', 'math-expression')
        raw = match.group(0)
        display = raw.startswith('$$') or raw.startswith('\\[')
        delimiter_length = 2 if display or raw.startswith('\\(') else 1
        expression = raw[delimiter_length:-delimiter_length]
        node.set('data-math', expression)
        node.set('data-display', 'true' if display else 'false')
        # Preserve readable source if the rendering CDN is unavailable.
        from markdown.util import AtomicString
        node.text = AtomicString(raw)
        return node, match.start(0), match.end(0)


class MathExtension(Extension):
    def extendMarkdown(self, md):
        pattern = r'(?s)(?<!\\)(?:\$\$.+?\$\$|\\\[.+?\\\]|\\\(.+?\\\)|\$(?!\$)[^\n$]+?(?<!\\)\$(?!\$))'
        # Code spans (190) are protected first; math precedes escapes/emphasis.
        md.inlinePatterns.register(MathProcessor(pattern, md), 'math', 185)


def render_markdown(source):
    return markdown.markdown(source, extensions=['fenced_code', 'tables', MathExtension()])
