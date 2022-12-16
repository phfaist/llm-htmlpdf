import os.path
import json
import shutil
import tempfile
import base64
import logging
logger = logging.getLogger(__name__)

import subprocess

#import weasyprint
#import pdfkit
#import pyhtml2pdf.converter

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
# from selenium.common.exceptions import TimeoutException
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support.expected_conditions import staleness_of
# from selenium.webdriver.common.by import By



from llm.fragmentrenderer.html import HtmlFragmentRenderer
from llm.runmain import RenderWorkflow, HtmlMinimalDocumentPostprocessor


#default_runmathjaxjs = os.path.join(os.path.dirname(__file__), '..', 'node_src', 'runmathjax.js')
default_runmathjaxjs = os.path.join(os.path.dirname(__file__), 'runmathjax_dist.js')


class HtmlMjxMathFragmentRenderer(HtmlFragmentRenderer):

    nodejs = shutil.which('node')
    runmathjaxjs = default_runmathjaxjs

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

        if self.nodejs is None or not self.nodejs:
            raise ValueError(
                "Cannot find node, please place the 'node' executable in your $PATH "
                "or set nodejs= to its full location path in the config as "
                "llm: { 'fragmentrenderer': { 'llmhtmlpdf.Workflow': { 'nodejs': ... }}}"
            )

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



#
# inspired by
# https://github.com/kumaF/pyhtml2pdf/blob/master/pyhtml2pdf/converter.py .
#
# Thanks!
#
def selenium_convert_html_to_pdf(input_path):

    settings = {
        "appState": {
            "recentDestinations": [{
                "id": "Save as PDF",
                "origin": "local"
            }],
            "selectedDestinationId": "Save as PDF",
            "version": 2
        },
        "images": 2,
    }

    prefs = {'printing.print_preview_sticky_settings': json.dumps(settings)}

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option('prefs', prefs)

    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")

    chrome_options.add_argument('--enable-print-browser')
    chrome_options.add_argument('--kiosk-printing')

    driver = webdriver.Chrome(
        ChromeDriverManager().install(),
        options=chrome_options
    )

    driver.get(f"file://{input_path}")

    # ## Waiting doesn't seem necessary, as we don't have dynamic JS in our
    # ## automatically generated pages
    #
    # try:
    #     timeout = 10 # max. 10 seconds
    #     WebDriverWait(driver, timeout).until(
    #         staleness_of(driver.find_element(by=By.TAG_NAME, value="html"))
    #     )
    # except TimeoutException:
    #     pass

    #driver.execute_script('window.print();')

    final_print_options = {
        "landscape": False,
        "displayHeaderFooter": False,
        "printBackground": True,
        "preferCSSPageSize": True,
    }
    #final_print_options.update(print_options)

    print_pdf_url = f"{driver.command_executor._url}/session/{driver.session_id}/chromium/send_command_and_get_result"
    print_pdf_body = json.dumps({"cmd": "Page.printToPDF", "params": final_print_options})
    print_pdf_response = driver.command_executor._request("POST", print_pdf_url, print_pdf_body)
    if not print_pdf_response:
        raise RuntimeError(print_pdf_response.get("value"))

    result_data = print_pdf_response.get("value")

    result_pdf = base64.b64decode(result_data['data'])

    driver.quit()

    return result_pdf


default_page_options = {
    'size': 'A4',
    'margin': {
        'top': '1in',
        'right': '1in',
        'bottom': '1in',
        'left': '1in'
    }
}


class Workflow(RenderWorkflow):

    binary_output = True

    # pdfkit_options = {
    #     'page-size': 'A4',
    #     'margin-top': '1in',
    #     'margin-right': '1in',
    #     'margin-bottom': '1in',
    #     'margin-left': '1in',
    #     'encoding': "UTF-8",
    # }

    render_header = True

    page_options = {}

    def get_fragment_renderer_class(self):
        return HtmlMjxMathFragmentRenderer

    def postprocess_rendered_document(self, rendered_content, document, render_context):

        # minimal HTML document & style -- TODO

        page_options = dict(default_page_options)
        if self.page_options:
            page_options.update(self.page_options)

        logger.debug("Using page_options = %r", page_options)

        def mk_page_css():
            s = "@page { "
            s += f"size: {page_options['size']}; "
            margin_opts = page_options['margin']
            if isinstance(margin_opts, str):
                s += f"margin: {margin_opts}; "
            else:
                for margin_which, margin_value in margin_opts.items():
                    s += f"margin-{margin_which}: {margin_value}; "
            s += "}\n"
            logger.debug("page CSS is -> %s", s)
            return s

        xtra_css = ""

        xtra_css += mk_page_css()

        xtra_css += _extra_css

        if hasattr(render_context, '_mathjax_css'):
            xtra_css += '\n' + render_context._mathjax_css

        html_postprocessor_config = {
            'html': { 'extra_css': xtra_css, },
            **self.config
        }

        pp = HtmlMinimalDocumentPostprocessor(document, render_context,
                                              html_postprocessor_config)

        html = pp.postprocess(rendered_content)

        # with open('test-intermediate.html', 'w') as fw:
        #     fw.write(html)

        logger.debug('Full HTML:\n\n%s\n\n', html)

        # convert result to PDF

        # --------

        #result_pdf = weasyprint.HTML(string=html).write_pdf()

        # ----

        # with tempfile.TemporaryDirectory() as tempdirname:
        #     pdffname = os.path.join(tempdirname, 'result.pdf')
        #     pdfkit.from_string(html, pdffname,
        #                        options=self.pdfkit_options,
        #                        verbose=logger.isEnabledFor(logging.DEBUG),)
        #     with open(pdffname, 'rb') as f:
        #         result_pdf = f.read()

        # ----

        with tempfile.TemporaryDirectory() as tempdirname:
            htmlfname = os.path.join(tempdirname, 'inpage.html')
            #pdffname = os.path.join(tempdirname, 'result.pdf')
            with open(htmlfname, 'w') as fw:
                fw.write(html)
            result_pdf = selenium_convert_html_to_pdf(
                htmlfname,
            )

        # --------

        return result_pdf
            
            


_extra_css = r"""
/* can add extra hard-coded CSS here */
"""
