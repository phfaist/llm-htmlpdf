import os.path
import json
import shutil
import tempfile
import logging
logger = logging.getLogger(__name__)

import subprocess

#import weasyprint
import pdfkit

from llm.fragmentrenderer.html import HtmlFragmentRenderer
from llm.runmain import RenderWorkflow, HtmlMinimalDocumentPostprocessor


class HtmlKlfMathFragmentRenderer(HtmlFragmentRenderer):

    nodejs = shutil.which('node')
    runmathjaxjs = os.path.join(os.path.dirname(__file__), '..', 'runmathjax.js')

    mathjax_id_offset = 1

    def get_html_js(self):
        return '' # no MathJax needed in HTML page

    def get_html_body_end_js_scripts(self):
        return '' # no MathJax needed in HTML page


    def render_math_content(self,
                            delimiters,
                            nodelist,
                            render_context,
                            displaytype,
                            environmentname=None,
                            target_id=None):

        if delimiters[0] in ('\\(', '\\[', '$', '$$'):
            # skip simple delimiters for nonnumbered equations
            tex = nodelist.latex_verbatim()
        else:
            tex = (
                delimiters[0]
                + nodelist.latex_verbatim()
                + delimiters[1]
            )

        self.mathjax_id_offset = self.mathjax_id_offset + 1

        indata = {
            'math_list': [
                {
                    'tex': tex,
                    'displaytype': displaytype,
                },
            ],
            'id_offset': self.mathjax_id_offset,
        }

        result = subprocess.check_output(
            [self.nodejs, '-r', 'esm', self.runmathjaxjs,],
            input=json.dumps(indata),
            encoding='utf-8',
        )

        outdata = json.loads(result)

        if not getattr(render_context, '_mathjax_css', None):
            render_context._mathjax_css = outdata['css']

        class_names = [ f"{displaytype}-math" ]
        if environmentname is not None:
            class_names.append(f"env-{environmentname.replace('*','-star')}")

        attrs = {}
        if target_id is not None:
            attrs['id'] = target_id

        content_html = outdata['svg_list'][0]

        if displaytype == 'display':
            # BlockLevelContent( # -- don't use blockcontent as display
            # equations might or might not be in their separate paragraph.
            return (
                self.wrap_in_tag(
                    'span',
                    content_html,
                    class_names=class_names,
                    attrs=attrs
                )
            )
        return self.wrap_in_tag(
            'span',
            content_html,
            class_names=class_names,
            attrs=attrs
        )





class Workflow(RenderWorkflow):

    binary_output = True

    pdfkit_options = {
        'page-size': 'A4',
        'margin-top': '1in',
        'margin-right': '1in',
        'margin-bottom': '1in',
        'margin-left': '1in',
        'encoding': "UTF-8",
    }

    def get_fragment_renderer_class(self):
        return HtmlKlfMathFragmentRenderer

    def postprocess_rendered_document(self, rendered_content, document, render_context):

        # minimal HTML document & style -- TODO

        # # make weasyprint a little quieter
        # logging.getLogger('fontTools').setLevel(logging.WARNING)

        xtra_css = _extra_css

        if hasattr(render_context, '_mathjax_css'):
            xtra_css += '\n' + render_context._mathjax_css

        pp = HtmlMinimalDocumentPostprocessor(document, render_context)
        html = pp.postprocess(rendered_content, {
            'html': { 'extra_css': xtra_css, },
        })

        # with open('test-intermediate.html', 'w') as fw:
        #     fw.write(html)

        logger.debug('Full HTML:\n\n%s\n\n', html)

        # convert result to PDF

        # --------

        #result_pdf = weasyprint.HTML(string=html).write_pdf()

        # ----

        with tempfile.TemporaryDirectory() as tempdirname:
            
            pdffname = os.path.join(tempdirname, 'result.pdf')

            pdfkit.from_string(html, pdffname,
                               options=self.pdfkit_options,
                               verbose=logger.isEnabledFor(logging.DEBUG),)

            with open(pdffname, 'rb') as f:
                result_pdf = f.read()

        # --------


        return result_pdf
            
            


_extra_css = r"""
html, body {
  font-size: 12pt;
  font-family: 'Source Serif Pro', 'Times New Roman', serif;
}

article {
  max-width: 100%;
  margin: 0px auto;
}

"""
