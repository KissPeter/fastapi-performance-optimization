#!/bin/bash
# pre-warming app
ab -q  -n 1000 -c 100 -T 'application/json' -prequestbody http://127.0.0.1:8000/items/ > /dev/null

# test
for i in `seq 3`
do
	echo "Test $i"
	ab -q  -n 10000 -c 100 -T 'application/json' -prequestbody http://127.0.0.1:8000/items/ | grep -e 'Requests per second' -e 'Time per request' | grep '(mean)'
done
