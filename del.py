import os
import sys
import subprocess
import platform
import stat
import logging

_log = logging.getLogger(__name__)


if sys.platform == 'win32':
    from ntfsutils.junction import unlink as remove_symlink, isjunction as is_symlink
else:
    from os import unlink
    from os.path import islink as is_symlink

    def remove_symlink(path):
        if not is_symlink(path):
            raise Exception("'%s' does not exist or is not a symlink" % path)
        unlink(path)


def _is_needed_pure_python_cleanup():
    return sys.platform != 'win32' \
             or int(platform.release()) <= 7    # can not use `del` tool for Win7 or lower version


def _remove_empty_dir(path):
    try:
        os.rmdir(path)
    except os.error:
        _log.error("Can't delete dir %s", path)
        if os.path.exists(path):
            os.chmod(path, stat.S_IWRITE)
            os.rmdir(path)


def _delete_file(name):
    if os.access(name, os.F_OK):
        stats = os.stat(name)
        if stats and not stats[stat.ST_MODE] & stat.S_IWRITE:
            os.chmod(name, stat.S_IWRITE)
    os.remove(name)


def _delete_dir(root_dir):
    if is_symlink(root_dir):
        try:
            remove_symlink(root_dir)
        except OSError:
            _log.error("Can't delete symlink %s", root_dir)
            if os.path.exists(root_dir):
                os.chmod(root_dir, stat.S_IWRITE)
                remove_symlink(root_dir)

        return

    for file_name in os.listdir(root_dir):
        abs_path = os.path.join(root_dir, file_name)
        if os.path.isfile(abs_path):
            _delete_file(abs_path)
        else:
            _delete_dir(abs_path)

    _remove_empty_dir(root_dir)


def _run_delete_path(name):
    if not os.path.exists(name):
        _log.info("Skipping '%s' because it doesnt exist", name)
        return

    if os.path.isfile(name):
        _delete_file(name)
    else:
        _delete_dir(name)


def _remove_all_symlinks(path):
    for current_root, dirs, files in os.walk(path):
        for d in dirs:
            abs_path = os.path.join(current_root, d)
            if is_symlink(abs_path):
                try:
                    remove_symlink(abs_path)
                except OSError:
                    _log.error("Remove symlink failed '%s' ", abs_path)
                    if os.path.exists(abs_path):
                        os.chmod(abs_path, stat.S_IWRITE)
                        remove_symlink(abs_path)


def _run_delete_with_del(path):
    _log.info("Remove symlinks from '%s'...", path)
    _remove_all_symlinks(path)

    _log.info("Deleting from '%s'...", path)

    _run_process_del(path)

    _log.info("Remove dir '%s'...", path)

    for dir in os.listdir(path):
        abs_path = os.path.join(path, dir)
        _delete_dir(abs_path)

    _remove_empty_dir(path)


def _run_delete_with_python(path):
    for file_name in os.listdir(path):
        _run_delete_path(os.path.join(path, file_name))

    _remove_empty_dir(path)


def _run_process_del(path):
    cmd = [
        'cmd.exe', '/C',
        'DEL', '/F', '/Q', '/S',
        path,
    ]
    with open(os.devnull, 'w') as tempf:
        proc = subprocess.Popen(cmd, stdout=tempf, stderr=tempf)
        proc.communicate()
        

def _run_delete(path):
    if _is_needed_pure_python_cleanup():
        _run_delete_with_python(path)
    else:
        _run_delete_with_del(path)


if '__name__' == __main__:
    _run_delete()
