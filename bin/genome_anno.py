#!/usr/bin/env python3
# ==============================================================
# Lars Gabriel
#
# genome_anno.py: Handles the data structure for a genome annotation file
# ==============================================================

import os
import sys
import csv

class NotGtfFormat(Exception):
    pass

class Transcript:
    # data structures and methods for a transcript
    def __init__(self, id, gene_id, chr, source_anno, strand):
        self.id = id
        self.chr = chr
        self.gene_id = gene_id
        # self.transcript_lines[segment_type] = [lines of segment type]
        self.transcript_lines = {}
        self.gtf = []
        self.source_anno = source_anno
        self.start = -1
        self.end = -1
        self.cds_coords = []
        self.strand = strand

    def add_line(self, line):
        # add a single line from the gtf file to the transcript
        if not (line[0] == self.chr or line[6] == self.strand):
            raise NotGtfFormat('File is not in gtf format. ' \
                + 'Error in line {}\n'.format('\t'.join(map(str, line)))
                + 'Transcript ID is not unique')

        if line[2] not in self.transcript_lines.keys():
            self.transcript_lines.update({line[2] : []})

        line[3] = int(line[3])
        line[4] = int(line[4])
        if self.start < 0 or line[3] < self.start:
            self.start = line[3]
        if self.end < 0 or line[4] > self.end:
            self.end = line[4]

        self.transcript_lines[line[2]].append(line)

    def get_cds_coords(self):
        # returns list of [start_coord, end_coord] of all CDS
        if not self.cds_coords:
            if 'CDS' in self.transcript_lines.keys():
                key  = 'CDS'
            else:
                key = 'exon'
            for line in self.transcript_lines[key]:
                self.cds_coords.append([line[3], line[4]])
        return self.cds_coords

    def add_missing_lines(self):
        # add components to tx, that can miss in gtf files
        # add intron lines
        self.find_introns()
        # check if tx has cds or exon
        if not self.check_cds_exons():
            return False
        # add transcript line
        self.find_transcript()
        # add start/stop codon line
        self.find_start_stop_codon()
        return True

    def check_cds_exons(self):
        # check if tx has cds or exon
        if 'CDS' not in self.transcript_lines.keys() and 'exon' not in self.transcript_lines.keys():
            sys.stderr.write('Skipping transcript {}, no CDS nor exons in {}\n'.format(self.id, self.id))
            return False
        return True

    def find_introns(self):
        # add intron lines
        if not 'intron' in self.transcript_lines.keys():
            self.transcript_lines.update({'intron' : []})
            key = ''
            if 'CDS' in self.transcript_lines.keys():
                key = 'CDS'
            elif 'exon' in self.transcript_lines.keys():
                key = 'exon'
            if key:
                exon_lst = []
                for line in self.transcript_lines[key]:
                    exon_lst.append(line)
                exon_lst = sorted(exon_lst, key=lambda e:e[0])
                for i in range(1, len(exon_lst)):
                    intron = []
                    intron += exon_lst[i][0:2]
                    intron.append('intron')
                    intron.append(exon_lst[i-1][4] + 1)
                    intron.append(exon_lst[i][3] - 1)
                    intron += exon_lst[i][5:8]
                    intron.append("gene_id \"{}\"; transcript_id \"{}\";".format(\
                    self.gene_id, self.id))
                    self.transcript_lines['intron'].append(intron)

    def find_transcript(self):
        # add transcript line
        if not 'transcript' in self.transcript_lines.keys():
            for k in self.transcript_lines.keys():
                for line in self.transcript_lines[k]:
                    if line[3] < self.start or self.start < 0:
                        self.start = line[3]
                    if line[4] > self.end:
                        self.end = line[4]
            tx_line = [self.chr, line[1], 'transcript', self.start, self.end, \
            '.', line[6], '.', self.id]
            self.add_line(tx_line)

    def find_start_stop_codon(self):
        # add start/stop codon line
        if not 'transcript' in self.transcript_lines.keys():
            self.find_transcript()
        tx = self.transcript_lines['transcript'][0]

        line1 = [self.chr, tx[1], '', tx[3], tx[3] + 2, \
        '.', tx[6], '.', "gene_id \"{}\"; transcript_id \"{}\";".format(\
        self.gene_id, self.id)]
        line2 = [self.chr, tx[1], '', tx[4] - 2, tx[4], \
        '.', tx[6], '.', "gene_id \"{}\"; transcript_id \"{}\";".format(\
        self.gene_id, self.id)]
        if tx[6] == '+':
            line1[2] = 'start_codon'
            line2[2] = 'stop_codon'
            start = line1
            stop = line2
        else:
            line1[2] = 'stop_codon'
            line2[2] = 'start_codon'
            stop = line1
            start = line2
        if not 'start_codon' in self.transcript_lines.keys():
            self.add_line(start)
        if not 'stop_codon' in self.transcript_lines.keys():
            self.add_line(stop)

    def get_gtf(self, prefix='', new_gene_id=None):
        # returns transcript lines in gtf
        gtf = []
        if new_gene_id:
            g_id = new_gene_id
        else:
            g_id = self.gene_id

        if prefix:
            prefix += '.'
        for k in self.transcript_lines.keys():
            for g in self.transcript_lines[k]:
                if k == 'transcript':
                    g[8] = prefix + self.id
                else:
                    g[8] = 'transcript_id \"{}\"; gene_id \"{}";'.format(\
                        prefix + self.id, g_id)
                gtf.append(g)
        gtf = sorted(gtf, key=lambda g:g[3])
        return gtf

class Anno:
    # data structures and methods for one genome annotation file
    def __init__(self, path, id):
        self.id = id
        self.genes = {'None' : []}
        self.gene_gtf = {}
        self.transcripts = {}
        self.path = path

    def addGtf(self):
        with open (self.path, 'r') as file:
            file_lines = csv.reader(file, delimiter='\t')
            for line in file_lines:
                if line[0][0] ==  '#':
                    continue
                line[3] = int(line[3])
                line[4] = int(line[4])
                if line[2] == 'gene':
                    gene_id = line[8]
                    self.genes_update(gene_id)
                    if not gene_id in self.gene_gtf.keys():
                        self.gene_gtf.update({gene_id : line})
                    else:
                        sys.stderr.write('ERROR, gene_id not unique: {}'.format(gene_id))
                elif line[2] == 'transcript':
                    transcript_id = line[8]
                    gene_id = transcript_id.split('.')[0]
                    self.transcript_update(transcript_id, gene_id, line[0], line[6])
                    self.transcripts[transcript_id].add_line(line)
                else:
                    transcript_id = line[8].split('transcript_id "')
                    if len(transcript_id) > 1:
                        transcript_id = transcript_id[1].split('";')[0]
                    else:
                        raise NotGtfFormat('File: "{}" is not in gtf format. \n'.format(\
                            self.path) + 'Error in line {}\n'.format('\t'.join(map(str, line))))

                    gene_id = line[8].split('gene_id "')
                    if len(gene_id) > 1:
                        gene_id = gene_id[1].split('";')[0]
                    else:
                        gene_id = 'None'
                        for key, value in self.genes.items():
                            if value == transcript_id:
                                gene_id = key

                    self.transcript_update(transcript_id, gene_id, line[0], line[6])
                    self.genes_update(gene_id, transcript_id)
                    self.transcripts[transcript_id].add_line(line)

        for tx_id in self.genes['None']:
            gene_id = tx_id + '_g'
            self.genes_update(gene_id, tx_id)

    def norm_tx_format(self):
        tx_no_cds = []
        # add missing lines to all tx
        for k in self.transcripts.keys():
            if not self.transcripts[k].add_missing_lines():
                tx_no_cds.append(k)
        for k in tx_no_cds:
            del self.transcripts[k]

    def genes_update(self, gene_id, transcript_id=''):
        # update gene ids
        if not gene_id in self.genes.keys():
            self.genes.update({ gene_id : []})
        if transcript_id and transcript_id not in self.genes[gene_id]:
            self.genes[gene_id].append(transcript_id)
        if transcript_id in self.genes['None'] and not gene_id == 'None':
            self.genes['None'].remove(transcript_id)
            self.transcripts[transcript_id].gene_id = gene_id

    def transcript_update(self, t_id, g_id, chr, strand):
        # update tx ids
        if not t_id in self.transcripts.keys():
            self.transcripts.update({ t_id : Transcript(t_id, g_id, chr, self.id, strand)})

    def get_gtf(self):
        # get annotaion file as gtf string
        gtf = []
        for k in self.genes.keys():
            if k in self.gene_gtf.keys():
                gtf.append(self.gene_gtf[k])
                #gtf += '\t'.join(map(str, self.gene_gtf[k])) + '\n'
            for t_id in self.genes[k]:
                gtf += self.transcripts[t_id].get_gtf()
        return gtf

    def get_subset_gtf(self, tx_list):
        # return string in gtf for tx in tx_list
        gtf = []
        for tx in tx_list:
            gtf += self.transcripts[tx[0]].get_gtf(self.id, tx[1])
        return gtf

    def change_id(self, new_id):
        # change annotation file id
        self.id = new_id
        for k in self.transcripts.keys():
            self.transcripts.source_anno = self.id

    def get_transcript_list(self):
        # get list of all txs
        return list(self.transcripts.values())
