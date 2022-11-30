import os.path
import tempfile
import logging
logger = logging.getLogger(__name__)

import weasyprint

from llm.fragmentrenderer.html import HtmlFragmentRenderer
from llm.runmain import RenderWorkflow, HtmlMinimalDocumentPostprocessor


class Workflow(RenderWorkflow):

    binary_output = True

    def get_fragment_renderer_class(self):
        return HtmlFragmentRenderer

    def postprocess_rendered_document(self, rendered_content, document, render_context):

        # minimal HTML document & style -- TODO

        # make weasyprint a little quieter
        logging.getLogger('fontTools').setLevel(logging.WARNING)

        pp = HtmlMinimalDocumentPostprocessor(document, render_context)
        html = pp.postprocess(rendered_content, {
            'html': { 'extra_css': _extra_css, },
        })

        logger.debug('Full HTML:\n\n%s\n\n', html)

        # convert result to PDF
        result_pdf = weasyprint.HTML(string=html).write_pdf()

        return result_pdf
            
            


_extra_css = r"""
html, body {
  font-family: 'Roboto', sans-serif;
}
"""
