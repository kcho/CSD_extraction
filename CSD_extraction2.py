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
    current_csv = args.input + '_current.csv'

    # read the current file
    df_raw = pd.read_csv(current_csv)

    # -----------------------------------------------------
    # Make Talairach map between
    #   coordinate : name of the structure
    # -----------------------------------------------------
    talairachNii = '/ccnc_bin/CSD_extraction/talairach.nii'
    talairachMap = '/usr/local/fsl/data/atlases/Talairach.xml'
    global data, newDict
    data, newDict = makeTalairachDB(talairachNii, talairachMap)

    # -----------------------------------------------------
    # Add location information to the coordinates
    # -----------------------------------------------------
    # add location information to each strength 
    df_with_lobe = get_df_with_lobe(df_raw)

    # -----------------------------------------------------
    # Get CSD time series for each strengths
    # -----------------------------------------------------
    # Extract time series data for the df_in_side_lobe
    df = get_time_series(df_raw,df_with_lobe)

    # -----------------------------------------------------
    # Arrange df
    # -----------------------------------------------------
    df['strength'] = df['strength'].astype(int)
    df['Side'] = df.lobe.str[0]
    df['Lobe'] = df.lobe.str[1]
    df['Gyrus'] = df.lobe.str[2]
    df['Matter'] = df.lobe.str[3]
    df['Broadmann'] = df.lobe.str[4]
    # Only select Gray Matter
    allData = df[df.Matter=='Gray Matter']
    #print allData.describe()


    # -----------------------------------------------------
    # Save data
    # -----------------------------------------------------
    # Make new columns
    timeCol = [x for x in df.columns if re.search('\d',x)]
    newCol = ['strength','coord','Side','Lobe','Gyrus','Matter','Broadmann'] + timeCol

    # Lobe data subset save
    sortList = ['Side', 'Lobe', 'Gyrus', 'strength']
    for lobe_wanted in ['Temporal Lobe', 'Frontal Lobe', 'Parietal Lobe']:
        toSave = allData[allData.Lobe==lobe_wanted][newCol].sort(sortList)
        nameToSave = re.sub('_out.csv',
                            '_{0}_out.csv'.format(lobe_wanted.split(' ')[0].lower()),
                            args.output)
        toSave.to_csv(nameToSave)

    # GyrusROI data subset save
    gyrusList = ['Superior Frontal Gyrus', 'Middle Frontal Gyrus', 
                 'Inferior Frontal Gyrus', 'Superior Temporal Gyrus',
                 'Transverse Temporal Gyrus', 'Middle Temporal Gyrus',
                 'Inferior Temporal Gyrus', 'Angular Gyrus',
                 'Supramarginal Gyrus', 'Superior Parietal Lobule']
    gb = allData.groupby('Gyrus')
    gyrusData = pd.concat([gb.get_group(x) for x in gyrusList])

    for side in ['Right','Left']:
        toSave = gyrusData[gyrusData.Side==side][newCol].sort(sortList)
        nameToSave = re.sub('_out.csv',
                            '_gyrus_{0}_out.csv'.format(side.lower()),
                            args.output)
        toSave.to_csv(nameToSave)

    print 'Completed'


def makeTalairachDB(talairachNii, talairachMap):
    # Read talairach nifti data
    f = nib.load(talairachNii)

    # Make the loaded image as array
    data = f.get_data()

    # Load talairach naming map
    with open(talairachMap,'r') as f:
            a=f.readlines()

    labelLines=[x for x in a if x.startswith('<label')]
    reList = [re.search('<label index="(\d+)".+>(.+)</label>\n',x) for x in labelLines]
    numNameDict = dict([(x.group(1),x.group(2)) for x in reList])

    # Make directory={roiNum:roiName}
    newDict={}
    for num,name in numNameDict.iteritems():
        a = name.split('.')

        side = a[0].split(' ')[0]
        lobe = a[1]
        loc = a[2]
        matter = a[3]
        name = a[4]

        newDict[num] = (side, lobe, loc, matter, name)

    return data, newDict

def get_df_with_lobe(df_raw):

    # df_raw = pd.read_csv(current_csv)

    # cut part with location information
    location_df = df_raw[df_raw['Latency [ms]'].str.startswith('Location')]

    # make shorter form
    location_df = location_df.ix[:,:2]

    # extract out strength as a column
    location_df['strength'] = location_df['Latency [ms]'].str.extract('Location (\d+)')

    # extract out axis as a column
    location_df['axis'] = location_df['Latency [ms]'].str.extract('\d+ (\w)')

    # make x, y, z axis into columns
    location_df = location_df.set_index(['strength','axis']).drop('Latency [ms]', axis=1).stack().unstack(1).reset_index()

    # make coord column from x, y, z columns
    location_df['coord']=location_df['x'].astype(str) + ',' + location_df['y'].astype(str) + ',' + location_df['z'].astype(str)

    # make coord column into list
    location_df['list'] = location_df.coord.str.split(',')

    # run coord_to_lobe on the coord column
    location_df['lobe'] = location_df['list'].map(coord_to_lobe)

    location_df.drop(['level_1', 'list'],axis=1)
    return location_df


def coord_to_lobe(df):
    '''
    talCoord=[x,y,z]
    '''
    i,j,k = [float(x) for x in df]

    try:
        M = np.array([[ 1.,  0.,  0.],
            [ 0.,  1.,  0.],
            [ 0.,  0.,  1.]])

        abc = np.array([ -70., -102.,  -42.])

        x,y,z = M.dot([i,j,k]-abc)
        #print i,j,k,'-->', round(x),round(y),round(z)
        return newDict[str(data[round(x),round(y),round(z)])] #return lobe 
    except:
        return 'error'

        #('Right', 'Limbic Lobe', 'Cingulate Gyrus', 'White Matter', '*')

def get_time_series(df_raw,df_in_side_lobe):

    # make strength list
    strength_list = df_in_side_lobe.strength.tolist()

    strengthTimeSeries = df_raw[df_raw['Latency [ms]'].str.startswith('Strength')]
    strengthTimeSeries['strength'] = strengthTimeSeries['Latency [ms]'].str.extract('Strength (\d+)')

    df = pd.merge(df_in_side_lobe[['strength','coord','lobe']],
                    strengthTimeSeries,
                    on='strength',
                    how='left'
                       )
    df = df.reset_index().drop('index',axis=1)
    return df


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
        default='Temporal Lobe'
        )

    parser.add_argument(
        '-s', '--side',
        help='select side; [Right/Left]'
        )
    #parser.add_argument(
        #'-s', '--source',
        #help='source file'
        #)
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
            
    else:
        if not args.dipole or not args.current:
            parser.error('Input missing, try --help option')


    if not args.dipole or not args.current:
        if not args.input:
            parser.error('Input missing, try --help option')

    if not args.output:
        args.output = args.input+'_out.csv'

    main(args)
