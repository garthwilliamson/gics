""" gics. A rather insane config system

Usage:
    gics is designed to be used to configure large web applications. The
    original usecase is for configuring fabric deployment and templating to
    several different clusters.
    
    The normal use case for gics is to be given a directory layout with a
    series of json files in each one.
    
    For example:
        config/
            servers/
                web1.json
                db1.json
                web2.json
                db2.json
            clusters/
                cluster1.json
                cluster2.json
    
    Each json file consists of normal json syntax, with a particular format of
    string special cased:
        (web1.json)
        {
            "name": "web1",
            "cluster": "<<clusters.cluster1>>,
            "ip": "1.2.3.4",
            "cores": 24
        }
        
        (cluster1.json)
        {
            "name": "Cluster 1",
            "servers": [
                "<<servers.web1>>,
                "<<servers.db1>>
            ],
            "db_server": "<<servers.db1>>",
            "web_server": "<<servers.web1>>",
            "outward_ip": "<<cluster1.web_server.ip>>"
        }
        (etc...)
    
    To create a config behemoth, one could run:
    
        config = gics.Config("config/")
    
    This returns a gics config object, which can then be used to access all
    the different properties of these clusters.
    
    Access to properties is via dot notation:
        
        >>> print config.clusters.cluster1.name
        "Cluster 1"
        >> print config.clusters.cluster1.servers[0].ip
        "1.2.3.4"
        
    Notice that the second one returns the name of the web server - this is
    because any strings either directly in values or as immediate members of
    lists are scanned for the format "<<word.words.morewords>>" and links are
    created if there is something in the tree with those properties. This
    process is iterative, so circular links, links through links and more can
    all be created.
    
    Future plans
        - In the future I plan to add thing["item"] access methods
        - Lists currently can only contain either literals, references or
          dictionaries - I don't parse further down than the immediate members.
        - I need to make writing to accessors work
        - I need to enable resaving of the json source
        
"""
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function

import json
import os
# Old pythons don't have ordered dict
try:
    from collections import OrderedDict
except ImportError:
    from .ordereddict import OrderedDict


REF_DELIMS = ("<<", ">>")


def Config(path_or_paths, name):
    """ Returns a ConfigNode object created and instantiated from the arguments
    
    This is the normal method of using gics. There are three options for the
    first arg - you can pass in a dictionary of directories or json files, you
    can pass in a json file directly or you can pass in a directory to be
    loaded.
    
    Note that Config({"dir1": "dir/dir1"}, "config") returns a "config" 
    node with the directory contents loaded under dir1 whereas
    Config("dir/dir1", "config") returns a "config" node with the
    contents directly underneath
    
    Args:
        path_or_paths: dictionary of json files and directories or...
                       json file or...
                       directory
    Returns: A ConfigNode object
    
    """
    config = None
    if isinstance(path_or_paths, dict):
        config = ConfigNode(name)
        for n, d in path_or_paths.items():
            config._append(DirNode(n, d))
    elif path_or_paths[-5:] == ".json":
        config = JsonNode(name, path_or_paths)
    else:
        try:
            config = DirNode(name, path_or_paths)
        except OSError as e:
            if e.errno == 20:
                pass
            else:
                raise e
    link_refs(config)
    return(config)


def link_refs(config):
    """ The method used to link references
    
    The method iterates through a tree of ConfigNodes and links test strings
    of the form <<name.thing.thingy>> to the appropriate location in the tree.
    
    The linking syntax can be overridden with any other pair of two character
    strings by first setting gics.REF_DELIMS = ("{{", "}}")
    
    Modifies config in place
    
    Args:
        config: The ConfigNode object to search through
        
    """
    changes = True
    while changes:
        changes = False
        for c in config._walk_children():
            for name, attrib in c._children.items():
                # Lists are tricky. Go to each member and link it if it is
                # a reference.
                # TODO: In future we should deal with things nested inside lists
                if isinstance(attrib, list):
                    out_list = []
                    for i in attrib:
                        if isinstance(i, basestring):
                            r = get_ref(config, i)
                            if r is None:
                                out_list.append(i)
                            if r is not None:
                                out_list.append(r)
                                changes = True
                        else:
                            out_list.append(i)
                    c._children[name] = out_list
                elif isinstance(attrib, basestring):
                    r = get_ref(config, attrib)
                    if r is not None:
                        c._reference_children[name] = r
                        c._children[name] = ">>" + attrib + "<<"
                        changes = True


def get_ref(config, name):
    """ Used to find the part of the config in the name place.
    
    Args:
        config: A ConfigNode object
        name: A string of the for "x.y.z"
    Returns: None if the reference isn't valid or if the item isn't in the tree
        otherwise either the ConfigNode or other oject at that position
        
    """
    if (not (name[0:2] == REF_DELIMS[0] and name[-2:] == REF_DELIMS[1])):
        return None
    path = name[2:-2].split(".")
    cur = config
    if path[0] == cur._name:
        path = path[1:]
    for p in path:
        try:
            cur = cur._any_children(p)
        except KeyError:
            return None
    return cur


def join(configs, name):
    """ Joins a list of configs under a new parent
    
    Args:
        configs: An iterable of the configs to put under the new parent
        name: The name the new parent should have
    Returns: A new ConfigNode called "name" with the configs as children
    
    """
    parent = ConfigNode(name)
    for c in configs:
        parent._append(c)
    return parent
    
    
class ConfigNode(object):
    """ The most basic config node type
    
    Overrides getattr so that we can use dot notation to access its members
    
    """
    def __init__(self, name):
        """ Create a new node called "name"
        
        Args:
            name: A string to call this node
        
        """
        self._name = name
        self._children = OrderedDict()
        self._reference_children = OrderedDict()
        
        self._parent = None
        self.__setattr__ = self._setattr
        
    def __str__(self):
        return self._name

    
    def _load_dict(self, d):
        """ Load a dictionary with the items as children of this node
        
        Args:
            d: A dictionary-like object
            
        """
        for key, value in d.items():
            if  isinstance(value, dict):
                new_node = ConfigNode(key)
                self._append(new_node)
                new_node._load_dict(value)
            else:
                self._children[key] = value


    def _append(self, node):
        """ Appends the supplied ConfigNode as a child of this node
        
        Args:
            node: A ConfigNode object
            
        """
        self._children[node._name] = node
        node._parent = self


    def _append_ref(self, node):
        """ Appends a referenced object as a child of this node
        
        This is used to avoid circles when walking the tree, and also to make
        save to json work
        
        Args:
            node: A ConfigNode object to be referenced
            
        """
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


    def _setattr(self, name, value):
        # We can't set attr before we have inited
        if name in self._reference_children:
            del self._reference_children[name]
            self._set(name, value)
        elif name in self._children:
            del self._children[name]
            self._set(name, value)
        elif name not in self.__dict__:
            raise AttributeError("{0} not in {1}".format(name, self._canon_name()))
        else:
            self.__dict__[name] = value


    def _set(self, name, value):
        if isinstance(value, ConfigNode):
            self._reference_children(name, value)
        else:
            self._children[name] = value


    def _canon_name(self):
        """ The canonical name of this node
        
        Of the form x.y.z where x, y and z could be directories, dictionaries
        or json files
        
        Returns: The canonical representation of the name of this node
        
        """
        parents = [self._name,]
        cur = self
        while cur._parent is not None:
            cur = cur._parent
            parents.append(cur._name)
        parents.reverse()
        return ".".join(parents)
    
    
    def _walk_children(self):
        """ Walks the non-reference children of this node and all child nodes
        
        Yields: One ConfigNode object at a time. Only node though - no leaves
        
        """
        yield self
        for c in self._children.values():
            if isinstance(c, ConfigNode):
                for cc in c._walk_children():
                    yield cc
                
                
    def _any_children(self, name):
        """ Returns the first child with a given name
         
        Convenience method to grab the first child out of reference children
        and normal children with a given name. Reference children are returned
        first because the original reference strind is left as a normal child
        
        """
        if name in self._reference_children:
            return self._reference_children[name]
        elif name in self._children:
            return self._children[name]
        else:
            raise KeyError("No children called " + name)


    # Methods to emulate container types:
    def __len__(self):
        return len(self._children) + len(self._reference_children)


    def __getitem__(self, key):
        if key in self._reference_children:
            return self._reference_children[key]
        elif key in self._children:
            return self._children[key]
        else:
            raise KeyError("{0} not in {1}".format(key, self._canon_name()))


    def __setitem__(self, key, value):
        if key not in self.__dict__:
            self.__setattr__(key, value)
        else:
            raise KeyError("{0} not in {1}".format(key, self._canon_name()))


    def __delitem__(self, key):
        if key in self._reference_children:
            del(self._reference_children[key])
        elif key in self._children:
            del(self._children[key])
        else:
            raise KeyError("{0} not in {1}".format(key, self._canon_name()))


    def __iter__(self):
        for k in self.cn._reference_children:
            yield k
        for k in self.cn.children:
            yield k


class DirNode(ConfigNode):
    def __init__(self, name, dir_name):
        """ Takes a directory name as well """
        ConfigNode.__init__(self, name)
        self._dir_name = dir_name
        for item in os.listdir(dir_name):
            if item[-5:] == ".json":
                self._append(JsonNode(item[0:-5], dir_name + "/" + item))
            else:
                try:
                    self._append(DirNode(item, dir_name + "/" + item))
                except OSError as e:
                    if e.errno in (20, 22):
                        pass
                    else:
                        raise e


class JsonNode(ConfigNode):
    def __init__(self, name, file_name):
        """ Takes a filename as well """
        ConfigNode.__init__(self, name)
        self._file_name = file_name
        with open(file_name, "r") as f:
            j = json.load(f)
        self._load_dict(j)

            
    def _save(self, file_name=None):
        """ Unimplemented """
        if file_name is None:
            file_name = self._file_name
        #TODO: Do a save
        # iterate through children, if a ref then stick a ref in, else jsonarize

