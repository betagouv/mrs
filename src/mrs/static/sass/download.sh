#!/bin/bash -eux

declare -A FONTS
FONTS[faustina]='Faustina'
FONTS[barlowcondensed]='Barlow+Condensed'
FONTS[barlow]='Barlow:100,100i,200,200i,300,300i,400,400i,500,500i,600,600i,700,700i,800,800i,900,900i'

for name in "${!FONTS[@]}"; do
    curl "https://fonts.googleapis.com/css?family=${FONTS[$name]}" > ${name}.css
    cat ${name}.css | grep -o 'http.*ttf' | xargs wget
    sed -i 's@http.*/\([^)]*\)@\1@' ${name}.css
done
