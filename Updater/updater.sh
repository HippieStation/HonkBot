#!/usr/bin/env bash
set -e

WORK_DIR=$(mktemp -d)
CONFIG_DIR=$(mktemp -d)
SECRET_DIR=$(mktemp -d)

SERVER_DIR="/home/byond/HippieServer"

export GIT_COMMITTER_EMAIL=HonkBot@users.noreply.github.com

mkdir -p "$SERVER_DIR/update/"
mkdir -p "$SERVER_DIR/.git/logs"

echo "Working folder: $WORK_DIR"
echo "Config folder: $CONFIG_DIR"
echo "Server folder: $SERVER_DIR"

git clone git@github.com:HippieStation/HippieStation13.git --depth=1 "$WORK_DIR"
git clone git@github.com:JamieH/HippieConfigs.git --depth=1 "$CONFIG_DIR"
git clone git@github.com:JamieH/HippieSecrets.git --depth=1 "$SECRET_DIR"

cd "$WORK_DIR"

python tools/ss13_genchangelog.py html/changelog.html html/changelogs

sed -i 's/visibility = 0/visibility = 1/g' "$WORK_DIR/code/world.dm"

DreamMaker tgstation.dme
if [ "$1" == "push" ]; then
        echo "Pushing changelogs"
        git add -u html/changelog.html
        git add -u html/changelogs
        git commit -m "Automatic changelog compile, [ci skip]"
        git push
fi

rm -Rf "$SERVER_DIR/_maps"
rm -Rf "$SERVER_DIR/html"
rm -Rf "$SERVER_DIR/sound"
rm -Rf "$SERVER_DIR/code"
#rm -Rf "$SERVER_DIR/css"
rm -Rf "$SERVER_DIR/config"

cp -R _maps/ "$SERVER_DIR/"
cp -R html/ "$SERVER_DIR/"
cp -R sound/ "$SERVER_DIR/"
cp -R code/ "$SERVER_DIR/"
#cp -R css/ "$SERVER_DIR/"
cp -R "$CONFIG_DIR" "$SERVER_DIR/config"

sed -i 's/\[RevisionHash\]/revisionhash/g' "$SERVER_DIR/config/motd.txt"
sed -i 's/\[DiscordHost\]/http:\/\/ipaddr:port\/discord/g' "$SERVER_DIR/config/config.txt"
sed -i 's/\[DiscordPassword\]/UQGwhh7HbZjYzEUQrKYCgMwq/g' "$SERVER_DIR/config/config.txt"
sed -i 's/\[SQLHost\]/host/g' "$SERVER_DIR/config/dbconfig.txt"
sed -i 's/\[SQLDatabase\]/db/g' "$SERVER_DIR/config/dbconfig.txt"
sed -i 's/\[SQLUsername\]/username/g' "$SERVER_DIR/config/dbconfig.txt"
sed -i 's/\[SQLPassword\]/password/g' "$SERVER_DIR/config/dbconfig.txt"

cp .git/logs/HEAD "$SERVER_DIR/.git/logs/HEAD"
cp tgstation.dmb tgstation.rsc "$SERVER_DIR/update/"

rm -Rf "$WORK_DIR"
rm -Rf "$CONFIG_DIR"
rm -Rf "$SECRET_DIR"