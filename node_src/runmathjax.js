import fs from 'fs';
//import yargs from 'yargs';

//import * as mathjax from 'mathjax-full';
const {mathjax} = require('mathjax-full/js/mathjax.js');
const {TeX} = require('mathjax-full/js/input/tex.js');
const {SVG} = require('mathjax-full/js/output/svg.js');
const {liteAdaptor} = require('mathjax-full/js/adaptors/liteAdaptor.js');
const {RegisterHTMLHandler} = require('mathjax-full/js/handlers/html.js');
//const {AssistiveMmlHandler} = require('mathjax-full/js/a11y/assistive-mml.js');

const {AllPackages} = require('mathjax-full/js/input/tex/AllPackages.js');


let in_content = null;
try {
    in_content = fs.readFileSync(0).toString('utf-8')
} catch (err) {
    console.error("Cannot read input!");
    throw err;
}

const indata = JSON.parse(in_content);

// const argv = yargs
//       .usage('Usage: runmathjax [options]  — Generate SVG for LaTeX formulas (JSON stdin)')
//       .option('displaytype', {
//           description: 'either "display" or "inline"',
//           type: 'string',
//           default: 'display'
//       })
//       .help()
//       .argv;


//console.log('indata = ', indata);

async function run() {

    //
    // load MathJax
    //
    // const MathJax = await mathjax.init({
    //     //
    //     //  The MathJax configuration
    //     //
    //     loader: {
    //         source: {},
    //         load: [
    //             'adaptors/liteDOM',
    //             'tex-svg',
    //         ]
    //     },
    //     tex: {
    //         inlineMath: [ ['\\(', '\\)'] ],
    //         displayMath: [ ['\\[', '\\]'] ],
    //         processEnvironments: true,
    //         processRefs: true,

    //         // equation numbering on
    //         tags: 'ams',

    //         packages: {'[+]': ['base', 'autoload', 'ams', 'newcommand', 'braket',]},
    //     },
    //     // chtml: {
    //     //     fontURL: argv.fontURL
    //     // },
    //     svg: {
    //         fontCache: 'local',
    //         localID: ((indata.id_offset != null) ? indata.id_offset : null),
    //         titleID: ((indata.id_offset != null) ? indata.id_offset : 0),
    //     },
    //     startup: {
    //         typeset: false
    //     },
    // });
    // const adaptor = MathJax.startup.adaptor;
    // const css_data = adaptor.textContent(MathJax.svgStylesheet()),

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

    process.stdout.write( JSON.stringify(output_data) );
}

try {
    run()
} catch (err) {
    console.error('ERROR!', err);
}
