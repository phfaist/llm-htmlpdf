

const {mathjax} = require('mathjax-full/js/mathjax.js');
const {TeX} = require('mathjax-full/js/input/tex.js');
const {SVG} = require('mathjax-full/js/output/svg.js');
const {liteAdaptor} = require('mathjax-full/js/adaptors/liteAdaptor.js');
const {RegisterHTMLHandler} = require('mathjax-full/js/handlers/html.js');
//const {AssistiveMmlHandler} = require('mathjax-full/js/a11y/assistive-mml.js');

const {AllPackages} = require('mathjax-full/js/input/tex/AllPackages.js');


async function runmathjax(indata)
{
    //
    // Load MathJaX -- manual components loading
    //
    const packages = AllPackages.slice();

    const adaptor = liteAdaptor();
    const handler = RegisterHTMLHandler(adaptor);

    const tex = new TeX({packages: packages});
    const svg = new SVG({fontCache: 'local'});
    const html = mathjax.document('', {InputJax: tex, OutputJax: svg});

    const css_data = adaptor.textContent(svg.styleSheet(html));

    //
    //  Typeset and display the math
    //
    let output_data = {
        css: css_data,
        svg_list: [],
    };

    for (const input of indata.math_list) {

        const node = html.convert(input.tex, {
            display: (input.displaytype === 'inline' ? false : true),
            em: 16,
            ex: 8,
            containerWidth: 600,
        });

        const result_svg = adaptor.outerHTML(node);
        
        // const svg = await MathJax.tex2svgPromise(input.tex, {
        //     display: (input.displaytype === 'inline' ? false : true),
        //     em: 16,
        //     ex: 8,
        //     containerWidth: 600,
        // });

        // // console.log('SVG IS:\n', svg);
        // // console.log('INNER HTML IS:\n', adaptor.innerHTML(svg));
        // const result_svg = adaptor.outerHTML(svg);

        //output_data.svg_list.push( adaptor.innerHTML(svg) );
        output_data.svg_list.push( result_svg );
    }

    return JSON.stringify(output_data);
};


module.exports = {
    runmathjax,
};
