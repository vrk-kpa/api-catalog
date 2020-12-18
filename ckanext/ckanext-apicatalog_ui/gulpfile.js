const { src, dest, parallel } = require('gulp');
const fs = require('fs');
const rename = require('gulp-rename')

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

const cookieConsentPath = './node_modules/cookieconsent/'

function cookieConsentJs() {
    return src(cookieConsentPath + 'src/cookieconsent.js')
        .pipe(dest("ckanext/apicatalog_ui/fanstatic/cookieconsent/"))
}

function cookieConsentCss() {
    return src(cookieConsentPath + 'build/cookieconsent.min.css')
        .pipe(rename((path) => {
            path.basename = path.basename.replace(".min", "")
        }))
        .pipe(dest("ckanext/apicatalog_ui/fanstatic/cookieconsent/"))
}

const bootstrapLessPath = './node_modules/bootstrap/less';
function bootstrapLess() {
    return src(bootstrapLessPath + '/**/*')
        .pipe(dest("vendor/bootstrap/less"))
}

exports.fontAwesomeCss = fontAwesomeCss;
exports.fontAwesomeFonts = fontAwesomeFonts;
exports.cookieConsentJs = cookieConsentJs;
exports.cookieConsentCss = cookieConsentCss;
exports.bootstrapLess = bootstrapLess;

exports.default = parallel(fontAwesomeCss, fontAwesomeFonts, cookieConsentJs, cookieConsentCss, bootstrapLess);