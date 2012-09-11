## Copyright (c) 2012 Aldebaran Robotics. All rights reserved.
## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.

import unittest
from StringIO import StringIO

import qisrc.manifest

class ManifestTestCase(unittest.TestCase):

    def test_parse(self):
        xml = """
<manifest>
    <remote name="origin"
        fetch="git@git.aldebaran.lan"
        review="{name}@gerrit.aldebaran.lan"
    />
</manifest>
"""
        xml_in = StringIO(xml)
        manifest = qisrc.manifest.load(xml_in)
        self.assertEquals(len(manifest.projects), 0)

    def test_simple_parse(self):
        xml = """
<manifest>
    <remote name="origin"
        fetch="git@git.aldebaran.lan"
    />

    <project name="qi/libqi.git"
        path="lib/libqi"
    />
</manifest>
"""
        xml_in = StringIO(xml)
        manifest = qisrc.manifest.load(xml_in)
        self.assertEquals(len(manifest.projects), 1)
        libqi = manifest.projects[0]
        self.assertEquals(libqi.fetch_url, "git@git.aldebaran.lan:qi/libqi.git")
        self.assertEquals(libqi.path, "lib/libqi")

    def test_trailing_slash(self):
        xml = """
<manifest>
    <remote name="origin" fetch="git@foo" />
    <project name="foo1" path="foo" />
    <project name="foo2" path="foo/" />
</manifest>
"""
        xml_in = StringIO(xml)
        error = None
        try:
            qisrc.manifest.load(xml_in)
        except Exception, e:
            error = e
        self.assertFalse(error is None)
        self.assertTrue("two projects with the same path" in str(error))

    def test_various_url_formats(self):
        xml = """
<manifest>
    <remote name="ssh" fetch="git@foo" />
    <remote name="ssh-url" fetch="ssh://git@foo" />
    <remote name="http" fetch="http://foo" />
    <remote name="local" fetch="/path/to/foo" />

    <project name="ssh-bar.git" remote="ssh" />
    <project name="ssh-url-bar.git" remote="ssh-url" />
    <project name="http-bar.git" remote="http" />
    <project name="local-bar.git" remote="local" />

</manifest>
"""
        xml_in = StringIO(xml)
        manifest = qisrc.manifest.load(xml_in)
        ssh_bar = manifest.get_project("ssh-bar.git")
        self.assertEquals(ssh_bar.fetch_url, "git@foo:ssh-bar.git")

        ssh_url_bar = manifest.get_project("ssh-url-bar.git")
        self.assertEquals(ssh_url_bar.fetch_url, "ssh://git@foo/ssh-url-bar.git")

        http_bar = manifest.get_project("http-bar.git")
        self.assertEquals(http_bar.fetch_url, "http://foo/http-bar.git")

        local_bar = manifest.get_project("local-bar.git")
        self.assertEquals(local_bar.fetch_url, "/path/to/foo/local-bar.git")


    def test_review_parse(self):
        xml = """
<manifest>
    <remote fetch="git@foo" review="http://gerrit"  />
    <project name="foo" review="true" />
    <project name="bar" />
</manifest>
"""
        xml_in = StringIO(xml)
        manifest = qisrc.manifest.load(xml_in)
        foo = manifest.get_project("foo")
        self.assertEqual(foo.review, True)
        self.assertEqual(foo.review_url, "http://gerrit/foo")

    def test_no_remote_fetch(self):
        xml = """
<manifest>
    <remote url="git@foo" />
    <project name="bar" />
</manifest>
"""
        xml_in = StringIO(xml)
        error = None
        try:
            qisrc.manifest.load(xml_in)
        except Exception, e:
            error = e
        self.assertFalse(error is None)
        self.assertTrue("remote must have a 'fetch' attribute" in str(error), error)

    def test_no_project_name(self):
        xml = """
<manifest>
    <remote fetch="git@foo" />
    <project />
</manifest>
"""
        xml_in = StringIO(xml)
        error = None
        try:
            qisrc.manifest.load(xml_in)
        except Exception, e:
            error = e
        self.assertFalse(error is None)
        self.assertTrue("project must have a 'name' attribute" in str(error), error)

    def test_no_project_path(self):
        xml = """
<manifest>
    <remote fetch="git@goo" />
    <project name="bar/foo.git" />
</manifest>
"""
        xml_in = StringIO(xml)
        manifest = qisrc.manifest.load(xml_in)
        project = manifest.get_project("bar/foo.git")
        self.assertEqual(project.path, "bar/foo")




def test_parse_other_remote(tmpdir):
    all_xml = """
<manifest>
  <remote fetch="ssh://git@all"
          review="http://gerrit" />
  <project name="a" review="true" />
  <project name="b" />
  <project name="private" />

</manifest>
"""

    other_xml = """
<manifest>
  <remote fetch="ssh://git@other" />
  <manifest url="all.xml" />
  <project name="c" />
</manifest>
"""

    all_manifest = tmpdir.join("all.xml")
    all_manifest.write(all_xml)
    other_manifest = tmpdir.join("other.xml")
    other_manifest.write(other_xml)

    all = qisrc.manifest.load(all_manifest.strpath)
    assert len(all.projects) == 3

    other = qisrc.manifest.load(other_manifest.strpath)
    assert len(other.projects) == 4
    c = other.get_project("c")
    assert c.fetch_url == "ssh://git@other/c"
    a = other.get_project("a")
    assert a.fetch_url == "ssh://git@all/a"

def test_parse_blacklist(tmpdir):
    all_xml = """
<manifest>
  <remote fetch="ssh://git@all"
          review="http://gerrit" />
  <project name="a" review="true" />
  <project name="b" />
  <project name="private" />

</manifest>
"""

    public_xml = """
<manifest>
  <manifest url="all.xml" />
  <blacklist name="private" />
</manifest>
"""

    all_manifest = tmpdir.join("all.xml")
    all_manifest.write(all_xml)
    public_manifest = tmpdir.join("public.xml")
    public_manifest.write(public_xml)

    all = qisrc.manifest.load(all_manifest.strpath)
    assert len(all.projects) == 3

    public = qisrc.manifest.load(public_manifest.strpath)
    assert len(public.projects) == 2


def test_parse_deep_recurse(tmpdir):
    a_xml = tmpdir.join("a.xml")
    a_xml.write("""
<manifest>
  <remote fetch="ssh://git@all" />
  <project name="a" />
  <manifest url="b.xml" />
</manifest>
""")

    b_xml = tmpdir.join("b.xml")
    b_xml.write("""
<manifest>
  <remote fetch="ssh://git@all" />
  <project name="b" />
  <manifest url="c.xml" />
</manifest>
""")


    c_xml = tmpdir.join("c.xml")
    c_xml.write("""
<manifest>
  <remote fetch="ssh://git@all" />
  <project name="c" />
</manifest>
""")

    a_manifest = qisrc.manifest.load(a_xml.strpath)

    assert len(a_manifest.projects) == 3



if __name__ == "__main__":
    unittest.main()
