#!/bin/bash
set -Eeuo pipefail

# First argument is the path to the sample app directory
TOP_DIR=$1
if [ -z "$TOP_DIR" ]; then
  echo "First argument must be the path to the dir in which to work"
  exit 1
fi

(
  cd "$TOP_DIR"
  # Find all *.gradle files
  find . -name "*.gradle" | while read file; do
    echo "Processing $file"
    # Find any occurences of 'System.env.<property> as int', and replace with the
    # value of the environment variable <property>
    (grep -o 'System\.env\.[a-zA-Z0-9_]\+\( as int\)' "$file" || true) | while read match; do
      property=${match#System.env.}
      property=${property%% as int}
      value=$(printenv "$property")
      if [ -n "$value" ]; then
        echo "Replacing $match with $value"
        sed -i "s|$match|$value|g" "$file"
      fi
    done
    # Find any occurences of 'System.env.<property>', and replace with the
    # value of the environment variable <property> in quotes
    (grep -o 'System\.env\.[a-zA-Z0-9_]\+' "$file" || true) | while read match; do
      property=${match#System.env.}
      value=$(printenv "$property")
      if [ -n "$value" ]; then
        echo "Replacing $match with \"$value\""
        sed -i "s|$match|\"$value\"|g" "$file"
      fi
    done
  done
)
