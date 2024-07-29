const { src, dest, parallel } = require('gulp');
const fs = require('fs');
const rename = require('gulp-rename')

let fontawesomePath = './node_modules/@fortawesome/fontawesome-pro';
if (!fs.existsSync('./node_modules/@fortawesome/fontawesome-pro')){
    fontawesomePath = './node_modules/@fortawesome/fontawesome-free'
}

function fontAwesomeCss() {
    return src(fontawesomePath + '/css/*.css')
        .pipe(dest("ckanext/apicatalog/public/fonts/font-awesome/css/"))
}

function fontAwesomeFonts() {
    return src(fontawesomePath + '/webfonts/*', {encoding:false})
        .pipe(dest("ckanext/apicatalog/public/fonts/font-awesome/webfonts/"))
}

const bootstrapDatepickerPath = './node_modules/eonasdan-bootstrap-datetimepicker/'

function bootstrapDatepickerJs() {
    return src(bootstrapDatepickerPath + 'src/js/bootstrap-datetimepicker.js')
        .pipe(dest("ckanext/apicatalog/fanstatic/datetimepicker/"))
  
}
function bootstrapDatepickerCss() {
    return src(bootstrapDatepickerPath + 'build/css/bootstrap-datetimepicker.css')
        .pipe(dest("ckanext/apicatalog/fanstatic/datetimepicker/"))
  
}

const bootstrapLessPath = './node_modules/bootstrap/less';
function bootstrapLess() {
    return src(bootstrapLessPath + '/**/*')
        .pipe(dest("vendor/bootstrap/less"))
}

exports.fontAwesomeCss = fontAwesomeCss;
exports.fontAwesomeFonts = fontAwesomeFonts;
exports.bootstrapDatepickerJs = bootstrapDatepickerJs;
exports.bootstrapDatepickerCss = bootstrapDatepickerCss;
exports.bootstrapLess = bootstrapLess;

exports.default = parallel(
  fontAwesomeCss, fontAwesomeFonts,
  bootstrapDatepickerJs, bootstrapDatepickerCss,
  bootstrapLess
);
