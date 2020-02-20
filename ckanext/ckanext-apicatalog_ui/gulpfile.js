const { src, dest, parallel } = require('gulp');

function fontAwesomeCss() {
    return src('./node_modules/@fortawesome/fontawesome-pro/css/*.css')
        .pipe(dest("ckanext/apicatalog_ui/fanstatic/font-awesome/css/"))
}

function fontAwesomeFonts() {
    return src('./node_modules/@fortawesome/fontawesome-pro/webfonts/*')
        .pipe(dest("ckanext/apicatalog_ui/fanstatic/font-awesome/webfonts/"))
}


exports.fontAwesomeCss = fontAwesomeCss;
exports.fontAwesomeFonts = fontAwesomeFonts;

exports.default = parallel(fontAwesomeCss, fontAwesomeFonts);