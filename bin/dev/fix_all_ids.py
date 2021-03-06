import argparse
import subprocess as sp
import os
import shutil
combiner_bin = os.path.dirname(os.path.realpath(__file__))
def main():
    args = parseCmd()
    braker2_level = ['species_excluded', 'family_excluded', 'order_excluded']
    species_list = []
    with open('{}/species.tab'.format(args.data), 'r') as file:
        for s in file.read().split('\n'):
            if s:
                if not s[0] == '#':
                    species_list.append(s)
    for species in species_list:
        species_path = "{}/{}".format(args.data, species)
        braker = "{}/braker1/".format(species_path)
        fix(braker + 'braker.gtf', braker + 'braker_fixed.gtf')
        for level in braker2_level:
            braker2 = "{}/braker2/{}/".format(species_path, level)
            if os.path.exists(braker2):
                #shutil.copy(braker + 'braker_fixed.gtf', braker + "braker_{}.gtf".format(level))
                fix(braker2 + 'braker.gtf', braker2 + 'braker_fixed.gtf')

def fix(gtf, out):
    cmd = '{}/fix_gtf_id_error.py --gtf {} --out {}'.format(combiner_bin, gtf, out)
    print(cmd)
    sp.call(cmd, shell=True)
def parseCmd():
    """Parse command line arguments

    Returns:
        dictionary: Dictionary with arguments
    """
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--data', type=str,
        help='')
    return parser.parse_args()

if __name__ == '__main__':
    main()
