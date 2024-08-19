const { execFile } = require('child_process');
const path = require('path');
const os = require('os');

const pythonType = os.platform() === 'win32' ? 'python' : 'python3';

execFile(pythonType, [path.join(__dirname,'src' , 'app.py')], (error, stdout, stderr) => {
    if (error) {
        console.error(`Error executing command: ${error}`);
        return;
    }
    if (stdout) {
        console.log(stdout);
    }
    if (stderr) {
        console.error(stderr);
    }
});

// This file handles the command to run the server depending on the operating system