"""Downloader for getting a directory off of an sftp server

This script assumes that the sftp server is already in your known_hosts file.
If it's not, take a look at 'ssh-keyscan'.

This script also assumes that you authenticate to the sftp server via password
(not via public key).  You'll be prompted for your password after you've started
running the script.

This script does not follow symbolic links when recursively copying directories.
"""
import argparse
from collections import deque
import getpass
import os
import stat

from paramiko.client import SSHClient


def _get_args():
    """Get command line arguments"""
    parser = argparse.ArgumentParser(
        description='Script to grab directory off of sftp server')
    parser.add_argument(
        'username',
        help='username used for logging into sftp server')
    parser.add_argument(
        'hostname',
        help='identifier for sftp server you want to connect to')
    parser.add_argument(
        'directory',
        help='directory you want to download from the sftp server')
    parser.add_argument(
        'output',
        help='local path where you want the contents of directory to be')
    return parser.parse_args()


def _dir_gen(sftp, cur):
    """Build a generator that prepends cur to its children"""
    for child in sftp.listdir(cur):
        yield os.path.join(cur, child)


def _getfile(sftp, cur, localcur, ofh):
    """Try getting file and report whether successful"""
    try:
        sftp.get(cur, localcur)
    except:
        print('\tProblem downloading '+cur)
        ofh.write(cur)
        ofh.write('\n')
        return False
    return True


def _download_directory(sftp, directory, outpath):
    """Downloads specified directory from sftp"""
    try:
        sftp.lstat(directory)
    except OSError:
        raise OSError('"'+directory+'" was not found on the server')
    sftp.chdir(directory)
    queue = deque(sftp.listdir())
    with open('badfiles.txt', 'w') as ofh:
        while queue:
            cur = queue.popleft()
            localcur = os.path.join(outpath, cur)
            if stat.S_ISDIR(sftp.lstat(cur).st_mode):
                queue.extend(_dir_gen(sftp, cur))
                os.makedirs(localcur, exist_ok=True)
            else:
                print('Downloading: "'+cur+'"')
                _getfile(sftp, cur, localcur, ofh)


def _run(args):
    """Run the script"""
    client = SSHClient()
    client.load_system_host_keys()
    password = getpass.getpass()
    client.connect(args.hostname, username=args.username, password=password)
    sftp = client.open_sftp()
    _download_directory(sftp, args.directory, args.output)
    sftp.close()
    client.close()

if __name__ == '__main__':
    _run(_get_args())
