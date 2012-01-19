#!/usr/bin/python

import xml.sax
import xml.sax.handler
from xml.sax.saxutils import quoteattr

import sys

class OsmHandler(xml.sax.handler.ContentHandler):
    def __init__(self, way_filter):
        self.in_nodes = self.in_ways = self.out_nodes = self.out_ways = 0

        self.node = self.way = None

        if " or " in way_filter and " and " in way_filter:
            raise Exception("Only one of ' or ' and ' and ' supported at the same time.")
        elif " or " in way_filter:
            way_filter_args = [f.split("=") for f in way_filter.split(" or ")]
            def way_filter_func(tag):
                for a in way_filter_args:
                    if tag[a[0]] == a[1]:
                        return True
                return False
        else:
            way_filter_args = [f.split("=") for f in way_filter.split(" and ")]
            def way_filter_func(tag):
                for a in way_filter_args:
                    if tag[a[0]] != a[1]:
                        return False
                return True
        self.way_filter_func = way_filter_func

    def startElement(self, name, attrs):
        if name == 'node':
            self.node = {'attrs': attrs, 'tags': []}
            self.in_nodes += 1
        elif name == 'way':
            self.way = {'attrs': attrs, 'nodes': [], 'tags': []}
            self.in_ways += 1
        elif name == 'tag':
            if self.node is not None:
                self.node['tags'].append(attrs)
            elif self.way is not None:
                self.way['tags'].append(attrs)
        elif name == 'nd':
            self.way['nodes'].append(attrs['ref'])
        elif name == 'osm':
            sys.stdout.write(("<osm version=%s generator=%s>\n" % (quoteattr(attrs['version']), quoteattr(attrs['generator']))).encode('utf-8'))

    def endElement(self, name):
        if name == 'node':
            sys.stdout.write(("<node %s>\n" % " ".join(["%s=%s" % (k, quoteattr(v)) for k, v in self.node['attrs'].items()])).encode('utf-8'))
            for tag in self.node['tags']:
                sys.stdout.write(("<tag k=%s v=%s />\n" % (quoteattr(tag['k']), quoteattr(tag['v']))).encode('utf-8'))
            sys.stdout.write("</node>\n".encode('utf-8'))
            self.out_nodes += 1
            self.node = None
        elif name == 'way':
            match = False
            for tag in self.way['tags']:
                if self.way_filter_func(tag):
                    match = True
                    break
            if match:
                sys.stdout.write(("<way %s>\n" % " ".join(["%s=%s" % (k, quoteattr(v)) for k, v in self.way['attrs'].items()])).encode('utf-8'))
                for nd in self.way['nodes']:
                    sys.stdout.write(("<nd ref=\"%s\" />\n" % nd).encode('utf-8'))
                for tag in self.way['tags']:
                    sys.stdout.write(("<tag k=%s v=%s />\n" % (quoteattr(tag['k']), quoteattr(tag['v']))).encode('utf-8'))
                sys.stdout.write("</way>\n".encode('utf-8'))
                self.out_ways += 1
            self.way = None
        elif name == 'osm':
            sys.stdout.write("</osm>\n".encode('utf-8'))

def parse(fileobj, way_filter):
    sys.stdout.write("<?xml version='1.0' encoding='UTF-8'?>\n".encode('utf-8'))
    handler = OsmHandler(way_filter)
    xml.sax.parse(fileobj, handler)

    sys.stderr.write("in_nodes: %s, in_ways: %s, out_nodes: %s, out_ways: %s\n"
                     % (handler.in_nodes, handler.in_ways, handler.out_nodes, handler.out_ways))

if __name__ == '__main__':
    parse(sys.stdin, sys.argv[1])
