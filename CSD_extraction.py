#!/ccnc_bin/venv/bin/python

import os
import re
import argparse
import textwrap
import pandas as pd

pd.set_option('display.max_rows', 50000)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
#pd.set_option('display.height', 1000)

def main(args):
    print args.source

    region_table = find_location('args.dipole')
    currentDf = pd.read_csv('args.current')
    strength_timeseries_list = coord_to_strength_time(currentDf,region_table)
    finalDf = pd.concat(strength_timeseries_list,axis=1)

    if not args.output:
        finalDf.to_csv(args.current.split('.')[0]+'_out.csv')
    else:
        if args.output.endswith('.csv'):
            finalDf.to_csv(args.output)
        else:
            finalDf.to_csv(args.output+'_out.csv')

    
def coord_to_strength_time(currentDf, coordsList):
    '''
    
    eg) df = 101027_Ctrl_LSJ2_current.csv'
        coord = {'x':0.42,'y':-0.54,'z':-0.73}
    '''
    strength_timeseries_list = []
    num = 1
    for region, coords in coordsList.iteritems():
        for coord in coords:
            currentDf_strength = currentDf[currentDf['Latency [ms]'].str.startswith('Strength')]
            currentDf_strength['strength'] = currentDf_strength['Latency [ms]'].str.extract('Strength (\d+)')
            currentDf_strength = currentDf_strength.set_index('strength').drop('Latency [ms]',axis=1)


            currentDf_location = currentDf[currentDf['Latency [ms]'].str.startswith('Location')]
            currentDf_location['strength'] = currentDf_location['Latency [ms]'].str.extract('Location (\d+)')
            currentDf_location['axis'] = currentDf_location['Latency [ms]'].str.extract('\d+ (\w)')
            currentDf_location = currentDf_location.set_index(['strength','axis']).drop('Latency [ms]',axis=1).stack().unstack(1)

            print coord['x']
            matching_strength = currentDf_location[currentDf_location.x==coord['x']][currentDf_location.y==coord['y']][currentDf_location.z==coord['z']]
            matching_strength_num = matching_strength.ix[0].name[0]
            strength_timeseries = currentDf_strength.ix[matching_strength_num]
            strength_timeseries['Strength'] = matching_strength_num
            strength_timeseries['Region'] = region
            strength_timeseries['x [mm]'] = coord['x']
            strength_timeseries['y [mm]'] = coord['y']
            strength_timeseries['z [mm]'] = coord['z']
            strength_timeseries.name = num
            strength_timeseries_list.append(strength_timeseries)
            num += 1
    return strength_timeseries_list


def find_location(dipoleCSV):
    dipoleDf = pd.read_csv(dipoleCSV)
    region_table = {}
    for region in dipoleDf[' atlas'].unique():
        
        coord_list = []
        for line in dipoleDf[dipoleDf[' atlas']==region][[u' x [mm]',u' y [mm]',u' z [mm]',' atlas']].drop_duplicates().iterrows():
            x = line[1][u' x [mm]']
            y = line[1][u' y [mm]']
            z = line[1][u' z [mm]']
            coord_list.append({'x':x,'y':y,'z':z})
            
        region_table[region] = coord_list
    
    return region_table

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

    parser.add_argument(
        '-o', '--output',
        help ="output file, default : current file + '_out.csv'"
        )

    args = parser.parse_args()

    if not args.source or not args.dipole or not args.current:
        parser.error('Input missing, try --help option')

    main(args)
