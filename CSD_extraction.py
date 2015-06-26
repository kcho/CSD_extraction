#!/ccnc_bin/venv/bin/python

import os
import re
import argparse
import textwrap
import pandas as pd

pd.set_option('display.max_rows', 50000)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
pd.set_option('display.height', 1000)

def main(args):
    print args.dipole
    print args.current
    print args.source



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
        '-s', '--source',
        help='source file'
        )
    parser.add_argument(
        '-d', '--dipole',
        help='dipole file',
        )
    parser.add_argument(
        '-c', '--current',
        help='current file')

    args = parser.parse_args()

    if not args.source or not args.dipole or not arg.current:
        parser.error('Input missing, try --help option')

    main(args)
