#!/bin/sh

echo_usage() {
    echo "Usage: deploy.sh (testconference|conference)"
}

if [ $# -ne 1 ]; then
    echo_usage
    exit
fi

case $1 in
    testconference | conference )
        chmod -R go+rX accuconf*
        rsync -rav --delete  --exclude=__pycache__/ --exclude=accuconf/static accuconf accuconf_config.py accuconf.wsgi cli.sh scripts conference@dennis.accu.org:/srv/$1.accu.org/public/htdocs/
        ;;
    *)
        echo_usage
        ;;
esac
