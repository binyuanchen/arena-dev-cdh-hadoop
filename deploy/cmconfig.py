#!/usr/bin/env python

import os
import json

class CMConfig(object):

    def __init__(self):
        pass

    def _materialize_config(self,
                           cfg_file_location=None,
                           substitution_map={}):

        if not cfg_file_location:
            raise RuntimeError('cfg_file_location is empty')

        if not os.path.exists(cfg_file_location):
            raise RuntimeError('path %s does not exist' % cfg_file_location)

        if not os.path.isfile(cfg_file_location):
            raise RuntimeError('path %s is not a file' % cfg_file_location)

        cfg_str = None
        with open(cfg_file_location, 'r') as cfg_file:
            cfg_str = cfg_file.read()

        for pkey, pval in substitution_map.items():
            cfg_str = cfg_str.replace(pkey, pval)

        return json.loads(cfg_str)

    def materialize_config(self,
                           cfg_file_location=None,
                           substitution_file_location=None,
                           substitution_runtime={}):

        if not substitution_file_location:
            raise RuntimeError('substitution_file_location is empty')

        if not os.path.exists(substitution_file_location):
            raise RuntimeError('path %s does not exist' % substitution_file_location)

        if not os.path.isfile(substitution_file_location):
            raise RuntimeError('path %s is not a file' % substitution_file_location)

        substitution_map={}
        with open(substitution_file_location, 'r') as substitution_file:
            substitution_map = json.loads(substitution_file.read())

        merged_map = dict(substitution_map.items() + substitution_runtime.items())
        return self._materialize_config(cfg_file_location, merged_map)

if __name__ == '__main__':
    cm_config = CMConfig()
    params_map = {}
    result = cm_config.materialize_config(cfg_file_location='./config_2.json',
                                          substitution_file_location='./substitution.json',
                                          substitution_runtime={'SSS':'1', 'TTT':'2'})
    print(result)
    print "========"
    print "%s" % json.dumps(result, indent=4, sort_keys=True)