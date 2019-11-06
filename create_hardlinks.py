import sys
from functools import partial

import os
from timeit import default_timer as timer
from saber.bender.stages.file_utils import (
    UPDATE_RESOLVE_TYPE, REPLACE_RESOLVE_TYPE, EXCLUDE_RESOLVE_TYPE, SYMLINK_COPY_TYPE)
from saber.bender.core.mapping_path import match_mapping_list
from saber.bender.stages.file_utils.delete_files import delete_dir
from saber.lib.io import deleteFile
from saber.bender import MappingPath

if sys.platform == 'win32':
    from ntfsutils.hardlink import create as hardlink
else:
    from os import link as hardlink


class MapFileLayerError(Exception):
    pass


def _create_hardlink(src, dst):
    target_dir = os.path.dirname(dst)
    if not os.path.isdir(target_dir):
        # ctx.info("Create dir '%s'", target_dir)
        os.makedirs(target_dir)

    # ctx.info("Create hardlink: %s --> %s", src, dst)
    hardlink(src, dst)


def _apply_hardlink_mapping(root_src, root_dst, mapping, excludes):
    if UPDATE_RESOLVE_TYPE not in mapping.tags:  # replace files by default
        for path in mapping.walkFiles(root_dst):
            rel_path = os.path.relpath(path, root_dst)
            if match_mapping_list(excludes, rel_path):
                continue
            deleteFile(path)

    for src_path in mapping.walkFiles(root_src):
        rel_path = os.path.relpath(src_path, root_src)

        dst_path = os.path.join(root_dst, rel_path)

        if os.path.exists(dst_path):
            deleteFile(dst_path)

        _create_hardlink(src_path, dst_path)


if __name__ == '__main__':

    start = timer()

    excludes = []
    mapping = []

    src = os.path.abspath('D:/work/test_del/')
    dst = os.path.abspath('D:/work/test_del_hardlinks/')


    for p in [MappingPath('...')]:
        if len({UPDATE_RESOLVE_TYPE, REPLACE_RESOLVE_TYPE, EXCLUDE_RESOLVE_TYPE}.intersection(p.tags)) > 1:
                raise ValueError(
                    "Tags can not contain '{}', '{}' and '{}' simultaneously".format(
                        UPDATE_RESOLVE_TYPE, REPLACE_RESOLVE_TYPE, EXCLUDE_RESOLVE_TYPE))

        if EXCLUDE_RESOLVE_TYPE in p.tags:
            excludes.append(p)
        else:
            mapping.append(p)

    for m in mapping:
        print "Merging files from '{srcRoot}' to '{dstRoot}' by pattern '{pattern}'".format(
                srcRoot=src, dstRoot=dst, pattern=m.pattern)

        _apply_hardlink_mapping(src, dst, m, excludes)

    end = timer()

    print('Create hardlinks ended, elapsed time: ', end - start)
