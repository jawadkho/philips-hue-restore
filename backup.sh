hubip=$1; shift
username=$1; shift

backupdir=hue_backup
basepath=https://$hubip/api/$username

mkdir -p ./$backupdir ./$backupdir/groups ./$backupdir/scenes

p=config;curl $basepath/$p -k | jq . > $backupdir/$p.json
p=lights;curl $basepath/$p -k | jq . > $backupdir/$p.json
p=rules;curl $basepath/$p -k | jq . > $backupdir/$p.json
p=groups;curl $basepath/$p -k | jq . > $backupdir/$p.json
p=scenes;curl $basepath/$p -k | jq . > $backupdir/$p.json
p=schedules;curl $basepath/$p -k | jq . > $backupdir/$p.json
p=sensors;curl $basepath/$p -k | jq . > $backupdir/$p.json

<$backupdir/groups.json jq 'keys[]' -r | while read id; do curl $basepath/groups/$id -k | jq . > $backupdir/groups/$id.json; done;
<$backupdir/scenes.json jq 'keys[]' -r | while read id; do curl $basepath/scenes/$id -k | jq . > $backupdir/scenes/$id.json; done;
