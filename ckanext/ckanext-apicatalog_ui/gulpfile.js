const { src, dest, parallel } = require('gulp');
const fs = require('fs');

let fontawesomePath = './node_modules/@fortawesome/fontawesome-pro';
if (!fs.existsSync('./node_modules/@fortawesome/fontawesome-pro')){
    fontawesomePath = './node_modules/@fortawesome/fontawesome-free'
}

function fontAwesomeCss() {
    return src(fontawesomePath + '/css/*.css')
        .pipe(dest("ckanext/apicatalog_ui/fanstatic/font-awesome/css/"))
}

function fontAwesomeFonts() {
    return src(fontawesomePath + '/webfonts/*')
        .pipe(dest("ckanext/apicatalog_ui/fanstatic/font-awesome/webfonts/"))
}


exports.fontAwesomeCss = fontAwesomeCss;
exports.fontAwesomeFonts = fontAwesomeFonts;

exports.default = parallel(fontAwesomeCss, fontAwesomeFonts);