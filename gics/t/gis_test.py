import unittest
import gics
import os

class TestGicsConfig(unittest.TestCase):
    pass

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
        
class TestDirNode(unittest.TestCase):
    def test_init(self):
        dn = gics.DirNode("dir1", "t/data/config1/dir1")
        self.assertEqual(dn._name, "dir1")
    def test_json_children(self):
        dn = gics.DirNode("dir2", "t/data/config1/dir2")
        self.assertEqual(dn.json1._name, "json1", "Don't have a json child")
        
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
        
class TestConfigJoin(unittest.TestCase):
    def test_config_join(self):
        c1 = gics.Config("t/data/config1/dir1", "dir1")
        c2 = gics.Config("t/data/config1/dir2", "dir2")
        c = gics.join((c1, c2), "config")
    