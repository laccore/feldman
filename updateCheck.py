# check GitHub repo for latest version

import distutils
import requests
import unittest

from distutils.version import StrictVersion
from urllib.parse import quote

HOST = "https://api.github.com/"
PATH = "repos/laccore/feldman/releases/latest"

def request(host, path, url_params=None):
    url_params = url_params or {}
    url = '{0}{1}'.format(host, quote(path.encode('utf8')))
    response = requests.request('GET', url, params=url_params)

    return response.json()

def cmpVersions(v1, v2):
    tv1 = StrictVersion(trim_version_suffix(v1))
    tv2 = StrictVersion(trim_version_suffix(v2))
    if tv1 < tv2:
        return -1
    elif tv1 == tv2:
        return 0
    elif tv1 > tv2:
        return 1

def trim_version_suffix(version):
    for c in ['-', '_', ' ']:
        idx = version.find(c)
        if idx != -1:
            version = version[:idx]
    return version

def getLatestGithubRelease():
    response = request(HOST, PATH)
    return response["tag_name"], response["html_url"]

class Tests(unittest.TestCase):
    def testTrim(self):
        self.assertTrue(trim_version_suffix("1.0") == "1.0")
        self.assertTrue(trim_version_suffix("1.0.1") == "1.0.1")
        self.assertTrue(trim_version_suffix("1.0 ") == "1.0")
        self.assertTrue(trim_version_suffix("1.0-b1") == "1.0")
        self.assertTrue(trim_version_suffix("1.0_alpha_10") == "1.0")
        self.assertTrue(trim_version_suffix("1.0 _-suffix") == "1.0")
        self.assertTrue(trim_version_suffix("1.0     _ 2.3.4-foobar") == "1.0")

if __name__ == "__main__":
    #unittest.main()
    response = request(HOST, PATH)
    # then get tag_name from json
    print(response['tag_name'])
