"""
Project: PiracyTools
File: lib_frida.py
Author: hyugogirubato
Date: 2022.10.28
"""

import os
import subprocess
import utils

""" Commands
ptools frida status
ptools frida install server
ptools frida install pip
ptools frida uninstall server
ptools frida uninstall pip
ptools frida start
ptools frida stop
ptools frida pinning $PACKAGE
"""

SCRIPT = './module/script_frida.js'


class Frida:

    def __init__(self, device, root=False):
        self.root = root
        self.device = device
        self.releases = 'https://github.com/frida/frida/releases'
        self.version = '15.2.2'  # '15.2.2'  # 12.4.7

    def _getStatus(self):
        pid = []
        r = subprocess.getoutput(f"adb -s {self.device['name']} shell \"ps -A | grep frida\"").strip()
        if r != '':
            for r in r.split('\n'):
                p = ['NONE'] * 3
                items = r.split(' ')
                p[0] = items[0]
                p[2] = items[-1]
                for item in items[1:-1]:
                    if item != '':
                        p[1] = item
                        break
                pid.append({'user': p[0], 'pid': p[1], 'name': p[2]})
        return pid

    def _getFrida(self, mode=None):
        result = True
        if mode is None or mode == 'server':
            result = 'frida-server' in subprocess.getoutput(f"adb -s {self.device['name']} shell \"cd '/data/local/tmp/'; ls -la\"").strip()
        if mode is None or mode == 'pip':
            tmp = subprocess.getoutput("pip list").strip()
            tmp = 'frida-tools' in tmp and 'python-xz' in tmp
            result = result or tmp if mode is None else tmp
        return result

    def args(self, cmd):
        pid = self._getStatus()
        tmp_server = self._getFrida(mode='server')
        tmp_pip = self._getFrida(mode='pip')

        if not cmd[2] in ['install', 'uninstall'] and (not tmp_server or not tmp_pip):
            if not tmp_server:
                utils.printError('Frida (server) is not installed', exit=False)
            if not tmp_pip:
                utils.printError('Frida (pip) is not installed', exit=False)
        elif cmd[2] in ['start', 'stop', 'install', 'uninstall', 'pinning']:  # require root auth
            if self.root:
                if len(cmd) == 3 and cmd[2] == 'stop':
                    if len(pid) == 0:
                        utils.printWarning('Frida is not running')
                    else:
                        for p in pid:
                            subprocess.getoutput(f"adb -s {self.device['name']} shell su -c \\\"kill -9 {p['pid']}\\\"")
                        utils.printSuccess('Frida stopped') if len(self._getStatus()) == 0 else utils.printError('Frida failed to stop', exit=False)
                elif len(cmd) == 4 and cmd[2] == 'pinning':
                    if len(pid) == 0:
                        utils.printError('Frida is not running', exit=False)
                    else:
                        utils.printSuccess('Bypass SSL pining started')
                        os.system(f"frida --no-pause -D \"{self.device['name']}\" -l \"{SCRIPT}\" -f \"{cmd[3]}\"")
                        utils.printSuccess('Bypass SSL pining stopped')
                elif len(pid) == 0:
                    if len(cmd) == 3 and cmd[2] == 'start':
                        subprocess.getoutput(f"adb -s {self.device['name']} shell su -c \\\"setsid ./data/local/tmp/frida-server &>/dev/null &\\\"")
                        utils.printError('Frida failed to start', exit=False) if len(self._getStatus()) == 0 else utils.printSuccess('Frida started')
                    elif len(cmd) == 4 and cmd[2] == 'install':
                        if cmd[3] == 'pip':
                            if not self._getFrida(mode='pip'):
                                os.system("pip install frida-tools")
                                os.system("pip install python-xz")
                                utils.printSuccess('Frida (pip) is installed') if self._getFrida(mode='pip') else utils.printError('Frida (pip) is not installed', exit=False)
                            else:
                                utils.printWarning('Frida (pip) is already installed')
                        elif cmd[3] == 'server':
                            if not self._getFrida(mode='server'):
                                if not self._getFrida(mode='pip'):
                                    utils.printWarning('Frida (pip) must be installed')
                                else:
                                    output = os.path.join('tmp', 'frida-server')
                                    arch = self.device['abi'].split('-')[0] if '-' in self.device['abi'] else self.device['abi']
                                    url = f"https://github.com/frida/frida/releases/download/{self.version}/frida-server-{self.version}-android-{arch}.xz"
                                    file = f"frida-server-{self.version}-{arch}.xz"
                                    if not os.path.exists(os.path.join('tmp', file)):
                                        utils.downloadFile('tmp', file, url)
                                    utils.extactFile(os.path.join('tmp', file), output, clear=False)
                                    if not os.path.exists(output):
                                        utils.printError('The required file does not exist', exit=True)

                                    os.system(f"adb -s {self.device['name']} push \"{output}\" \"/data/local/tmp/frida-server\"")
                                    subprocess.getoutput(f"adb -s {self.device['name']} shell su -c \\\"chmod 755 '/data/local/tmp/frida-server'\\\"")
                                utils.printSuccess('Frida (server) is installed') if self._getFrida(mode='server') else utils.printError('Frida (server) is not installed', exit=False)
                            else:
                                utils.printWarning('Frida (server) is already installed')
                        else:
                            utils.printError('Frida module invalid', exit=False)
                    elif len(cmd) == 4 and cmd[2] == 'uninstall':
                        if cmd[3] == 'pip':
                            if self._getFrida(mode='pip'):
                                os.system("pip uninstall frida-tools")
                                os.system("pip uninstall python-xz")
                                utils.printSuccess('Frida (pip) is uninstalled') if not self._getFrida(mode='pip') else utils.printError('Frida (pip) is not uninstalled', exit=False)
                            else:
                                utils.printWarning('Frida (pip) is not installed')
                        elif cmd[3] == 'server':
                            if self._getFrida(mode='server'):
                                subprocess.getoutput(f"adb -s {self.device['name']} shell su -c \\\"rm '/data/local/tmp/frida-server'\\\"")
                                subprocess.getoutput(f"adb -s {self.device['name']} shell su -c \\\"rm -r '/data/local/tmp/re.frida.server'\\\"")
                                utils.printSuccess('Frida (server) is uninstalled') if not self._getFrida(mode='server') else utils.printError('Frida (server) is not uninstalled', exit=False)
                            else:
                                utils.printWarning('Frida (server) is not installed')
                        else:
                            utils.printError('Frida module invalid', exit=False)
                    else:
                        print(f"sh: {' '.join(cmd)}: Invalid command")
                else:
                    utils.printWarning('Frida already running')
            else:
                utils.printError('Root permission required', exit=False)
        else:
            if len(cmd) == 3 and cmd[2] == 'status':
                if len(pid) == 0:
                    utils.printWarning('Frida is not running')
                else:
                    utils.printInfo('Frida process running:')
                    print('{0:<10} {1:<10} {2:<30}'.format('User', 'PID', 'Name'))
                    for p in pid:
                        print('{0:<10} {1:<10} {2:<30}'.format(p['user'], p['pid'], p['name']))
            else:
                print(f"sh: {' '.join(cmd)}: Invalid command")
