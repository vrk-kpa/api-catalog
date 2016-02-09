#!/bin/bash

# A script for checking if there are forms that need csrf handling

HELPTEXT="Usage: $0 [whitelist file]\n\n\
Finds HTML files with forms without mentions of CSRF tokens.\n\
Run at the root of the directory tree to scan. To exclude already cleared files from the results provide a whitelist file.\n"

if [ $1 = "--help" ]; then
  echo -e $HELPTEXT
else
  grep --include "*.html" -Rli "<form" . \
    | xargs grep -Li "csrf_token" \
    | while read f; do 
      if [ ! -z $1 ]; then
        if ! grep -xq "$f" $1; then 
          echo $f; 
        fi; 
      else
        echo $f; 
      fi
    done;
fi
