# -*- coding: utf-8 -*-

import StringIO
from ast import literal_eval
import re
import time
from flask import render_template, url_for, request, redirect, send_file, abort
from sage.misc.cachefunc import cached_function
from sage.misc.cachefunc import cached_method

from lmfdb.db_backend import db
from lmfdb.utils import to_dict, comma, flash_error
from lmfdb.search_parsing import parse_ints, parse_bracketed_posints
from lmfdb.search_wrapper import search_wrap
from lmfdb.belyi import belyi_page
from lmfdb.belyi.web_belyi import WebBelyiGalmap, WebBelyiPassport #, belyi_db_galmaps, belyi_db_passports

credit_string = "Michael Musty, Sam Schiavone, and John Voight"

###############################################################################
# global database connection and stats objects
###############################################################################

the_belyistats = None
def belyistats():
    global the_belyistats
    if the_belyistats is None:
        the_belyistats = belyi_stats()
    return the_belyistats

###############################################################################
# List and dictionaries needed routing and searching
###############################################################################

from web_belyi import geomtypelet_to_geomtypename_dict as geometry_types_dict
geometry_types_list = geometry_types_dict.keys()


###############################################################################
# Routing for top level, random, and stats
###############################################################################

def learnmore_list():
    return [('Completeness of the data', url_for(".completeness_page")),
            ('Source of the data', url_for(".how_computed_page")),
            ('Belyi labels', url_for(".labels_page"))]

# Return the learnmore list with the matchstring entry removed
def learnmore_list_remove(matchstring):
    return filter(lambda t:t[0].find(matchstring) <0, learnmore_list())

@belyi_page.route("/")
def index():
    if len(request.args) > 0:
        return belyi_search(to_dict(request.args))
    info = {'counts' : belyistats().counts()}
    info["stats_url"] = url_for(".statistics")
    info["belyi_galmap_url"] =  lambda label: url_for_belyi_galmap_label(label)
    belyi_galmap_labels = ('7T6-[7,4,4]-7-421-421-g1-b','7T7-[7,12,12]-7-43-43-g2-d', '7T5-[7,7,3]-7-7-331-g2-a', '6T15-[5,5,5]-51-51-51-g1-a', '7T7-[6,6,6]-61-61-322-g1-a')
    info["belyi_galmap_list"] = [ {'label':label,'url':url_for_belyi_galmap_label(label)} for label in belyi_galmap_labels ]
    info["degree_list"] = ('1-6', '7-8', '9-10','10-100')
    info['title'] = title =  'Belyi maps'
    info['bread'] = bread = [('Belyi Maps', url_for(".index"))]

    #search options
    info['geometry_types_list'] = geometry_types_list
    info['geometry_types_dict'] = geometry_types_dict

    return render_template("belyi_browse.html", info=info, credit=credit_string, title=title, learnmore=learnmore_list(), bread=bread)

@belyi_page.route("/random")
def random_belyi_galmap():
    label = db.belyi_galmaps.random()
    return redirect(url_for_belyi_galmap_label(label), 307)

@belyi_page.route("/stats")
def statistics():
    info = { 'counts': belyistats().counts(), 'stats': belyistats().stats() }
    title = 'Belyi maps: statistics'
    bread = (('Belyi Maps', url_for(".index")), ('Statistics', ' '))
    return render_template("belyi_stats.html", info=info, credit=credit_string, title=title, bread=bread, learnmore=learnmore_list())

###############################################################################
# Galmaps, passports, triples and groups routes
###############################################################################

@belyi_page.route("/<group>/<abc>/<sigma0>/<sigma1>/<sigmaoo>/<g>/<letnum>")
def by_url_belyi_galmap_label(group, abc, sigma0, sigma1, sigmaoo, g, letnum):
    label = group+"-"+abc+"-"+sigma0+"-"+sigma1+"-"+sigmaoo+"-"+g+"-"+letnum
    return render_belyi_galmap_webpage(label)

@belyi_page.route("/<group>/<abc>/<sigma0>/<sigma1>/<sigmaoo>/<g>")
def by_url_belyi_passport_label(group, abc, sigma0, sigma1, sigmaoo, g):
    label = group+"-"+abc+"-"+sigma0+"-"+sigma1+"-"+sigmaoo+"-"+g
    return render_belyi_passport_webpage(label)

@belyi_page.route("/<group>/<abc>")
def by_url_belyi_search_group_triple(group, abc):
    info = to_dict(request.args)
    info['title'] = 'Belyi maps with group %s and orders %s' % (group, abc)
    info['bread'] = [('Belyi Maps', url_for(".index")), ('%s' % group, url_for(".by_url_belyi_search_group", group=group)), ('%s' % abc, url_for(".by_url_belyi_search_group_triple", group=group, abc=abc)) ]
    if len(request.args) > 0:
        # if group or abc changed, fall back to a general search
        if 'group' in request.args and (request.args['group'] != str(group) or request.args['abc_list'] != str(abc)):
            return redirect (url_for(".index", **request.args), 307)
        info['title'] += ' search results'
        info['bread'].append(('search results',''))
    info['group'] = group
    info['abc_list'] = abc
    return belyi_search(info)



@belyi_page.route("/<smthorlabel>")
def by_url_belyi_search_url(smthorlabel):
    split = smthorlabel.split('-')
    # strip out the last field if empty
    if split[-1] == '':
        split = split[:-1]
    if len(split) == 1:
        return by_url_belyi_search_group(group = split[0])
    elif len(split) <= 5:
        # not all the sigmas and g
        return redirect(url_for(".by_url_belyi_search_group_triple", group = split[0], abc = split[1]), 301)
    elif len(split) == 6:
        return redirect( url_for(".by_url_belyi_passport_label", group = split[0], abc = split[1], sigma0 = split[2], sigma1 = split[3], sigmaoo = split[4], g = split[5]), 301)
    elif len(split) == 7:
        return redirect( url_for(".by_url_belyi_galmap_label", group = split[0], abc = split[1], sigma0 = split[2], sigma1 = split[3], sigmaoo = split[4], g = split[5], letnum = split[6]), 301)

@belyi_page.route("/<group>")
def by_url_belyi_search_group(group):
    info = to_dict(request.args)
    info['title'] = 'Belyi maps with group %s' % group
    info['bread'] = [('Belyi Maps', url_for(".index")), ('%s' % group, url_for(".by_url_belyi_search_group", group=group))]
    if len(request.args) > 0:
        # if the group changed, fall back to a general search
        if 'group' in request.args and request.args['group'] != str(group):
            return redirect (url_for(".index", **request.args), 307)
        info['title'] += ' search results'
        info['bread'].append(('search results',''))
    info['group'] = group
    return belyi_search(info)




def render_belyi_galmap_webpage(label):
    try:
        belyi_galmap = WebBelyiGalmap.by_label(label)
    except (KeyError,ValueError) as err:
        return abort(404,err.args)
    return render_template("belyi_galmap.html",
                           properties2=belyi_galmap.properties,
                           credit=credit_string,
                           info={},
                           data=belyi_galmap.data,
                           code=belyi_galmap.code,
                           bread=belyi_galmap.bread,
                           learnmore=learnmore_list(),
                           title=belyi_galmap.title,
                           friends=belyi_galmap.friends)

def render_belyi_passport_webpage(label):
    try:
        belyi_passport = WebBelyiPassport.by_label(label)
    except (KeyError,ValueError) as err:
        return abort(404,err.args)
    return render_template("belyi_passport.html",
                           properties2=belyi_passport.properties,
                           credit=credit_string,
                           data=belyi_passport.data,
                           bread=belyi_passport.bread,
                           learnmore=learnmore_list(),
                           title=belyi_passport.title,
                           friends=belyi_passport.friends)

def url_for_belyi_galmap_label(label):
    slabel = label.split("-")
    return url_for(".by_url_belyi_galmap_label", group=slabel[0], abc=slabel[1], sigma0=slabel[2], sigma1=slabel[3], sigmaoo=slabel[4], g=slabel[5], letnum=slabel[6])

def url_for_belyi_passport_label(label):
    slabel = label.split("-")
    return url_for(".by_url_belyi_passport_label", group=slabel[0], abc=slabel[1], sigma0=slabel[2], sigma1=slabel[3], sigmaoo=slabel[4], g=slabel[5])

def belyi_passport_from_belyi_galmap_label(label):
    return '-'.join(label.split("-")[:-1])


################################################################################
# Searching
################################################################################

def belyi_jump(info):
    jump = info["jump"].strip()
    if re.match(r'^\d+T\d+-\[\d+,\d+,\d+\]-\d+-\d+-\d+-g\d+-[a-z]+$', jump):
        return redirect(url_for_belyi_galmap_label(jump), 301)
    else:
        if re.match(r'^\d+T\d+-\[\d+,\d+,\d+\]-\d+-\d+-\d+-g\d+$', jump):
            return redirect(url_for_belyi_passport_label(jump), 301)
        else:
            errmsg = "%s is not a valid Belyi map or passport label"
    flash_error (errmsg, jump)
    return redirect(url_for(".index"))

def download_search(info):
    download_comment_prefix = {'magma':'//','sage':'#','gp':'\\\\','text':'#'}
    download_assignment_defn = {'magma':':=','sage':' = ','gp':' = ' ,'text':'='}
    delim_start = {'magma':'[*','sage':'[','gp':'[','text':' ['}
    delim_end = {'magma':'*]','sage':']','gp':']','text':' ]'}
    start_and_end = {'magma':['[*','*];'],'sage':['[','];'],'gp':['{[',']}'],'text':['[','];']}
    file_suffix = {'magma':'.m','sage':'.sage','gp':'.gp','text':'.txt'}
    lang = info.get('Submit','text').strip()
    filename = 'belyi_maps' + file_suffix[lang]
    mydate = time.strftime("%d %B %Y")
    start = delim_start[lang]
    end = delim_end[lang]
    # reissue query here
    try:
        res = db.belyi_galmaps.search(
                literal_eval(info.get('query','{}')),
                projection = ['label', 'triples'],
                )
    except Exception as err:
        return "Unable to parse query: %s"%err
    # list of labels and triples

    def coerce_triples(triples):
        deg = len(triples[0][0])
        if lang == 'sage':
            return '[' +',\n'.join(["map(SymmetricGroup(%d), %s)" % (deg, s) for s in triples]) + ']'
        elif lang == "magma":
            return '[' + ',\n'.join([
                '[' +
                ',\n'.join( ["Sym(%d) ! %s" % (deg, t) for t in s])
                + ']'
                for s in triples
                ]) + ']'

            return '[' +',\n'.join(["Sym(%d) ! %s" % (deg, s) for s in triples]) + ']'
        else:
            return str(triples)


    res_list = [
            start +
            str(r['label']).__repr__().replace("'","\"") +
            ", " + coerce_triples(r['triples']) +
            end
            for r in res
            ]
    c = download_comment_prefix[lang]
    s =  '\n'
    s += c + ' Belyi maps downloaded from the LMFDB, downloaded on %s.\n'% mydate
    s += c + ' Query "%s" returned %d maps.\n\n' %(str(info.get('query')), len(res_list))
    s += c + ' Below is a list called data. Each entry has the form:\n'
    s += c + '   [label, permutation_triples]\n'
    s += c + ' where the permutation triples are in one line notation\n'
    s += c + '\n'
    s += '\n'
    s += 'data ' + download_assignment_defn[lang] + start_and_end[lang][0] + '\\\n'
    s += str(',\n'.join(res_list))
    s += start_and_end[lang][1]
    s += '\n\n'
    strIO = StringIO.StringIO()
    strIO.write(s)
    strIO.seek(0)
    return send_file(strIO, attachment_filename=filename, as_attachment=True, add_etags=False)

@search_wrap(template="belyi_search_results.html",
             table=db.belyi_galmaps,
             title='Belyi map search results',
             err_title='Belyi Maps Search Input Error',
             shortcuts={'jump':belyi_jump,
                        'download':download_search},
             projection=['label', 'group', 'deg', 'g', 'orbit_size', 'geomtype'],
             cleaners={'geomtype': lambda v:geometry_types_dict[v['geomtype']]},
             bread=lambda:[('Belyi Maps', url_for(".index")), ('Search Results', '.')],
             credit=lambda:credit_string,
             learnmore=learnmore_list)
def belyi_search(info, query):
    info['geometry_types_list'] = geometry_types_list
    info['geometry_types_dict'] = geometry_types_dict
    info["belyi_galmap_url"] = lambda label: url_for_belyi_galmap_label(label)
    if 'group' in query:
        info['group'] = query['group']
    parse_bracketed_posints(info, query, 'abc_list', 'a, b, c', maxlength=3)
    if query.get('abc_list'):
        if len(query['abc_list']) == 3:
            a, b, c = sorted(query['abc_list'])
            query['a_s'] = a
            query['b_s'] = b
            query['c_s'] = c
        elif len(query['abc_list']) == 2:
            a, b = sorted(query['abc_list'])
            sub_query = []
            sub_query.append( {'a_s': a, 'b_s': b} )
            sub_query.append( {'b_s': a, 'c_s': b} )
            query['$or'] = sub_query
        elif len(query['abc_list']) == 1:
            a = query['abc_list'][0]
            query['$or'] = [{'a_s': a}, {'b_s': a}, {'c_s': a}]
        query.pop('abc_list')

    # a naive hack
    if info.get('abc'):
        for elt in ['a_s', 'b_s', 'c_s']:
            info_hack = {}
            info_hack[elt] = info['abc']
            parse_ints(info_hack, query, elt)

    parse_ints(info, query, 'g','g')
    parse_ints(info, query, 'deg', 'deg')
    parse_ints(info, query, 'orbit_size', 'orbit_size')
    # invariants and drop-list items don't require parsing -- they are all strings (supplied by us, not the user)
    for fld in ['geomtype','group']:
        if info.get(fld):
            query[fld] = info[fld]

################################################################################
# Statistics
################################################################################

stats_attribute_list = [
    {'name':'deg','top_title':'Degree','row_title':'deg','knowl':'belyi.degree','avg':True},
    {'name':'orbit_size','top_title':'Galois orbit size','row_title':'size','knowl':'belyi.orbit_size','avg':True},
    {'name':'g','top_title':'Genus','row_title':'genus','knowl':'belyi.genus','avg':True}
]

class belyi_stats(object):
    """
    Class for creating and displaying statistics for Belyi maps
    """


    @cached_method
    def counts(self):
        counts = {}
        ngalmaps = db.belyi_galmaps.stats.count()
        counts['ngalmaps']  = ngalmaps
        counts['ngalmaps_c'] = comma(ngalmaps)

        npassports =  db.belyi_passports.stats.count()
        counts['npassports'] = npassports
        counts['npassports_c'] = comma(npassports)
        max_deg = db.belyi_passports.max('deg')
        counts['max_deg'] = max_deg
        counts['max_deg_c'] = comma(max_deg)
        return counts

    @cached_method
    def stats(self):
        dists = []
        for attr in stats_attribute_list:
            counts = db.belyi_galmaps.stats.display_data([attr["name"]],
                                                      url_for(".index"),
                                                      include_avg=attr.get("avg",False),
                                                      formatter=attr.get("format"),
                                                      # artifact from copy and paste
                                                      count_key='curves')
            rows = [counts[i:i+10] for i in range(0,len(counts),10)]
            dists.append({'attribute':attr,'rows':rows})
        return {"distributions": dists}

#        galmaps = belyi_db_galmaps()
#        self.init_belyi_count()
#        counts = self._counts
#        total = counts["ngalmaps"]
#        stats = {}
#        dists = []
#        # TODO use aggregate $group to speed this up and/or just store these counts in the database
#        for attr in stats_attribute_list:
#            counts = 100 #FIXME attribute_value_counts(galmaps, attr['name'])
#            counts = [c for c in counts if c[0] != None]
#            if len(counts) == 0:
#                continue
#            vcounts = []
#            rows = []
#            avg = 0
#            total = sum([c[1] for c in counts])
#            for value,n in counts:
#                prop = format_percentage(n,total)
#                if 'avg' in attr and attr['avg'] and (type(value) == int or type(value) == float):
#                    avg += n*value
#                value_string = attr['format'](value) if 'format' in attr else value
#                vcounts.append({'value': value_string, 'curves': n, 'query':url_for(".index")+'?'+attr['name']+'='+str(value),'proportion': prop})
#                if len(vcounts) == 10:
#                    rows.append(vcounts)
#                    vcounts = []
#            if len(vcounts):
#                rows.append(vcounts)
#            if 'avg' in attr and attr['avg']:
#                vcounts.append({'value':'\(\\mathrm{avg}\\ %.2f\)'%(float(avg)/total), 'galmaps':total, 'query':url_for(".index") +'?'+attr['name'],'proportion':format_percentage(1,1)})
#            dists.append({'attribute':attr,'rows':rows})
#        stats["distributions"] = dists
#        self._stats = stats

@belyi_page.route("/Completeness")
def completeness_page():
    t = 'Completeness of Belyi map data'
    bread = (('Belyi Maps', url_for(".index")), ('Completeness',''))
    return render_template("single.html", kid='dq.belyi.extent',
                           credit=credit_string, title=t, bread=bread, learnmore=learnmore_list_remove('Completeness'))

@belyi_page.route("/Source")
def how_computed_page():
    t = 'Source of Belyi map data'
    bread = (('Belyi Maps', url_for(".index")), ('Source',''))
    return render_template("single.html", kid='dq.belyi.source',
                           credit=credit_string, title=t, bread=bread, learnmore=learnmore_list_remove('Source'))

@belyi_page.route("/Labels")
def labels_page():
    t = 'Labels for Belyi maps'
    bread = (('Belyi Maps', url_for(".index")), ('Labels',''))
    return render_template("single.html", kid='belyi.label',
                           credit=credit_string, title=t, bread=bread, learnmore=learnmore_list_remove('labels'))
