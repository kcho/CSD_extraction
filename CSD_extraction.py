#!/ccnc_bin/venv/bin/python

import os
import re
import argparse
import textwrap
import pandas as pd
import nibabel as nib

pd.set_option('display.max_rows', 50000)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
pd.options.mode.chained_assignment = None  # default='warn'
#pd.set_option('display.height', 1000)

def main(args):

    talairachImg = '/ccnc_bin/CSD_extraction/talairach.nii'
    f = nib.load(talairachImg)
    data = f.get_data()

    # If args.input present
    if args.input:
        current_file = args.input +'_current.csv'
        dipole_file = args.input +'_dipole.csv'
        source_file = args.input +'_source.rtf'
    else:
        current_file = args.current
        dipole_file = args.dipole
        source_file = args.source

    # Get information from the source file
    #CDR_results = get_info_from_source(source_file)

    # returns dict eg) {'x': 13,'y':-2,'z':60}
    #source_CDR_table = get_coord_from_source(CDR_results) 

    # Read files + get location + add source_CDR location
    #region_table = find_location(dipole_file,source_CDR_table)

    # Read current CSV
    currentDf = pd.read_csv(current_file)

    strength_timeseries_list = coord_to_strength_time(currentDf,region_table)
    finalDf = pd.concat(strength_timeseries_list,axis=1)

    if not args.output:
        finalDf.to_csv(current_file.split('.')[0]+'_out.csv')
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
        print

        # for clean print of regions
        if region.startswith(' '):
            print region[1:]
        else:
            print region

        for coord in coords:
            currentDf_strength = currentDf[currentDf['Latency [ms]'].str.startswith('Strength')]
            currentDf_strength['strength'] = currentDf_strength['Latency [ms]'].str.extract('Strength (\d+)')
            currentDf_strength = currentDf_strength.set_index('strength').drop('Latency [ms]',axis=1)


            currentDf_location = currentDf[currentDf['Latency [ms]'].str.startswith('Location')]
            currentDf_location['strength'] = currentDf_location['Latency [ms]'].str.extract('Location (\d+)')
            currentDf_location['axis'] = currentDf_location['Latency [ms]'].str.extract('\d+ (\w)')
            currentDf_location = currentDf_location.set_index(['strength','axis']).drop('Latency [ms]',axis=1).stack().unstack(1)


            #matching_strength = currentDf_location[currentDf_location.x==coord['x']][currentDf_location.y==coord['y']][currentDf_location.z==coord['z']]
            matching_strength_x = currentDf_location[currentDf_location.x==coord['x']]
            matching_strength_x_y = matching_strength_x[matching_strength_x.y==coord['y']]
            matching_strength = matching_strength_x_y[matching_strength_x_y.z==coord['z']]


            #print matching_strength
            try:
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
                print '\t', coord['x'], coord['y'], coord['z']
            except:
                print '\t', coord['x'], coord['y'], coord['z'], 'is missing in the current.csv***'

    return strength_timeseries_list


def find_location(dipoleCSV,source_CDR_table):
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
    
    region_table['source CDR'] = [source_CDR_table]
    return region_table


def get_info_from_source(sourceCSV):
    with open(sourceCSV) as f:
        source = f.read()

    return source

def get_coord_from_source(source):
    #print source,'source'
    coord = re.search('\): \((.*)\)mm',source).group(1).split(', ')

    coord_float = [float(x) for x in coord]
    coord_dict = {'x':coord_float[0], 
                  'y':coord_float[1],
                  'z':coord_float[2]}
    return coord_dict

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
        help='subject name'
        )
    parser.add_argument(
        '-l', '--lobe',
        help='select lobe; T, F, P + there will be more coming. Contact Kevin',
        default='T'
        )
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


    if args.input:
        if not args.dipole or not args.current:
            print '\tThis will automatically grep'
            print '\t\t{0}'.format(args.input+'_current.csv')
            print '\t\t{0}'.format(args.input+'_dipole.csv')
            print '\t\t{0}'.format(args.input+'_source.rtf')
            
    else:
        if not args.dipole or not args.current:
            parser.error('Input missing, try --help option')


    if not args.dipole or not args.current:
        if not args.input:
            parser.error('Input missing, try --help option')

    main(args)
