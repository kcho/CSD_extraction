#!/ccnc_bin/venv/bin/python

import os
import re
import numpy as np
import argparse
import textwrap
import pandas as pd
import nibabel as nib

# option for pandas
#pd.set_option('display.max_rows', 50000)
#pd.set_option('display.max_columns', 500)
#pd.set_option('display.width', 1000)
pd.options.mode.chained_assignment = None  # default='warn'


def main(args):

    # -----------------------------------------------------
    # Load current data
    # -----------------------------------------------------
    # current file to read
    #gyrus_wanted = ['Superior Temporal Gyrus', 'Middle Temporal Gyrus', 'Transverse Temporal Gyrus']
    # 2016_11_30
    gyrus_wanted = ['Cingulate Gyrus', 'Medial Frontal Gyrus', 'Superior Frontal Gyrus', 'Middle Frontal Gyrus', 'Inferior Frontal Gyrus', 'Transverse Temporal Gyrus', 'Angular Gyrus', 'Fusiform Gyrus']

    if args.input:
        current_csv = args.input
        print find_max(csv, gyrus_wanted)
    elif args.list:
        outData = {}
        for csvFileLoc in args.list:
            outData[csvFileLoc] =  find_max(csvFileLoc, gyrus_wanted)
        df = pd.DataFrame(outData).T
        df.to_csv('prac.csv')

def find_max(csv, gyrus_wanted):
    # read the current file
    df_raw = pd.read_csv(csv)

    gb = df_raw.groupby(['Side','Gyrus'])
    
    maxCSD  = {}
    for side_gyrus_name, table in gb:
        if side_gyrus_name[1] in gyrus_wanted:
            #maxCSD[side_gyrus_name] = side_gyrus_name[0], side_gyrus_name[1], table[table.columns[8:]].max().max(), table[table.columns[8:]].max().idxmax() 
            maxCSD[side_gyrus_name] = table[table.columns[8:]].max().max()

    print maxCSD
    return maxCSD


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''\
            {codeName} : Search files with user defined extensions 
            ========================================
            eg) {codeName} -e 'dcm|ima' -i /Users/kevin/NOR04_CKI
                Search dicom files in /Users/kevin/NOR04_CKI
            eg) {codeName} -c -e 'dcm|ima' -i /Users/kevin/NOR04_CKI
                Count dicom files in each directory under input 
            '''.format(codeName=os.path.basename(__file__))))

    parser.add_argument(
        '-i', '--input',
        help='Input csv file'
        )

    parser.add_argument(
        '-l', '--list',
        help='Input csv file list',
        nargs='+'
        )

    args = parser.parse_args()

    main(args)
