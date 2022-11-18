"""
Project: PiracyTools
File: main.py
Author: hyugogirubato
Date: 2022.11.18
"""

import json
import os
import re
import subprocess
import sys
from termcolor import colored
import utils
from module import lib_frida, lib_adv

HELPS = [
    {'command': 'adv', 'description': 'Advanced commands'},
    {'command': 'frida', 'description': 'Dynamic instrumentation'}
]


def get_root(device, exit=True):
    r = subprocess.getoutput(f"adb -s {device['name']} shell su -c \\\"id\\\"").strip()
    status = '(root)' in r
    if not status:
        utils.printError('Root access unavailable', exit=exit)
    return status


def get_devices(exit=True):
    devices = []
    for l in subprocess.getoutput("adb devices").strip().split('\n')[1:]:
        if '\t' in l and l.split('\t')[1] == 'device':
            name = l.split('\t')[0]
            properties = {}
            for p in subprocess.getoutput(f"adb -s {name} shell \"getprop\"").strip().split('\n'):
                m = re.match("^\[([\s\S]*?)\]: \[([\s\S]*?)\]\r?$", p)
                if m:
                    properties[m.group(1)] = m.group(2)
            devices.append({'name': name, 'sdk': properties['ro.build.version.sdk'], 'abi': properties['ro.product.cpu.abi']})

    if len(devices) == 0:
        utils.printWarning('No device available')
        sys.exit(0)

    utils.printInfo('List of devices attached:')
    print('{0:<20} {1:10} {2:<10}'.format('Name', 'SDK', 'Architecture'))
    for device in devices:
        print('{0:<20} {1:10} {2:<10}'.format(device['name'], device['sdk'], device['abi']))

    r = utils.getInput('\nSelect device?', default=devices[0]['name'], type=str)
    for i in range(len(devices)):
        if devices[i]['name'] == r or str(i) == r:
            return devices[i]
    utils.printError('The selected device is invalid', exit=exit)
    if not exit:
        return None


if __name__ == '__main__':
    device = get_devices(exit=True)
    root = False
    hostname = colored(device['name'], 'magenta')
    user = colored('piracytools', 'yellow')
    separator = [colored('@', 'cyan'), colored(':', 'cyan')]
    path = '/'
    utils.printSuccess('Shell started')

    try:
        while True:
            print(f"{hostname}{separator[0]}{user}{separator[1]}{colored(path, 'red')}{colored('#' if root else '$', 'white')} ", end='')
            cmd = str(input())
            if cmd == 'clear':
                os.system('clear') if os.name == 'posix' else os.system('cls')
            elif cmd == 'exit':
                if root:
                    root = False
                else:
                    break
            elif cmd in ['su', 'su -']:
                root = get_root(device, exit=False)
            elif cmd.startswith('ptools'):
                tmp_cmd = cmd.split(' ')
                if len(tmp_cmd) >= 3:
                    if tmp_cmd[1] == 'frida':
                        lib_frida.Frida(device, root=root).args(tmp_cmd)
                    elif tmp_cmd[1] == 'adv':
                        if len(tmp_cmd) == 3 and tmp_cmd[2] == 'switch':
                            tmp_device = get_devices(exit=False)
                            if tmp_device is None:
                                utils.printError('Device not updated', exit=False)
                            elif json.dumps(tmp_device) == json.dumps(device):
                                utils.printWarning('Device already used')
                            else:
                                device = tmp_device
                                path = '/'
                                root = False
                                hostname = colored(device['name'], 'magenta')
                                utils.printSuccess('Updated device')
                        else:
                            lib_adv.ADV(device, root=root).args(tmp_cmd)
                    else:
                        print(f"sh: {cmd}: Invalid command")
                elif len(tmp_cmd) == 2 and tmp_cmd[1] == 'help':
                    print('Available commands:')
                    print('{0:<26} {1:<40}'.format('Command', 'Description'))
                    for h in HELPS:
                        print('{0:<26} {1:<40}'.format(
                            h['command'],
                            h['description']
                        ))
                else:
                    print(f"sh: {cmd}: Invalid command")
            elif cmd == 'logcat' or cmd.startswith('logcat '):
                try:
                    os.system(f"adb -s {device['name']} shell \"{cmd}\"")
                except KeyboardInterrupt as e:
                    print('')
            elif cmd != '':
                is_cd = cmd.startswith('cd ') or cmd == 'cd'
                cmd = f"cd '{path}'; {cmd}"
                if is_cd:
                    cmd = f"{cmd}; pwd"

                cmd = f"adb -s {device['name']} shell su -c \\\"{cmd}\\\"" if root else f"adb -s {device['name']} shell \"{cmd}\""
                r = subprocess.getoutput(cmd).strip()
                if is_cd:
                    items = r.split('\n')
                    if len(items) == 1:
                        path = items[0]
                    r = '\n'.join(items[1:])

                if r != '':
                    if r in ['error: closed', f"adb.exe: device '{device['name']}' not found"]:
                        raise Exception('error: closed')
                    else:
                        print(r)
    except KeyboardInterrupt as e:
        print('')
    except Exception as e:
        utils.printError('Connection to terminal lost')
    utils.printSuccess('Shell stopped')
    r = utils.getInput('Stop ADB?', default='no', type='boolean')
    if r:
        os.system(f"adb kill-server")
        utils.printSuccess('ADB stopped')
    sys.exit(0)
