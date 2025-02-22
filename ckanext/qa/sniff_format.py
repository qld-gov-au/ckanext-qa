# encoding: utf-8

from collections import defaultdict
import csv
import logging
import os
import re
import magic
import six
import subprocess
import xlrd
import zipfile

from ckan.plugins import toolkit

from . import lib


log = logging.getLogger(__name__)


def read_unknown_encoding(filepath, count, mode='r'):
    for encoding in ['utf-16', 'utf-8', 'iso-8859-1']:
        try:
            with open(filepath, mode=mode, encoding=encoding) as f:
                return f.read(count)
        except UnicodeError:
            pass
    else:
        log.debug("Unable to recognise char encoding of %s", filepath)
        return None


def sniff_file_format(filepath):
    '''For a given filepath, work out what file format it is.

    Returns a dict with format as a string, which is the format's canonical
    shortname (as defined by ckan's resource_formats.json) and a key that says
    if it is contained in a zip or something.

    e.g. {'format': 'CSV',
          'container': 'zip',
          }
    or None if it can\'t tell what it is.

    Note, log is a logger, either an RQ one or a standard Python logging
    one.
    '''
    format_ = None
    log.info('Sniffing file format of: %s', filepath)
    filepath_utf8 = filepath.encode('utf8') if isinstance(filepath, six.string_types) \
        else filepath
    mime_type = magic.from_file(filepath_utf8, mime=True)
    log.info('Magic detects file as: %s', mime_type)
    if mime_type:
        # some operating systems magic mime xml as text/xml
        if mime_type == 'application/xml' or mime_type == 'text/xml':
            buf = read_unknown_encoding(filepath, 5000)
            format_ = get_xml_variant_including_xml_declaration(buf)
        elif mime_type == 'application/zip':
            format_ = get_zipped_format(filepath)
        elif mime_type in ('application/msword', 'application/vnd.ms-office'):
            # In the past Magic gives the msword mime-type for Word and other
            # MS Office files too, so use BSD File to be sure which it is.
            format_ = run_bsd_file(filepath)
            if not format_ and is_excel(filepath):
                format_ = {'format': 'XLS'}
        elif mime_type == 'application/octet-stream':
            # Excel files sometimes come up as this
            if is_excel(filepath):
                format_ = {'format': 'XLS'}
            else:
                # e.g. Shapefile
                format_ = run_bsd_file(filepath)
            if not format_:
                with open(filepath, 'rb') as f:
                    buf = f.read(500)
                format_ = is_html(buf)
        elif mime_type == 'text/html':
            # Magic can mistake IATI for HTML
            buf = read_unknown_encoding(filepath, 100)
            if is_iati(buf):
                format_ = {'format': 'IATI'}
        elif mime_type == 'application/javascript':
            # Script-heavy HTML pages can be mistaken for JavaScript
            buf = read_unknown_encoding(filepath, 100)
            for tag in ['<!DOCTYPE html', '<html', '<head', '<body']:
                if tag in buf:
                    format_ = {'format': 'HTML'}
                    break

        if not format_:
            format_tuple = toolkit.h.resource_formats().get(mime_type)
            if format_tuple:
                format_ = {'format': format_tuple[1]}

        if not format_:
            if mime_type.startswith('text/') or mime_type == 'application/csv':
                # is it JSON?
                buf = read_unknown_encoding(filepath, 10000, mode='rtU')
                if is_json(buf):
                    format_ = {'format': 'JSON'}
                # is it CSV?
                elif is_csv(buf):
                    format_ = {'format': 'CSV'}
                elif is_psv(buf):
                    format_ = {'format': 'PSV'}

        if not format_:
            log.warning('Mimetype not recognised by CKAN as a data format: %s',
                        mime_type)

    if not format_ and is_excel(filepath):
        # Excel files sometimes not picked up by magic, so try alternative
        format_ = {'format': 'XLS'}

    # BSD file picks up some files that Magic misses
    # e.g. some MS Word files
    if not format_:
        format_ = run_bsd_file(filepath)

    if format_:
        log.info('Mimetype translates to filetype: %s',
                 format_['format'])

        if format_['format'] == 'TXT':
            # is it JSON?
            buf = read_unknown_encoding(filepath, 10000, mode='rtU')
            if is_json(buf):
                format_ = {'format': 'JSON'}
            # is it CSV?
            elif is_psv(buf):
                format_ = {'format': 'PSV'}
            elif is_csv(buf):
                format_ = {'format': 'CSV'}
            # XML files without the "<?xml ... ?>" tag end up here
            elif is_xml_but_without_declaration(buf):
                format_ = get_xml_variant_without_xml_declaration(buf)
            elif is_ttl(buf):
                format_ = {'format': 'TTL'}

        elif format_['format'] == 'HTML':
            # maybe it has RDFa in it
            buf = read_unknown_encoding(filepath, 100000)
            if has_rdfa(buf):
                format_ = {'format': 'RDFa'}
    else:
        log.warning('Could not detect format of file: %s', filepath)
    return format_


def is_json(buf):
    '''Returns whether this text buffer (potentially truncated) is in
    JSON format.'''
    string = '"[^"]*"'
    string_re = re.compile(string)
    number_re = re.compile(r'-?\d+(\.\d+)?([eE][+-]?\d+)?')
    extra_values_re = re.compile(r'true|false|null')
    object_start_re = re.compile(r'{%s:\s?' % string)
    object_middle_re = re.compile(r'%s:\s?' % string)
    object_end_re = re.compile(r'}')
    comma_re = re.compile(r',\s?')
    array_start_re = re.compile(r'\[')
    array_end_re = re.compile(r'\]')
    any_value_regexs = [string_re, number_re, object_start_re, array_start_re, extra_values_re]

    # simplified state machine - just looks at stack of object/array and
    # ignores contents of them, beyond just being simple JSON bits
    pos = 0
    state_stack = []  # stack of 'object', 'array'
    number_of_matches = 0
    while pos < len(buf):
        part_of_buf = buf[pos:]
        if pos == 0:
            potential_matches = (object_start_re, array_start_re, string_re, number_re, extra_values_re)
        elif not state_stack:
            # cannot have content beyond the first byte that is not nested
            return False
        elif state_stack[-1] == 'object':
            # any value
            potential_matches = [comma_re, object_middle_re, object_end_re] + any_value_regexs
        elif state_stack[-1] == 'array':
            # any value or end it
            potential_matches = any_value_regexs + [comma_re, array_end_re]
        for matcher in potential_matches:
            if matcher.match(part_of_buf):
                if matcher in any_value_regexs and state_stack and state_stack[-1] == 'comma':
                    state_stack.pop()
                if matcher == object_start_re:
                    state_stack.append('object')
                elif matcher == array_start_re:
                    state_stack.append('array')
                elif matcher in (object_end_re, array_end_re):
                    try:
                        state_stack.pop()
                    except IndexError:
                        # nothing to pop
                        log.info('Not JSON - %i matches', number_of_matches)
                        return False
                break
        else:
            # no match
            log.info('Not JSON - %i matches', number_of_matches)
            return False
        match_length = matcher.match(part_of_buf).end()
        # print("MATCHED %r %r %s" % (matcher.match(part_of_buf).string[:match_length], matcher.pattern, state_stack))
        pos += match_length
        number_of_matches += 1
        if number_of_matches > 5:
            log.info('JSON detected: %i matches', number_of_matches)
            return True

    log.info('JSON detected: %i matches', number_of_matches)
    return True


def is_csv(buf, **kwargs):
    return _is_spreadsheet(buf, 'CSV')


def is_psv(buf, **kwargs):
    return _is_spreadsheet(buf, 'PSV', '|')


def _extract_row_lengths(buf, format_, delimiter=None):
    # Return a list containing the count of cells in each row, if CSV
    row_lengths = []
    try:
        for row in csv.reader(six.StringIO(buf), delimiter=delimiter or ','):
            row_lengths.append(len(row))
        return row_lengths
    except csv.Error as e:
        log.info('Not %s - unable to parse as a table: %s', format_, e)
        return None


def _is_spreadsheet(buf, format_, delimiter=None):
    row_lengths = _extract_row_lengths(buf, format_, delimiter)
    if not row_lengths:
        return False

    def get_cells_per_row(num_cells, num_rows):
        if not num_rows:
            return 0
        return float(num_cells) / float(num_rows)
    num_cells = num_rows = 0
    for row in row_lengths:
        # Must have enough cells
        num_cells += row
        num_rows += 1
        if num_cells > 20 or num_rows > 10:
            cells_per_row = get_cells_per_row(num_cells, num_rows)
            # over the long term, 2 columns is the minimum
            if cells_per_row > 1.9:
                log.info('Is %s because %.1f cells per row (%i cells, %i rows)',
                         format_,
                         get_cells_per_row(num_cells, num_rows),
                         num_cells, num_rows)
                return True

    cells_per_row = get_cells_per_row(num_cells, num_rows)
    # if file is short then be more lenient
    if num_cells <= 5 or num_rows <= 2:
        if cells_per_row > 1.5:
            log.info('Is %s because %.1f cells per row (%i cells, %i rows)',
                     format_,
                     get_cells_per_row(num_cells, num_rows),
                     num_cells, num_rows)
            return True
    log.info('Not %s - not enough valid cells per row '
             '(%i cells, %i rows, %.1f cells per row)',
             format_, num_cells, num_rows, cells_per_row)
    return False


def is_html(buf):
    '''If this buffer is HTML, return that format type, else None.'''
    xml_re = r'.{0,3}\s*(<\?xml[^>]*>\s*)?(<!doctype[^>]*>\s*)?<html[^>]*>'
    match = re.match(xml_re, six.ensure_text(buf), re.IGNORECASE)
    if match:
        log.info('HTML tag detected')
        return {'format': 'HTML'}
    log.debug('Not HTML')


def is_iati(buf):
    '''If this buffer is IATI format, return that format type, else None.'''
    xml_re = r'.{0,3}\s*(<\?xml[^>]*>\s*)?(<!doctype[^>]*>\s*)?<iati-(activities|organisations)[^>]*>'
    match = re.match(xml_re, buf, re.IGNORECASE)
    if match:
        log.info('IATI tag detected')
        return {'format': 'IATI'}
    log.debug('Not IATI')


def is_xml_but_without_declaration(buf):
    '''Decides if this is a buffer of XML, but missing the usual <?xml ...?>
    tag.'''
    xml_re = r'.{0,3}\s*(<\?xml[^>]*>\s*)?(<!doctype[^>]*>\s*)?<([^>\s]*)([^>]*)>'
    match = re.match(xml_re, buf, re.IGNORECASE)
    if match:
        top_level_tag_name, top_level_tag_attributes = match.groups()[-2:]
        if ('xmlns:' not in top_level_tag_attributes
                and (len(top_level_tag_name) > 20
                     or len(top_level_tag_attributes) > 200)):
            log.debug('Not XML (without declaration) - unlikely length first tag: <%s %s>',
                      top_level_tag_name, top_level_tag_attributes)
            return False
        log.info('XML detected - first tag name: <%s>', top_level_tag_name)
        return True
    log.debug('Not XML (without declaration) - tag not detected')
    return False


def get_xml_variant_including_xml_declaration(buf):
    '''If this buffer is in a format based on XML and has the <xml>
    declaration, return the format type.'''
    return get_xml_variant_without_xml_declaration(buf)
    log.debug('XML declaration not found: %s', buf)


def get_xml_variant_without_xml_declaration(buf):
    '''If this buffer is in a format based on XML, without any XML declaration
    or other boilerplate, return the format type.'''
    # Parse the XML to find the first tag name.
    # Using expat directly, rather than go through xml.sax, since using I
    # couldn't see how to give it a string, so used StringIO which failed
    # for some files curiously.
    from xml.parsers import expat
    from xml.sax import SAXException

    class GotFirstTag(Exception):
        pass

    def start_element(name, attrs):
        raise GotFirstTag(name)
    p = expat.ParserCreate()
    p.StartElementHandler = start_element
    try:
        p.Parse(buf)
    except GotFirstTag as e:
        top_level_tag_name = six.text_type(e).lower()
    except (SAXException, expat.ExpatError) as e:
        log.info('Sax parse error: %s %s', e, buf)
        return {'format': 'XML'}

    log.info('Top level tag detected as: %s', top_level_tag_name)
    top_level_tag_name = top_level_tag_name.replace('rdf:rdf', 'rdf')
    top_level_tag_name = top_level_tag_name.replace('wms_capabilities', 'wms')  # WMS 1.3
    top_level_tag_name = top_level_tag_name.replace('wmt_ms_capabilities', 'wms')  # WMS 1.1.1
    top_level_tag_name = re.sub('wfs:.*', 'wfs', top_level_tag_name)  # WFS 2.0
    top_level_tag_name = top_level_tag_name.replace('wfs_capabilities', 'wfs')  # WFS 1.0/1.1
    top_level_tag_name = top_level_tag_name.replace('feed', 'atom feed')
    if top_level_tag_name.lower() == 'capabilities' and \
            'xmlns="http://www.opengis.net/wmts/' in buf:
        top_level_tag_name = 'wmts'
    if top_level_tag_name.lower() in ('coveragedescriptions', 'capabilities') and \
            'xmlns="http://www.opengis.net/wcs/' in buf:
        top_level_tag_name = 'wcs'
    format_tuple = toolkit.h.resource_formats().get(top_level_tag_name)
    if format_tuple:
        format_ = {'format': format_tuple[1]}
        log.info('XML variant detected: %s', format_tuple[2])
        return format_
    log.warning('Did not recognise XML format: %s', top_level_tag_name)
    return {'format': 'XML'}


def has_rdfa(buf):
    '''If the buffer HTML contains RDFa then this returns True'''
    # quick check for the key words
    if 'about=' not in buf or 'property=' not in buf:
        log.debug('Not RDFA')
        return False

    # more rigorous check for them as tag attributes
    about_re = r'<[^>]+\sabout="[^"]+"[^>]*>'
    property_re = r'<[^>]+\sproperty="[^"]+"[^>]*>'
    # remove CR to catch tags spanning more than one line
    # buf = re.sub('\r\n', ' ', buf)
    if not re.search(about_re, buf):
        log.debug('Not RDFA')
        return False
    if not re.search(property_re, buf):
        log.debug('Not RDFA')
        return False
    log.info('RDFA tags found in HTML')
    return True


def get_zipped_format(filepath):
    '''For a given zip file, return the format of file inside.
    For multiple files, choose by the most open, and then by the most
    popular extension.'''
    # just check filename extension of each file inside
    try:
        with zipfile.ZipFile(filepath, 'r') as zip:
            filepaths = zip.namelist()
    except zipfile.BadZipfile as e:
        log.info('Zip file open raised error %s: %s',
                 e, e.args)
        return
    except Exception as e:
        log.warning('Zip file open raised exception %s: %s',
                    e, e.args)
        return

    # Shapefile check - a Shapefile is a zip containing specific files:
    # .shp, .dbf and .shx amongst others
    extensions = set([f.split('.')[-1].lower() for f in filepaths])
    if len(extensions & set(('shp', 'dbf', 'shx'))) == 3:
        log.info('Shapefile detected')
        return {'format': 'SHP'}

    # GTFS check - a GTFS is a zip which containing specific filenames
    filenames = set((os.path.basename(f) for f in filepaths))
    if not (set(('agency.txt', 'stops.txt', 'routes.txt', 'trips.txt',
                 'stop_times.txt', 'calendar.txt')) - set(filenames)):
        log.info('GTFS detected')
        return {'format': 'GTFS'}

    top_score = 0
    top_scoring_extension_counts = defaultdict(int)  # extension: number_of_files
    for filepath in filepaths:
        extension = os.path.splitext(filepath)[-1][1:].lower()
        format_tuple = toolkit.h.resource_formats().get(extension)
        if format_tuple:
            score = lib.resource_format_scores().get(format_tuple[1])
            if score is not None and score > top_score:
                top_score = score
                top_scoring_extension_counts = defaultdict(int)
            if score == top_score:
                top_scoring_extension_counts[extension] += 1
        else:
            log.info('Zipped file of unknown extension: "%s" (%s)',
                     extension, filepath)
    if not top_scoring_extension_counts:
        log.info('Zip has no known extensions: %s', filepath)
        return {'format': 'ZIP'}

    top_scoring_extension_counts = sorted(top_scoring_extension_counts.items(),
                                          key=lambda x: x[1])
    top_extension = top_scoring_extension_counts[-1][0]
    log.info('Zip file\'s most popular extension is "%s" (All extensions: %r)',
             top_extension, top_scoring_extension_counts)
    format_tuple = toolkit.h.resource_formats()[top_extension]
    format_ = {'format': format_tuple[1],
               'container': 'ZIP'}
    log.info('Zipped file format detected: %s', format_tuple[2])
    return format_


def is_excel(filepath):
    try:
        xlrd.open_workbook(filepath)
    except Exception as e:
        log.info('Not Excel - failed to load: %s %s', e, e.args)
        return False
    else:
        log.info('Excel file opened successfully')
        return True


# same as the python 2.7 subprocess.check_output
def check_output(*popenargs, **kwargs):
    if 'stdout' in kwargs:
        raise ValueError('stdout argument not allowed, it will be overridden.')
    process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise Exception('Non-zero exit status %s: %s' % (retcode, output))
    return six.text_type(output)


def run_bsd_file(filepath):
    '''Run the BSD command-line tool "file" to determine file type. Returns
    a format dict or None if it fails.'''
    result = check_output(['file', filepath])
    match = re.search('Name of Creating Application: ([^,]*),', result)
    if match:
        app_name = match.groups()[0]
        format_map = {'Microsoft Office PowerPoint': 'ppt',
                      'Microsoft PowerPoint': 'ppt',
                      'Microsoft Excel': 'xls',
                      'Microsoft Office Word': 'doc',
                      'Microsoft Word 10.0': 'doc',
                      'Microsoft Macintosh Word': 'doc',
                      }
        if app_name in format_map:
            extension = format_map[app_name]
            format_tuple = toolkit.h.resource_formats()[extension]
            log.info('"file" detected file format: %s',
                     format_tuple[2])
            return {'format': format_tuple[1]}
    match = re.search(': ESRI Shapefile', result)
    if match:
        format_ = {'format': 'SHP'}
        log.info('"file" detected file format: %s',
                 format_['format'])
        return format_
    log.info('"file" could not determine file format of "%s": %s',
             filepath, result)


def is_ttl(buf):
    '''If the buffer is a Turtle RDF file then return True.'''
    # Turtle spec: "Turtle documents may have the strings '@prefix' or '@base' (case dependent) near the beginning of the document."
    at_re = '^@(prefix|base) '
    match = re.search(at_re, buf, re.MULTILINE)
    if match:
        log.info('Turtle RDF detected - @prefix or @base')
        return True

    # Alternatively look for several triples
    num_required_triples = 5
    ignore, num_replacements = turtle_regex().subn('', buf, num_required_triples)
    if num_replacements >= num_required_triples:
        log.info('Turtle RDF detected - %s triples' % num_replacements)
        return True

    log.debug('Not Turtle RDF - triples not detected (%i)' % num_replacements)


turtle_regex_ = None


def turtle_regex():
    '''Return a compiled regex that matches a turtle triple.

    Each RDF term may be in these forms:
         <url>
         "a literal"
         "translation"@ru
         "literal typed"^^<http://www.w3.org/2001/XMLSchema#string>
         "literal typed with prefix"^^xsd:string
         'single quotes'
         """triple \n quotes"""
         -4.2E-9
         false
         _:blank_node
     No need to worry about prefixed terms, since there would have been a
     @prefix already detected for them to be used.
         prefix:term  :blank_prefix
     does not support nested blank nodes, collection, sameas ('a' token)
    '''
    global turtle_regex_
    if not turtle_regex_:
        rdf_term = r'(<[^ >]+>|_:\S+|".+?"(@\w+)?(\^\^\S+)?|\'.+?\'(@\w+)?(\^\^\S+)?|""".+?"""(@\w+)' \
                   r'?(\^\^\S+)?|\'\'\'.+?\'\'\'(@\w+)?(\^\^\S+)?|[+-]?([0-9]+|[0-9]*\.[0-9]+)(E[+-]?[0-9]+)?|false|true)'

        # simple case is: triple_re = '^T T T \.$'.replace('T', rdf_term)
        # but extend to deal with multiple predicate-objects:
        # triple = '^T T T\s*(;\s*T T\s*)*\.\s*$'.replace('T', rdf_term).replace(' ', '\s+')
        triple = r'(^T|;)\s*T T\s*(;|\.\s*$)'.replace('T', rdf_term).replace(' ', r'\s+')
        turtle_regex_ = re.compile(triple, re.MULTILINE)
    return turtle_regex_
