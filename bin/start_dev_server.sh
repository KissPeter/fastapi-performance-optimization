#!/usr/bin/env bash
# https://jekyllrb.com/docs/
# wget https://curl.haxx.se/ca/cacert.pem --no-check-certificate
export SSL_CERT_FILE=$(pwd)/cacert.pem
bundle exec jekyll serve --livereload --trace --incremental