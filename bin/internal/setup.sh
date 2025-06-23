#!/bin/bash

function HTTK_PROJECT_CFG() {
    CATEGORY=$1
    KEY=$2
    awk -F "=" "/\[$CATEGORY\]/ {cat=1}
         cat==1 && /^ *$KEY *=/ {print \$2; exit}
        " "$HTTK_PROJECT_DIR/ht.project/config"
}

if [ ! -e ~/".httk/config" ]; then
    echo "You appear to not have setup your user information with httk."
    echo "Do you want to do that now? [Y/N] (you cannot continue if you answer N)"
    read YESNO
    echo ""
    if [ "$YESNO" != "y" -a "$YESNO" != "Y" -a "$YESNO" != "yes" -a "$YESNO" != "YES" ]; then
	echo "User cancelled. Nothing done."
	exit 1
    fi
    DIRNAME=$(dirname "$0")
    HTTK_BIN_PATH=$(cd "$DIRNAME"; pwd -P)
    "${HTTK_BIN_PATH}/httk-setup"
fi

HTTK_USER_HOME=~/.httk/
mkdir -p "$HTTK_USER_HOME"
mkdir -p "$HTTK_USER_HOME/tasks"
mkdir -p "$HTTK_USER_HOME/computers"
mkdir -p "$HTTK_USER_HOME/keys"

HTTK_PROJECT_DIR=$(
    DIR=""
    while [ "$DIR" != "/" ]; do
    DIR="$(pwd -P)"
    if [ -e ht.project ]; then
	echo "$DIR"
	exit 0
    fi
    cd ..
done
exit 1
)

HTTK_REL_DIR=$(
    DIR=""
    RELPATH="./"
    while [ "$DIR" != "/" ]; do
    DIR="$(pwd -P)"
    if [ -e ht.project ]; then
	echo "$RELPATH"
	exit 0
    fi
    BASENAME=$(basename "$DIR")
    RELPATH="${RELPATH}${BASENAME}/"
    cd ..
done
exit 1
)

if [ -n "$HTTK_PROJECT_DIR" ]; then
    HTTK_PROJECT_DIR_NAME=$(basename "$HTTK_PROJECT_DIR")
    HTTK_PROJECT_NAME=$(HTTK_PROJECT_CFG "main" "project_name")
fi
