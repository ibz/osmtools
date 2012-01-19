#!/usr/bin/python

import xml.sax
import xml.sax.handler
from xml.sax.saxutils import quoteattr

import sys

class UsedNodesHandler(xml.sax.handler.ContentHandler):
    def __init__(self):
        self.used_nodes = set()

    def startElement(self, name, attrs):
        if name == 'nd':
            self.used_nodes.add(int(attrs['ref']))

class OsmHandler(xml.sax.handler.ContentHandler):
    def __init__(self, used_nodes):
        self.in_nodes = self.out_nodes = 0

        self.node = None

        self.used_nodes = used_nodes

    def startElement(self, name, attrs):
        if name == 'node':
            self.node = {'attrs': attrs, 'used': int(attrs['id']) in self.used_nodes, 'tags': []}
            self.in_nodes += 1
        elif name == 'tag':
            if self.node is not None:
                self.node['tags'].append(attrs)
            else:
                sys.stdout.write(("<tag k=%s v=%s />\n" % (quoteattr(tag['k']), quoteattr(tag['v']))).encode('utf-8'))
        else:
            sys.stdout.write(("<%s %s>\n" % (name, " ".join("%s=%s" % (k, quoteattr(v)) for k, v in attrs.items()))).encode('utf-8'))

    def endElement(self, name):
        if name == 'node':
            if self.node['used']:
                sys.stdout.write(("<node %s>\n" % " ".join(["%s=%s" % (k, quoteattr(v)) for k, v in self.node['attrs'].items()])).encode('utf-8'))
                for tag in self.node['tags']:
                    sys.stdout.write(("<tag k=%s v=%s />\n" % (quoteattr(tag['k']), quoteattr(tag['v']))).encode('utf-8'))
                sys.stdout.write("</node>\n".encode('utf-8'))
                self.out_nodes += 1
                self.node = None
        else:
            if name != 'tag':
                sys.stdout.write(("</%s>\n" % name).encode('utf-8'))

def filter_orphans(filename):
    sys.stdout.write("<?xml version='1.0' encoding='UTF-8'?>\n".encode('utf-8'))

    sys.stderr.write("parsing ways...\n")

    handler = UsedNodesHandler()
    with file(filename) as f:
        xml.sax.parse(f, handler)

    sys.stderr.write("used_nodes: %s\n" % (len(handler.used_nodes)))

    sys.stderr.write("parsing nodes and ways...\n")

    handler = OsmHandler(handler.used_nodes)
    with file(filename) as f:
        xml.sax.parse(f, handler)

    sys.stderr.write("in_nodes: %s, out_nodes: %s\n" % (handler.in_nodes, handler.out_nodes))

if __name__ == '__main__':
    filter_orphans(sys.argv[1])
