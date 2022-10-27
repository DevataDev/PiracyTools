"""
Project: PiracyTools
File: utils.py
Date: 2022.05.10
"""

import os.path
import shutil
import sys

# External library
from colorama import init
from termcolor import colored
import requests
from clint.textui import progress

init()
_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'


def deletePATH(path):
    if os.path.exists(path):
        shutil.rmtree(path)


def getFileContent(path):
    if not os.path.exists(path):
        printError('Input file not found', exit=True)
    with open(path, mode='rb') as f:
        return f.read()


def deleteFile(pathFile):
    if os.path.exists(pathFile):
        os.remove(pathFile)


def makePath(path):
    if not os.path.exists(path):
        os.makedirs(path)


def saveFile(path, file, content):
    makePath(path)
    output = os.path.join(path, file)
    with open(output, mode='wb') as f:
        f.write(content)


def printError(value, exit=False):
    print(f"{colored('[ERROR]', 'red')} {value}")
    if exit:
        sys.exit(1)


def printInfo(value):
    print(f"{colored('[INFO]', 'cyan')} {value}")


def printWarning(value):
    print(f"{colored('[WARNING]', 'yellow')} {value}")


def printSuccess(value):
    print(f"{colored('[SUCCESS]', 'green')} {value}")


def downloadFile(path: str, file: str, url: str, user_agent=_USER_AGENT):
    output = os.path.join(path, file)
    deleteFile(output)
    printInfo(f'Download file: {output}')
    try:
        r = requests.get(url, stream=True, headers={'accept': '*/*', 'user-agent': user_agent})
    except Exception as e:
        printWarning(f'Save file to "{output}" following link: {url}')
        printError('Unable to download file', exit=True)

    if not r.ok:
        printError(f'Unable to download file from: {url}', exit=True)
    makePath(path)
    with open(os.path.join(path, file), 'wb') as f:
        total_length = int(r.headers.get('content-length'))
        for chunk in progress.bar(r.iter_content(chunk_size=1024), expected_size=(total_length / 1024) + 1):
            if chunk:
                f.write(chunk)
                f.flush()


def getContent(url: str, user_agent=_USER_AGENT):
    r = requests.get(url, headers={'accept': '*/*', 'user-agent': user_agent})
    if not r.ok:
        printError(f'Unable to load file: {url}', exit=True)
    return r.content


def extactFile(input, output, clear=False):
    if not os.path.exists(input):
        printError(f'Input file not found: {input}', exit=True)
    deleteFile(output)
    try:
        import xz
        with xz.open(input) as i:
            with open(output, mode='wb') as o:
                o.write(i.read())
    except Exception as e:
        printError(e, exit=True)

    if clear:
        deleteFile(input)


def getInput(question: str, type='str', default=None):
    if not default is None:
        question += f' [{default}]'
    answer = str(input(question + ': '))
    valid = True
    if answer == '':
        if not default is None:
            answer = default
        else:
            valid = False
    if type == 'int':
        try:
            answer = int(answer)
        except Exception as e:
            valid = False
    elif type == 'bool' or type == 'boolean':
        if answer.lower() in ['y', 'yes', '1', 'true']:
            answer = True
        elif answer.lower() in ['n', 'no', '0', 'false']:
            answer = False
        else:
            valid = False
    if valid:
        return answer
    printError('The answer is invalid.', exit=True)
