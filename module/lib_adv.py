"""
Project: PiracyTools
File: lib_adv.py
Author: hyugogirubato
Date: 2022.11.10
"""

import json
import os
import re
import subprocess
import urllib.parse
import xmltodict
import utils

""" Commands
ptools adv pkg
ptools adv pkg $NAME
ptools adv wifi
ptools adv db $PACKAGE
ptools adv switch
"""


def _get_network(data, mode='xml'):
    network = ['NONE'] * 3
    if mode == 'xml':
        for item in data['WifiConfiguration']['string']:
            if item['@name'] == 'SSID':
                network[0] = item['#text']
            elif item['@name'] == 'ConfigKey':
                network[1] = item['#text']
            elif item['@name'] == 'PreSharedKey':
                network[2] = item['#text']

        network[1] = network[1].replace(network[0], '')
        network[0] = network[0][1:-1]
        network[2] = network[2][1:-1] if network[2] != 'NONE' else network[2]
    elif mode == 'json':
        network[0] = data['ssid'][1:-1]
        network[1] = data['key_mgmt'].replace('-', '_')
        network[2] = data['psk'][1:-1] if 'psk' in data else network[2]
    else:
        utils.printError('Incompatible file mode', exit=True)
    return {'ssid': network[0], 'security': network[1], 'password': network[2]}


class ADV:

    def __init__(self, device, root=False):
        self.root = root
        self.device = device

    def _get_packages(self):
        packages = []
        for p in subprocess.getoutput(f"adb -s {self.device['name']} shell \"pm list packages -f 2>/dev/null\"").strip().split('\n'):
            m = re.match(r"^package\:/(.*?)/.*/(.*?).apk=(.*?)$", p)
            if m:
                mode = m.group(1).strip()
                name = m.group(2).strip()
                pkg = m.group(3).strip()
                if mode != '' and name != '' and pkg != '':
                    packages.append({'mode': mode, 'name': name, 'pkg': pkg})
        return packages

    def args(self, cmd):
        if cmd[2] in ['wifi', 'db']:  # require root auth
            if self.root:
                if len(cmd) == 3 and cmd[2] == 'wifi':
                    PATH = '/data/misc/wifi'
                    networks = []
                    r = subprocess.getoutput(f"adb -s {self.device['name']} shell su -c \\\"ls -la '{PATH}'\\\"").strip()
                    if 'WifiConfigStore.xml' in r:
                        r = subprocess.getoutput(f"adb -s {self.device['name']} shell su -c \\\"cat '{PATH}/WifiConfigStore.xml'\\\"").strip()
                        r = xmltodict.parse(r)['WifiConfigStoreData']['NetworkList']['Network']
                        if type(r) == list:
                            for data in r:
                                networks.append(_get_network(data, mode='xml'))
                        else:
                            networks.append(_get_network(r, mode='xml'))
                    elif 'wpa_supplicant.conf' in r:
                        r = subprocess.getoutput(f"adb -s {self.device['name']} shell su -c \\\"cat '{PATH}/wpa_supplicant.conf'\\\"").strip()
                        for item in r.split('network=')[1:]:
                            data = {}
                            for r in item.strip()[1:-1].strip().split('\n'):
                                key = r.split('=')[0].strip()
                                value = urllib.parse.unquote(r.split('=')[1].strip())
                                if key == 'id_str':
                                    value = json.loads(value[1:-1])
                                data[key] = value
                            networks.append(_get_network(data, mode='json'))
                    else:
                        utils.printError('Android version not supported', exit=False)
                    if len(networks) == 0:
                        utils.printWarning('No wifi network found')
                    else:
                        utils.printInfo('Wi-Fi network:')
                        print('{0:<24} {1:<14} {2:<30}'.format('SSID', 'Security', 'Password'))
                        for network in networks:
                            print('{0:<24} {1:<14} {2:<30}'.format(network['ssid'], network['security'], network['password']))
                elif len(cmd) == 4 and cmd[2] == 'db':
                    PATH = f"/data/data/{cmd[3]}/databases/"
                    tmp_p = self._get_packages()
                    exist = False
                    for p in tmp_p:
                        if cmd[3] == p['pkg']:
                            exist = True
                            break

                    if exist:
                        r = subprocess.getoutput(f"adb -s {self.device['name']} shell su -c \\\"ls -la '{PATH}'\\\"").strip()
                        if 'No such file or directory' in r:
                            utils.printError('No database available', exit=False)
                        else:
                            databases = []
                            for item in r.split('\n'):
                                if item.startswith('-r'):
                                    r = item.split(' ')
                                    databases.append({'size': r[-4], 'date': f"{r[-3]}T{r[-2]}Z", 'file': r[-1].strip()})
                            if len(databases) == 0:
                                utils.printWarning('No database found')
                            else:
                                utils.printInfo('Database available:')
                                print('{0:<22} {1:<10} {2:<30}'.format('Date', 'Size', 'File'))
                                for database in databases:
                                    print('{0:<22} {1:<10} {2:<30}'.format(database['date'], database['size'], database['file']))

                                file = None
                                r = utils.getInput('\nSelect database?', default=databases[0]['file'], type=str)
                                for i in range(len(databases)):
                                    if r == str(i) or databases[i]['file'] == r:
                                        file = databases[i]['file']
                                        break

                                if file is None:
                                    utils.printError('Invalid database', exit=False)
                                else:
                                    try:
                                        os.system(f"adb -s {self.device['name']} shell su -c \\\"sqlite3 '{PATH}/{file}'\\\"")
                                    except KeyboardInterrupt as e:
                                        print('')
                    else:
                        utils.printError('No app matches', exit=False)
                else:
                    print(f"sh: {' '.join(cmd)}: Invalid command")
            else:
                utils.printError('Root permission required', exit=False)
        else:
            if len(cmd) in [3, 4] and cmd[2] == 'pkg':
                tmp_p = self._get_packages()
                if len(tmp_p) == 0:
                    utils.printWarning('No app installed')
                else:
                    if len(cmd) == 3:
                        packages = tmp_p
                    else:
                        packages = []
                        for p in tmp_p:
                            if cmd[3] in p['name'] or cmd[3] in p['pkg']:
                                packages.append(p)

                    if len(packages) == 0:
                        utils.printError('No app matches', exit=False)
                    else:
                        utils.printInfo('list of installed applications:')
                        print('{0:<20} {1:50} {2:<50}'.format('Mode', 'Name', 'Package'))
                        for p in packages:
                            print('{0:<20} {1:50} {2:<50}'.format(p['mode'], p['name'], p['pkg']))
            else:
                print(f"sh: {' '.join(cmd)}: Invalid command")
