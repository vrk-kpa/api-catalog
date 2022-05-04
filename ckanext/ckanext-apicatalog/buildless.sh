lessc less/main.less  --source-map=ckanext/apicatalog/public/base/main.css.map --source-map-url=/base/main.css.map --source-map-less-inline > ckanext/apicatalog/fanstatic/apicatalog/main.css
lessc less/openapi_view.less  --source-map=ckanext/apicatalog/public/base/openapi_view.css.map --source-map-url=/base/openapi_view.css.map --source-map-less-inline > ckanext/apicatalog/fanstatic/openapi_view.css
echo $(date): Compiled LESS
