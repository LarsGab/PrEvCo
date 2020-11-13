#!/usr/bin/env python3
# ==============================================================
# Lars Gabriel
#
# Klass structure for a genome annotation file
# ==============================================================
import os


class transcript:
    #data structures and methods for a transcript

    def __init__(self, id):
        self.id = id
        self.transcript_lines = {}
        self.gtf = []
        self.prfl_match = []

    def add_line(self, line):
        if line[2] not in self.transcript_lines.keys():
            self.transcript_lines.update({line[2] : []})
        self.transcript_lines[line[2]].append(line)

    def get_gtf(self, gene_id):
        #returns the annotation of the transcript in gtf
        gtf = []
        for k in self.transcript_lines.keys():

        #self.transcript_line[8] = self.id
        #gtf = ['\t'.join(list(map(str, self.transcript_line)))]
            for g in self.transcript_lines[k]:
                g[8] = "transcript_id \"{}\"; gene_id \"{}\"".format(self.id, gene_id)
                gtf.append('\t'.join(list(map(str, g))))
        return('\n'.join(gtf))

class gene:
    #data structures and methods for a gene

    def __init__(self, id, chr):
        self.id = id
        self.chr = chr
        self.gtf_line = []
        self.transcript = {}
        self.score = 0

    def transcript_update(self, id):
        if not id in self.transcript.keys():
            self.transcript.update({ id : transcript(id)})

    def gtf(self):
        #returns the annotation of the transcript in gtf
        if self.gtf_line:
            self.gtf_line[8] = self.id
        gtf = ['\t'.join(list(map(str, self.gtf_line)))]
        for k in self.transcript.keys():
            gtf.append(self.transcript[k].get_gtf(self.id))
        return('\n'.join(gtf))

class genome:
    #data structures and methods for one genome annotation file
    def __init__(self, path, id):
        self.id = id
        self.genes = {}
        self.path = path

    def addGtf(self):
        with open (self.path, 'r') as file:
            file_lines = file.readlines()
        for line in file_lines:
            if not (line[0] == '#' or line == '\n'):
                line = line.strip('\n').split('\t')
                if line[2] == 'gene':
                    gene_id = "{}_{}".format(self.id, line[8])
                    self.genes_update(gene_id, line[0])
                    self.genes[gene_id].gtf_line = line
                    self.genes[gene_id].start = int(line[3])
                    self.genes[gene_id].end = int(line[4])
                elif line[2] == 'transcript':
                    gene_id = "{}_{}".format(self.id, line[8].split('.')[0])
                    self.genes_update(gene_id, line[0])
                    transcript_id = "{}_{}".format(self.id, line[8])
                    self.genes[gene_id].transcript_update(transcript_id)
                    self.genes[gene_id].transcript[transcript_id].add_line(line)
                else:
                    gene_id = "{}_{}".format(self.id, line[8].split('gene_id "')[1].split('";')[0])
                    self.genes_update(gene_id, line[0])
                    transcript_id = "{}_{}".format(self.id, line[8].split('transcript_id "')[1].split('";')[0])
                    self.genes[gene_id].transcript_update(transcript_id)
                    self.genes[gene_id].transcript[transcript_id].add_line(line)

    def genes_update(self, id, chr):
        if not id in self.genes.keys():
            self.genes.update({ id : gene(id, chr)})

    def print_gtf(self):
        c = 0
        for k in self.genes.keys():
            print(self.genes[k].gtf())
            c+=1
            if c == 2:
                break
