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

const bootstrapDatepickerPath = './node_modules/eonasdan-bootstrap-datetimepicker/'

function bootstrapDatepickerJs() {
    return src(bootstrapDatepickerPath + 'src/js/bootstrap-datetimepicker.js')
        .pipe(dest("ckanext/apicatalog_ui/fanstatic/datetimepicker/"))
  
}
function bootstrapDatepickerCss() {
    return src(bootstrapDatepickerPath + 'build/css/bootstrap-datetimepicker.css')
        .pipe(dest("ckanext/apicatalog_ui/fanstatic/datetimepicker/"))
  
}

const momentPath = './node_modules/moment/'

function momentJs() {
    return src(momentPath + 'src/moment.js')
        .pipe(dest("ckanext/apicatalog_ui/fanstatic/datetimepicker/"))
  
}

exports.fontAwesomeCss = fontAwesomeCss;
exports.fontAwesomeFonts = fontAwesomeFonts;
exports.cookieConsentJs = cookieConsentJs;
exports.cookieConsentCss = cookieConsentCss;
exports.bootstrapDatepickerJs = bootstrapDatepickerJs;
exports.bootstrapDatepickerCss = bootstrapDatepickerCss;
exports.momentJs = momentJs;

exports.default = parallel(
  fontAwesomeCss, fontAwesomeFonts,
  cookieConsentJs, cookieConsentCss,
  bootstrapDatepickerJs, bootstrapDatepickerCss,
  momentJs
);
