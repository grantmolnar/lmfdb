# -*- coding: utf8 -*-
from lmfdb.base import LmfdbTest

class BelyiTest(LmfdbTest):

    def check_args(self, path, text):
        L = self.tc.get(path, follow_redirects=True)
        if isinstance(text, list):
            for elt in text:
                assert elt in L.data
        else:
            assert text in L.data


    ######## all tests should pass

    def test_main(self):
        self.check_args('/Belyi/', ['Belyi maps', 'proportion'])

    def test_stats(self):
        self.check_args('/Belyi/stats', ['number of maps', 'proportion'])

    def test_learn_more_about(self):
        self.check_args('/Belyi/Completeness', 'Completeness of Belyi map data')
        self.check_args('/Belyi/Source', 'Source of Belyi map data')
        self.check_args('/Belyi/Labels', 'Labels for Belyi maps')


    def test_random(self):
        self.check_args('/Belyi/random', 'Monodromy group')

    def test_by_galmap_label(self):
        self.check_args('/Belyi/6T15-[5,4,4]-51-42-42-g1-b', 'A_6')

    def test_passport_label(self):
        self.check_args('/Belyi/5T4-[5,3,3]-5-311-311-g0-a', '5T4-[5,3,3]-5-311-311-g0')

    def test_passport(self):
        self.check_args('/Belyi/9T33-[10,15,2]-522-531-22221-g0-a', '3.1.14175.1')

    ######## web pages

    def test_urls(self):
        self.check_args('/Belyi/4T5-[4,3,2]-4-31-211-g0-a', 'Belyi map 4T5-[4,3,2]-4-31-211-g0-a')
        self.check_args('/Belyi/4T5-[4,3,2]-4-31-211-g0-', 'Passport 4T5-[4,3,2]-4-31-211-g0')
        self.check_args('/Belyi/4T5-[4,3,2]-4-31-211-g0', 'Passport 4T5-[4,3,2]-4-31-211-g0')
        self.check_args('/Belyi/4T5-[4,3,2]-4-31-211-', 'Belyi maps with group 4T5 and orders [4,3,2]')
        self.check_args('/Belyi/4T5-[4,3,2]-4-31-', 'Belyi maps with group 4T5 and orders [4,3,2]')
        self.check_args('/Belyi/4T5-[4,3,2]', 'Belyi maps with group 4T5')

    ######## searches

    def test_deg_range(self):
        L = self.tc.get('/Belyi/?deg=2-7')
        assert '5T4-[5,3,3]-5-311-311-g0-a' in L.data

    def test_group_search(self):
        self.check_args('/Belyi/?group=7T5', '7T5-[7,7,3]-7-7-331-g2-a')

    def test_abc_search(self):
        self.check_args('/Belyi/?abc=2-4', '6T10-[4,4,3]-42-42-33-g1-a')

    def test_abc_list_search(self):
        self.check_args('/Belyi/?abc_list=[7,6,6]', '7T7-[7,6,6]-7-3211-3211-g0-a')
        self.check_args('/Belyi/?abc_list=[4,3]', ['4T5-[4,3,2]-4-31-211-g0-a', '7T6-[4,6,3]-421-322-331-g0-a', '8T50-[10,3,4]-521-3311-422-g0-a'])
        self.check_args('/Belyi/?abc_list=[4]', ['5T5-[5,6,4]-5-32-41-g1-a', '4T3-[4,2,2]-4-22-211-g0-a'])

    def test_genus_search(self):
        self.check_args('/Belyi/?genus=2', '6T6-[6,6,3]-6-6-33-g2-a')

    def test_orbit_size_search(self):
        self.check_args('/Belyi/?orbit_size=20-', '7T7-[6,10,4]-61-52-421-g1-a')

    def test_geom_type_search(self):
        self.check_args('/Belyi/?geomtype=H', '6T8-[4,4,3]-411-411-33-g0-a')

    def test_count_search(self):
        self.check_args('/Belyi/?count=20', '5T1-[5,5,5]-5-5-5-g2-c')

    def test_bread_and_then_search(self):
        self.check_args('/Belyi/7T6?group=7T3', '7T3-[3,3,3]-331-331-331-g0-a')
        self.check_args('/Belyi/7T6/%5B4%2C4%2C3%5D?group=7T3', '7T3-[3,3,3]-331-331-331-g0-a')

    def test_bread(self):
        self.check_args('/Belyi/7T7', ['Belyi maps with group 7T7', '7T7-[10,10,2]-52-52-22111-g0-a'])
        self.check_args('/Belyi/7T6/%5B4%2C4%2C6%5D', ['Belyi maps with group 7T6 and orders [4,4,6]', '7T6-[4,4,6]-421-421-322-g0-a'])

    def test_label_jump(self):
        self.check_args('/Belyi/?jump=maria', 'Error: maria is not a valid Belyi map or passport label')
        self.check_args('/Belyi/?jump=7T6-[7,4,4]-7-421-421-g1-b', 'Belyi map 7T6-[7,4,4]-7-421-421-g1-b')
        self.check_args('/Belyi/?jump=7T6-[7,4,4]-7-421-421-g1', 'Passport 7T6-[7,4,4]-7-421-421-g1')


    def test_downloads(self):
        text = "Belyi maps downloaded from the LMFDB"
        for lang in ['gp', 'magma', 'sage']:
            self.check_args('/Belyi/?group=7T5&download=%s' % lang, [text, '7T5-[7,7,3]-7-7-331-g2-a'])
            self.check_args('/Belyi/?genus=2&download=%s', [text, '6T6-[6,6,3]-6-6-33-g2-a'])
            self.check_args('/Belyi/?abc=2-4&download=%s' % lang, [text, '6T10-[4,4,3]-42-42-33-g1-a'])
            self.check_args('/Belyi/?abc_list=[7,6,6]&download=%s' % lang, [text, '7T7-[7,6,6]-7-3211-3211-g0-a'])
