from django.forms import fields, forms

from formset.richtext import controls
from formset.richtext.widgets import RichTextarea


initial_html = """
<p>
 Lorem ipsum dolor sit amet, consectetur adipisici elit, sed eiusmod tempor incidunt ut labore et dolore magna aliqua.
 <strong>Petierunt uti sibi concilium totius Galliae in diem certam indicere. </strong>
 <em>Excepteur sint obcaecat cupiditat non proident culpa. </em>
</p>
"""


class AdvertisementForm(forms.Form):
    text = fields.CharField(
        widget=RichTextarea(control_elements=[
            controls.Heading([1,2,3]),
            controls.Bold(),
            controls.Blockquote(),
            controls.CodeBlock(),
            controls.HardBreak(),
            controls.Italic(),
            controls.Underline(),
            #controls.TextColor(['rgb(212, 0, 0)', 'rgb(0, 212, 0)', 'rgb(0, 0, 212)']),
            controls.TextColor(['text-red', 'text-green', 'text-blue']),
            controls.TextIndent(),
            controls.TextIndent('outdent'),
            controls.TextMargin('increase'),
            controls.TextMargin('decrease'),
            controls.Link(),
            controls.TextAlign(['left', 'center', 'right']),
            controls.HorizontalRule(),
            controls.Subscript(),
            controls.Superscript(),
            controls.Placeholder(),
            controls.Separator(),
            controls.ClearFormat(),
            controls.Redo(),
            controls.Undo(),
        ], attrs={'placeholder': "Start typing …"}),
    )
