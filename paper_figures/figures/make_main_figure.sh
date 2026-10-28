#!/bin/zsh
# Render figures/main_figure.html to a vector PDF (figures/main_figure.pdf) with headless Chrome, then crop.
cd "$(dirname $0)"
"${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}" --headless=new --disable-gpu --no-pdf-header-footer \
  --print-to-pdf=main_figure_raw.pdf "file://$PWD/main_figure.html" 2>/dev/null
pdfcrop --margins 2 main_figure_raw.pdf main_figure.pdf >/dev/null && rm -f main_figure_raw.pdf
