from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import unittest
import gics

class TestGicsConfig(unittest.TestCase):
    def test_gics_config_dict(self):
        c = gics.Config({"dir1": "t/data/config1/dir1", "dir2": "t/data/config1/dir2"}, "config")
        self.assertEqual(c.dir1._name, "dir1")
        self.assertEqual(c.dir2.json1._name, "json1")
    
    def test_gics_config_json(self):
        c = gics.Config("t/data/config1/dir2/json1.json", "config")
        self.assertEqual(c.literal1, "lit_val1")
        
    def test_gics_config_dir(self):
        c = gics.Config("t/data/config1/dir2", "config")
        self.assertEqual(c.json1.literal1, "lit_val1")
        
    def test_loops(self):
        loop_c = gics.Config("t/data/config1/dir3", "loopy")
        self.assertEqual(loop_c.loop1.loop2.loop1.loop2.name, "loop2")


class TestConfigNode(unittest.TestCase):
    def setUp(self):
        self.cn = gics.ConfigNode("node1")
        self.cn._append(gics.ConfigNode("node2"))
        self.cn._append(gics.ConfigNode("node3"))
        self.cn.node2._append_ref(self.cn.node3)

    def test_init(self):
        self.assertEqual(self.cn._name, "node1", "Bad initiation routine")
        
    def test_children(self):
        self.assertEqual(self.cn.node2._name, "node2", "Failed to create a child node")
        self.assertEqual(self.cn.node2._parent._name, "node1", "Didn't create parent relationship")
        
    def test_ref_children(self):
        self.assertEqual(self.cn.node3._parent._name, "node1", "Parent of reference child should stay the same")
        self.assertEqual(self.cn.node2.node3._name, "node3", "Reference child can't be accessed")
    
    def test_walk_children(self):
        b = [c._name for c in self.cn._walk_children()]
        self.assertTrue("node1" in b)
        self.assertTrue("node2" in b)
        self.assertTrue("node3" in b)

    def test_indexing(self):
        self.assertEqual(self.cn["node2"]._name, "node2", "Can't access via index")

    def test_sets(self):
        self.cn.node2.node3 = self.cn.node2
        self.assertEqual(self.cn.node2["node3"], self.cn.node3)

class TestDirNode(unittest.TestCase):
    def test_init(self):
        dn = gics.DirNode("dir1", "t/data/config1/dir1")
        self.assertEqual(dn._name, "dir1")

    def test_json_children(self):
        dn = gics.DirNode("dir2", "t/data/config1/dir2")
        self.assertEqual(dn.json1._name, "json1", "Don't have a json child")
    
    def test_literals(self):
        dn = gics.DirNode("dir2", "t/data/config1/dir2")
        self.assertEqual(dn.json1.literal1, "lit_val1")
    
    def test_lists(self):
        dn = gics.DirNode("dir2", "t/data/config1/dir2")
        self.assertTrue("item1" in dn.json1.list1)
        
class TestConfigCreation(unittest.TestCase):
    def test_config_creation(self):
        c1 = gics.Config("t/data/config1/dir2", "config1")
        self.assertEqual(c1.json1._name, "json1")


class TestGetRef(unittest.TestCase):
    def setUp(self):
        self.cn = gics.ConfigNode("node1")
        self.cn._append(gics.ConfigNode("node2"))
        self.cn._append(gics.ConfigNode("node3"))
        self.cn.node2._append_ref(self.cn.node3)
    
    def t_ref_name(self, path, name):
        r = gics.get_ref(self.cn, path)
        self.assertEqual(r._name, name, name + " should be in " + path)

    def test_get_ref(self):
        self.t_ref_name("<<node1>>", "node1")
        self.t_ref_name("<<node1.node2>>", "node2")
        self.t_ref_name("<<node1.node3>>", "node3")
        self.t_ref_name("<<node1.node2.node3>>", "node3")
    
    def test_link_refs(self):
        dn = gics.DirNode("dir2", "t/data/config1/dir2")
        gics.link_refs(dn)
        self.assertEqual(dn.json1.ref1, 1)
        
    def test_list_ref(self):
        dn = gics.DirNode("dir2", "t/data/config1/dir2")
        gics.link_refs(dn)
        self.assertEqual(dn.json1.list1[2], "lit_val1")
    
        
class TestConfigJoin(unittest.TestCase):
    def test_config_join(self):
        c1 = gics.Config("t/data/config1/dir1", "dir1")
        c2 = gics.Config("t/data/config1/dir2", "dir2")
        c = gics.join((c1, c2), "config")
        self.assertEqual(c.dir1._name, "dir1")
        self.assertEqual(c.dir2._name, "dir2")

