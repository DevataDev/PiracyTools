"""
Project: PiracyTools
File: lib_frida.py
Author: hyugogirubato
Date: 2022.12.18
"""

import os
import subprocess
import time
import utils

""" Commands
ptools frida status
ptools frida install server
ptools frida install pip
ptools frida uninstall server
ptools frida uninstall pip
ptools frida start
ptools frida stop
ptools frida pinning $PACKAGE $VERSION
ptools frida run $SCRIPT $PACKAGE
ptools frida create
"""

PATH_SCRIPTS = os.path.join('module', 'frida_scripts')
HELPS = [
    {'command': 'status', 'root': False, 'description': 'Show frida status'},
    {'command': 'install server|pip', 'root': True, 'description': 'Install frida server|pip'},
    {'command': 'uninstall server|pip', 'root': True, 'description': 'Uninstall frida server|pip'},
    {'command': 'start|stop', 'root': True, 'description': 'Start|Stop frida service'},
    {'command': 'pinning $PACKAGE $VERSION', 'root': True, 'description': 'Bypass SSL pinning for an application'},
    {'command': 'run $SCRIPT $PACKAGE', 'root': True, 'description': 'Run a frida personal script'},
    {'command': 'create', 'root': False, 'description': 'Native and classic function interception script creation'}
]


class Frida:

    def __init__(self, device, root=False):
        self.root = root
        self.device = device
        self.releases = 'https://github.com/frida/frida/releases'

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
        elif cmd[2] in ['start', 'stop', 'install', 'uninstall', 'pinning', 'run']:  # require root auth
            if self.root:
                if len(cmd) == 3 and cmd[2] == 'stop':
                    if len(pid) == 0:
                        utils.printWarning('Frida is not running')
                    else:
                        for p in pid:
                            subprocess.getoutput(f"adb -s {self.device['name']} shell su -c \\\"kill -9 {p['pid']}\\\"")
                        utils.printSuccess('Frida stopped') if len(self._getStatus()) == 0 else utils.printError('Frida failed to stop', exit=False)
                elif (len(cmd) == 4 or len(cmd) == 5) and cmd[2] == 'pinning':
                    if len(pid) == 0:
                        utils.printError('Frida is not running', exit=False)
                    else:
                        version = None
                        if len(cmd) == 5:
                            if not cmd[4] in ['1', '2']:
                                utils.printError('Version number is incorrect', exit=False)
                            else:
                                version = cmd[4]
                        else:
                            version = '1'
                        if not version is None:
                            utils.printSuccess('Bypass SSL pining started')
                            os.system(f"frida -D \"{self.device['name']}\" -l \"{os.path.join(PATH_SCRIPTS, f'pinning_v{version}.js')}\" -f \"{cmd[3]}\"")
                            utils.printSuccess('Bypass SSL pining stopped')
                elif len(cmd) == 5 and cmd[2] == 'run':
                    if os.path.exists(cmd[3]):
                        os.system(f"frida -D \"{self.device['name']}\" -l \"{cmd[3]}\" -f \"{cmd[4]}\"")
                    else:
                        utils.printError('Frida script not found', exit=False)
                elif cmd[2] in ['start', 'install', 'uninstall']:
                    if len(pid) == 0:
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
                                        version = subprocess.getoutput("frida --version").strip()
                                        url = f"https://github.com/frida/frida/releases/download/{version}/frida-server-{version}-android-{arch}.xz"
                                        file = f"frida-server-{version}-{arch}.xz"
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
                        utils.printWarning('Frida already running')
                else:
                    print(f"sh: {' '.join(cmd)}: Invalid command")
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
            elif len(cmd) == 3 and cmd[2] == 'create':
                is_native = utils.getInput('Native library?', default='no', type='boolean')
                if is_native:
                    content = utils.getFileContent(os.path.join(PATH_SCRIPTS, 'native_function.js')).decode('utf-8')
                    nv_lib_name = utils.getInput('Library name?', default='Crypto', type='str')
                    nv_lib_module = utils.getInput('Module name?', default='Hash', type='str')
                    nv_lib_count = utils.getInput('Arguments count?', default=2, type='int')
                    content = content.replace('{NATIVE_LIBRARY_NAME}', nv_lib_name)
                    content = content.replace('{NATIVE_MODULE_NAME}', nv_lib_module)
                    content = content.replace('{NATIVE_ARGS_COUNT}', str(nv_lib_count))
                else:
                    content = utils.getFileContent(os.path.join(PATH_SCRIPTS, 'function.js')).decode('utf-8')
                    fc_class_name = utils.getInput('Class name?', default='MainActivity', type='str')
                    fc_name = utils.getInput('Function name?', default='Display', type='str')
                    fc_args_count = utils.getInput('Arguments count?', default=2, type='int')
                    fc_args = []
                    fc_types = []
                    for i in range(fc_args_count):
                        fc_type = utils.getInput(f"Argument {i} type?", default='java.lang.String', type='str')
                        if fc_type.lower() in ['str', 'string']:
                            fc_type = '"java.lang.String"'
                        elif fc_type.lower() in ['integer']:
                            fc_type = '"java.lang.Integer"'
                        elif fc_type.lower() in ['bool', 'boolean']:
                            fc_type = '"java.lang.Boolean"'
                        elif fc_type.lower() in ['byte']:
                            fc_type = '"java.lang.Byte"'
                        elif fc_type.lower() in ['double']:
                            fc_type = '"java.lang.Double"'
                        elif fc_type.lower() in ['float']:
                            fc_type = '"java.lang.Float"'
                        elif fc_type.lower() in ['long']:
                            fc_type = '"long"'
                        else:
                            fc_type = f'"{fc_type}"'
                        fc_types.append(fc_type)
                        fc_args.append(f"arg{i}")

                    content = content.replace('{FUNCTION_CLASS_NAME}', fc_class_name)
                    content = content.replace('{FUNCTION_NAME}', fc_name)
                    content = content.replace('{FUNCTION_ARGS_TYPE}', ', '.join(fc_types))
                    content = content.replace('{FUNCTION_ARGS}', ', '.join(fc_args))
                    result = []
                    for i in range(fc_args_count):
                        result.append(f"                    console.log(`  --> arg{i}:  $" + "{" + f"arg{i}" + "}`);")
                    content = content.replace('{FUNCTION_CONSOLE_ARGS}', '\n'.join(result))
                file = f"{int(time.time())}_frida_{'native_function' if is_native else 'function'}.js"
                utils.saveFile('tmp', file, content.encode('utf-8'))
                utils.printInfo(f"File saved at: {os.path.join('tmp', file)}")
            elif len(cmd) == 3 and cmd[2] == 'help':
                print('Available commands:')
                print('{0:<26} {1:<14} {2:<40}'.format('Command', 'Permission', 'Description'))
                for h in HELPS:
                    print('{0:<26} {1:<14} {2:<40}'.format(
                        h['command'],
                        'root' if h['root'] else 'shell',
                        h['description']
                    ))
            else:
                print(f"sh: {' '.join(cmd)}: Invalid command")
