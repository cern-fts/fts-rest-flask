#!/bin/sh
NC='\033[0m' # No Color

INFO () {
    BLUE='\033[0;34m'; 
    echo -e "${BLUE}$1${NC}";
}

OK () {
    GREEN='\033[0;32m' 
    echo -e "${GREEN}$1${NC}";
}

FAIL () {
    RED='\033[0;31m' 
    echo -e "${RED}$1${NC}";
}

WARN () {
    YELLOW='\033[0;33m' 
    echo -e "${YELLOW}$1${NC}";
}


for file in $FILES
do
    radon_output="$(radon cc --min E --show-complexity $file)"
    if [ $exit_code -ne 0 ]
    then 
        FAIL "radon exited with an error"
        exit 1
    fi
    if [[ "${radon_output// }" ]] # ignore whitespace (the last //)
    then
        echo -e "$radon_output"
        FAIL "radon detected files with a very high Cyclomatic Complexity"
        exit 1
    fi
done

INFO "Running radon     (checking Maintainability Index)"
for file in $FILES
do
    radon_output="$(radon mi --min B $file)"
    if [ $exit_code -ne 0 ]
    then 
        FAIL "radon exited with an error"
        exit 1
    fi
    if [[ "${radon_output// }" ]]
    then
        echo -e "$radon_output"
        FAIL "radon detected files with a very low Maintainability Index"
        exit 1
    fi
done
}