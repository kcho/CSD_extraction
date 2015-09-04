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
    gyrus_wanted = ['Superior Temporal Gyrus', 'Middle Temporal Gyrus', 'Transverse Temporal Gyrus']

    current_csv = args.input

    # read the current file
    df_raw = pd.read_csv(current_csv)

    gb = df_raw.groupby(['Side','Gyrus'])

    for side_gyrus_name, table in gb:
        if side_gyrus_name[1] in gyrus_wanted:
            print side_gyrus_name, table[table.columns[8:]].max().max()


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
    args = parser.parse_args()

    main(args)
