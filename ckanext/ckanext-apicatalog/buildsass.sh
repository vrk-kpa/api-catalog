sass scss/main.scss  --source-map=ckanext/apicatalog/public/base/main.css.map --source-map-url=/base/main.css.map --source-map-less-inline > ckanext/apicatalog/fanstatic/apicatalog/main.css
sass scss/openapi_view.scss  --source-map=ckanext/apicatalog/public/base/openapi_view.css.map --source-map-url=/base/openapi_view.css.map --source-map-less-inline > ckanext/apicatalog/fanstatic/openapi_view.css
echo $(date): Compiled sass
