fswatch -o less | xargs -n1 -I{} ./buildless.sh &
browser-sync start --proxy "10.100.10.10" --files "ckanext/apicatalog_ui/public/main.css" &

