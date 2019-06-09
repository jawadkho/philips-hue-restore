import json
import requests
import urllib3

# Disabled warnings because the Hub uses SSL but the vertificate cannot be verified.
urllib3.disable_warnings()


class HubBackup:
    def __init__(
        self,
        path
    ):
        self._path = path
        self._basepath = _strpslash(path)

    def lights(self):
        with open(f"{self._basepath}/lights.json") as f:
            return json.load(f)
    
    def groups(self):
        with open(f"{self._basepath}/groups.json") as f:
            return json.load(f)

    def scenes(self):
        with open(f"{self._basepath}/scenes.json") as f:
            scenes = json.load(f)

        scenes_detailed = {}
        for sceneid in scenes.keys():
            with open(f"{self._basepath}/scenes/{sceneid}.json") as f:
                scenes_detailed[sceneid] = json.load(f)

        return scenes_detailed

    def __repr__(self):
        return f'HubBackup({self._path})'

class Hub:
    def __init__(
        self,
        hub_ip, 
        username, 
        session=requests.Session()
    ):
        self.ip = _strpslash(hub_ip)
        self.username = username
        self._session = session
        self._session.verify = False
        self._basepath = f"{self.ip}/api/{self.username}"
    
    def lights(self):
        res = self._session.get(f"{self._basepath}/lights")
        res.raise_for_status()
        return res.json()
    
    def groups(self):
        res = self._session.get(f"{self._basepath}/groups")
        res.raise_for_status()
        return res.json()

    def scenes(self):
        res = self._session.get(f"{self._basepath}/scenes")
        res.raise_for_status()
        return res.json()

    def scene(self, id):
        res = self._session.get(f"{self._basepath}/scenes/{id}")
        res.raise_for_status()
        return res.json()

    def create_group(self, group: dict):
        res = self._session.post(f"{self._basepath}/groups", json=group)
        res.raise_for_status()
        res_json = res.json()
        if len(res_json) == 1 and 'success' in res_json[0]:
            print(res_json)
            return res_json[0]['success']['id']
        raise Exception(f'Failed to create group: {res_json}')
    
    def create_scene(self, scene: dict):
        res = self._session.post(f"{self._basepath}/scenes", json=scene)
        res.raise_for_status()
        res_json = res.json()
        if len(res_json) == 1 and 'success' in res_json[0]:
            return res_json
        raise Exception(f'Failed to create scene: {res_json} => {scene}')

    def set_scene(self, group_id, scene_name):
        res = self._session.put(f"{self._basepath}/groups/{group_id}/action", json={"scene":scene_name})
        res.raise_for_status()
        return res.text


def old_to_new_id_mapping(hub: Hub, backup: HubBackup) -> dict:
    lights = hub.lights()
    old_lights = backup.lights()

    new_light_ids = lights.keys()
    old_light_ids = old_lights.keys()

    uniqueid_new_id = {
        light_info['uniqueid']: new_id 
        for new_id, light_info in lights.items()
    }

    old_id_uniqueid = {
        old_id: light_info['uniqueid']
        for old_id, light_info in old_lights.items()
    }

    old_to_new_id = {
        old_id: uniqueid_new_id[uniqueid]
        for old_id, uniqueid in old_id_uniqueid.items()
        if uniqueid in uniqueid_new_id
    }

    return old_to_new_id

def recreate_groups(hub: Hub, backup: HubBackup, old_to_new_lights: dict):
    old_groups = backup.groups()
    old_to_new_group_ids = {}

    for old_group_id, old_group in old_groups.items():
        if old_group['type'] not in ['Room', 'Zone']:
            # Haven't tested others yet
            continue
        
        print(f"Creating group: {old_group['name']} {old_group['type']}")
        new_group_id = hub.create_group({
            'name': old_group['name'],
            'type': old_group['type'],
            'class': old_group['class'],
            'lights': [
                old_to_new_lights[id] 
                for id in old_group['lights']
            ]
        })

        old_to_new_group_ids[old_group_id] = new_group_id

    # 0 -> 0 -- special philips hue group
    old_to_new_group_ids['0'] = '0'

    return old_to_new_group_ids

def recreate_scenes(
    hub: Hub,
    backup: HubBackup,
    old_to_new_groups: dict, 
    old_to_new_lights: dict
):
    cur_scenes = hub.scenes()
    old_scenes = backup.scenes()

    existing_scenes = set((scene['name'], scene.get('group')) for scene in cur_scenes.values())

    for scene in old_scenes.values():
        new_group = old_to_new_groups.get(scene.get('group'))

        # type == GroupScene; Others don't work so well – just groups for now
        # not scene['recycle']; Don't want anything that'll be recycled – probably not ours
        # not scene['locked']; See docs
        # scene['appdata']; This is required by the hue app
        if (scene['name'], new_group) not in existing_scenes \
            and scene['type'] == 'GroupScene' \ 
            and not scene['recycle'] \
            and not scene['locked'] \ 
            and scene['appdata']: 
            print(f"Creating scene: {scene['name']} {new_group}")
            new_scene = {
                'name': scene['name'],
                'type': scene['type'],
                'lightstates': {
                    old_to_new_lights[id]: state
                    for id, state in scene['lightstates'].items()
                },
                'appdata': scene['appdata'], # used by official hue app otherwise it doesn't display
                'recycle': False
            }
            if new_group:
                new_scene['group'] = new_group
            
            hub.create_scene(new_scene)

def _strpslash(path: str) -> str:
    return path[:-1] if path[-1] == '/' else path

if __name__ == "__main__":
    api_username = None
    hub = Hub(hub_ip='https://...', username='api_key')
    backup = HubBackup('./hue_backup')
    
    old_to_new_lights = old_to_new_id_mapping(hub, backup)
    print(f'\nlights_mapping: {old_to_new_lights}\n')
    
    old_to_new_groups = recreate_groups(hub, backup, old_to_new_lights)
    print(f'\ngroups_mapping: {old_to_new_groups}\n')

    _ = recreate_scenes(hub, backup, old_to_new_groups, old_to_new_lights)