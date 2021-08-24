lessc less/main.less  --source-map=ckanext/apicatalog_ui/public/base/main.css.map --source-map-url=/base/main.css.map --source-map-less-inline > ckanext/apicatalog_ui/fanstatic/apicatalog_ui/main.css
lessc less/openapi_view.less  --source-map=ckanext/apicatalog_ui/public/base/openapi_view.css.map --source-map-url=/base/openapi_view.css.map --source-map-less-inline > ckanext/apicatalog_ui/fanstatic/openapi_view.css
echo $(date): Compiled LESS
