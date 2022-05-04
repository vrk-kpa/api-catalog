fswatch -o less | xargs -n1 -I{} ./buildless.sh &
browser-sync start --https --proxy "https://10.100.10.10" --files "ckanext/apicatalog/fanstatic/apicatalog/main.css" &
