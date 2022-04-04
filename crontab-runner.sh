#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

PID="$(pgrep -f 'python3 main.py')"
echo $PID
if [[ "$PID" -ne "" ]]; then
	echo MATCH
	kill -9 $PID
fi

python3 main.py &
