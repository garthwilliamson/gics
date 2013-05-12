'''
Created on 11/05/2013

@author: Garth Williamson
'''
from __future__ import unicode_literals
from __future__ import print_function

import json
import os
# Old pythons don't have ordered dict
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

class GicsConfig(object):
    def __init__(self, config_dir, include_dirs=None):
        self.config_dir = config_dir
        if include_dirs is None:
            include_dirs = os.listdir(config_dir)
        
        self.config = ConfigNode("config", None)
        
        for d in include_dirs:
            self.load_dir(self.config, config_dir, d)

REF_DELIMS = ("<<", ">>")

def Config(path_or_paths, name):
    # todo: path
    if path_or_paths[-5:] == ".json":
        return JsonNode(name, path_or_paths)
    else:
        return DirNode(name, path_or_paths)


def link_refs(config):
    changes = True
    while changes:
        changes = False
        for c in config._walk_children():
            for name, attrib in c._children:
                if isinstance(attrib, list):
                    out_list = []
                    for i in list:
                        r = get_ref(config, i)
                        if r is None:
                            out_list.append(config, i)
                        else:
                            out_list.append(r)
                            changes = True
                    c._children[name] = out_list
                else:
                    r = get_ref(attrib)
                    if r is not None:
                        c._children[name] = r
                        changes = True
                                    
                            
def get_ref(config, name):
    if (not (name[0:3] == REF_DELIMS[0] and name[-3:] == REF_DELIMS[1])):
        return None
    path = name[2:-2].split(".")
    cur = config
    for p in path:
        try:
            cur = cur._children[p]
        except KeyError:
            return None
    return cur


def join(configs, name):
    parent = ConfigNode(name)
    for c in configs:
        parent._append(c)
    return parent
    
    
class ConfigNode(object):
    def __init__(self, name):
        self._name = name
        self._children = OrderedDict()
        self._reference_children = OrderedDict()
        
        self._parent = None

        
    def __str__(self):
        return self._name

    
    def _load_dict(self, d):
        for key, value in d:
            if  isinstance(value, dict):
                new_node = ConfigNode(key)
                self._append(new_node)
                new_node._load_dict(value)
                #TODO: Deal with lists also
            else:
                # Must be a literal. I hope.
                self._children[key] = value

                
    def _append(self, node):
        self._children[node._name] = node
        node._parent = self


    def _append_ref(self, node):
        self._reference_children[node._name] = node

        
    def __getattr__(self, name):
        if name in self._reference_children:
            return self._reference_children[name]
        elif name in self._children:
            return self._children[name]
        elif name not in self.__dict__:
            raise AttributeError("{0} not in {1}".format(name, self._canon_name()))
        else:
            return self.__dict__[name]


    def _canon_name(self):
        parents = [self._name,]
        cur = self
        while cur._parent is not None:
            cur = cur._parent
            parents.append(cur._name)
        parents.reverse()
        return ".".join(parents)
    
    
    def _walk_children(self):
        yield self
        for c in self._children.values():
            if isinstance(c, ConfigNode):
                for cc in c._walk_children():
                    yield cc
                
            
class DirNode(ConfigNode):
    def __init__(self, name, dir_name):
        ConfigNode.__init__(self, name)
        self._dir_name = dir_name
        for item in os.listdir(dir_name):
            if item[-5:] == ".json":
                self._append(JsonNode(item[0:-5], dir_name + "/" + item))
            else:
                self._append(DirNode(item, dir_name + "/" + item))

                        
class JsonNode(ConfigNode):
    def __init__(self, name, file_name):
        ConfigNode.__init__(self, name)
        self._file_name = file_name
        with open(file_name, "r") as f:
            j = json.load(f)
        self._load_dict(j)

            
    def _save(self, file_name=None):
        if file_name is None:
            file_name = self._file_name
        #TODO: Do a save
            