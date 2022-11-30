import fs from 'fs';
import * as mathjax from 'mathjax-full';
import yargs from 'yargs';

const indata = JSON.parse(fs.readFileSync(0).toString('utf-8'));

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
    const MathJax = await mathjax.init({
        //
        //  The MathJax configuration
        //
        loader: {
            source: {},
            load: [
                'adaptors/liteDOM',
                'tex-svg',
            ]
        },
        tex: {
            inlineMath: [ ['\\(', '\\)'] ],
            displayMath: [ ['\\[', '\\]'] ],
            processEnvironments: true,
            processRefs: true,

            // equation numbering on
            tags: 'ams',

            packages: {'[+]': ['base', 'autoload', 'ams', 'newcommand', 'braket',]},
        },
        // chtml: {
        //     fontURL: argv.fontURL
        // },
        svg: {
            fontCache: 'local',
            localID: ((indata.id_offset != null) ? indata.id_offset : null),
            titleID: ((indata.id_offset != null) ? indata.id_offset : 0),
        },
        startup: {
            typeset: false
        },
    });

    const adaptor = MathJax.startup.adaptor;

    //
    //  Typeset and display the math
    //
    let output_data = {
        css: adaptor.textContent(MathJax.svgStylesheet()),
        svg_list: [],
    };

    for (const input of indata.math_list) {

        const svg = await MathJax.tex2svgPromise(input.tex, {
            display: (input.displaytype === 'inline' ? false : true),
            em: 16,
            ex: 8,
            containerWidth: 600,
        });

        // console.log('SVG IS:\n', svg);
        // console.log('INNER HTML IS:\n', adaptor.innerHTML(svg));

        //output_data.svg_list.push( adaptor.innerHTML(svg) );
        output_data.svg_list.push( adaptor.outerHTML(svg) );
    }

    process.stdout.write( JSON.stringify(output_data) );
}

try {
    run()
} catch (err) {
    console.error('ERROR!', err);
}
