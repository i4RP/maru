#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export PYTHONPATH="$DIR/../Resources/lib/python3.12/site-packages:$PYTHONPATH"
python3 "$DIR/financial_analyzer_app.py"
