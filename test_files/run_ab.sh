#!/bin/bash
PORT=$1
URL=$2
if [ -z "$URL" ]; then
  URL='/items/'
fi

# pre-warming app
ab -q -n 1000 -c 100 -T 'application/json' -prequestbody http://127.0.0.1:"$PORT""$URL" >/dev/null

# test
for i in $(seq 3); do
  echo "Test $i"
  ab -q -n 10000 -c 100 -T 'application/json' -prequestbody http://127.0.0.1:"$PORT""$URL" | grep -e 'Requests per second' -e 'Time per request' -e "Failed requests" | grep -e '(mean)' -e "Failed"
done
