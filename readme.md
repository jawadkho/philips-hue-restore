# Philips Hue semi-restore tool

This tool will restore groups and scenes. Lights must be setup. It assumes that lights are all the same (using their `uniqueid` to identitfy them). It has been tested after a clean up of the Hub via the Android Philips Hue app. Currently this will only restore some groups and most group scenes. Note: groups must not exist already – doing a clean up via the app will not delete exisiting groups, you must do this yourself.

## Why

I couldn't connect Philips Hue to my Google Home ;( – Philips support suggested 'clean up' via the app which worked! However, I didn't want to lose all my scenes so I wrote this little restore utility. Feel free to extend as you wish but please do make it open source!

## Requirements

Python 3.7

`pip install requests`

Tested with Hue API `1.32.0`, swversion `1932073040` (source: https://192.168.0.10/api/config)

## Steps to use

1. Create a backup using `./backup.sh <hubip> <username>`. Requires curl and jq.
   1. This stores the files under the api paths starting from after `api/<username>/...`. E.g. `api/<username>/scenes/abcd` stored under `<backup_dir>/scenes/abcd.json`. `api/<username>/groups` -> `<backup_dir>/groups.json`
2. This app will require a [Hub username or api key](https://developers.meethue.com/develop/get-started-2/) and the [hub local ip](https://developers.meethue.com/develop/application-design-guidance/hue-bridge-discovery/). (Login required for links)
   1. Paste in the details in `restore.py` at the bottom.
3. Run `python restore.py`
4. Hopefully thats it!
