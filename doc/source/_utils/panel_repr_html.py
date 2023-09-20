# Code provided by Marc Skov Madsen.
# https://discourse.holoviz.org/t/how-to-use-sphinx-gallery-with-panel/6035
#
# This code adds a _repr_html_() method to all Panel objects. _repr_html_() is
# called by shinx-gallery when using the default value for the
# capture_repr setting.
# See https://sphinx-gallery.github.io/dev/auto_examples/plot_3_capture_repr.html.
#
# To use this code, import this module into your conf.py file then call
# add_repr_html().
#
# Unfortunately, https://docs.bokeh.org/en/2.4.3/docs/reference/embed.html#bokeh.embed.file_html,
# which gets called by Panel objects to create html, indicates that callbacks won't
# work. See the suppress_callback_warning. This may be a misinterpretation on my part.
# Regardless, there is a way to render interactive controls in documentation as
# demonstrated on https://panel.holoviz.org/getting_started/build_app.html. It's just
# not clear how to do it with sphinx-gallery. This code is kept as a reference
# for future enhancements to the documentation.
from html import escape
from io import StringIO
from uuid import uuid4

import panel as pn
import param


class PanelReprHTML(param.Parameterized):
    max_height = param.Integer(1000, bounds=(0, None))
    embed = param.Boolean(True)

    def __init__(self, object):
        self._object = object

    def _get_html(self):
        out = StringIO()
        self._object.save(out, embed=self.embed)
        out.seek(0)
        return escape(out.read())

    def _repr_html_(self):
        html = self._get_html()
        uid = str(uuid4())
        return f"""
<script>
function resizeIframe(uid){{
    setTimeout(() => {{
        var iframe = document.getElementById(uid);
        iframe.width = iframe.contentWindow.document.body.scrollWidth + 400;
        iframe.height = Math.min(iframe.contentWindow.document.body.scrollHeight + 80, {self.max_height});
        console.log(iframe.height)
    }}, "100");

}}
</script>
<iframe id="{uid}" srcdoc='{html}' frameBorder='0' onload='resizeIframe("{uid}")'></iframe>
"""


def _repr_html_(self):
    return PanelReprHTML(self)._repr_html_()


def add_repr_html():
    pn.viewable.Viewable._repr_html_ = _repr_html_


PanelReprHTML.max_height = 1000
# add_repr_html()
