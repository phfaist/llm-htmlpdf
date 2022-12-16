import fs from 'fs';

import { runmathjax } from './runmathjax.js';

let in_content = null;
try {
    in_content = fs.readFileSync(0).toString('utf-8')
} catch (err) {
    console.error("Cannot read input!");
    throw err;
}

const indata = JSON.parse(in_content);


async function do_run(indata)
{
    const result_output = await runmathjax(indata);
    process.stdout.write( result_output );
}



do_run(indata).then( () => {
    //console.error('Done.');
} ).catch( (err) => {
    console.error('ERROR!', err);
} );


