import numpy as np
import pandas as pd
import nibabel as nb
import matplotlib.pyplot as plt
import re
import os
from os.path import join, dirname, basename, isfile
from xml.dom import minidom
from nipy.core.api import Image, vox2mni, rollimg, xyz_affine, as_xyz_image
import argparse
import textwrap
import matplotlib

pd.options.mode.chained_assignment = None  # default='warn'

def get_layer_name_dict(fsl_xml):
    xmldoc = minidom.parse(fsl_xml)
    itemlist = xmldoc.getElementsByTagName('label')

    layer_name_dict = {}
    for s in itemlist:
        layer_name_dict[int(s.attributes['index'].value) + 1] = s.childNodes[0].data

    return layer_name_dict

def get_value(img, x, y, z):    
    '''
    img : nibabel image class
    x,y,z in MNI mm coordinate
    layer_name_dict from fsl_xml
    '''
    # mm coordinate to voxel location
    voxel_loc = nb.affines.apply_affine(np.linalg.inv(img.affine), 
                                        [x,y,z]).round().astype('int')
    img_data = img.get_data()
    # layer number
    try:
        layer_number = img_data[voxel_loc[0], voxel_loc[1], voxel_loc[2]]
    except IndexError:
        layer_number = -1

    return layer_number

def current_file_preprocessing(csv):
    '''
    Returns 
    - strength df with matching brain region, 
    - 'normal' value df
    from the csv file containing the current information.
    
    The csv file has 5 lines of header : (not returned)
    - Latency
    - Residual Deviation (normalized)
    - Residual Deviation (original)
    - Explained Variance (normalized)
    - Explained Variance (original)
    
    Main dataframe is composed of three parts :
    1. Strength
        - for each activations along the latency
    2. Location
        - for each activations
    3. Normal (Normalized)
        - for each activations along the latency
        
    During the preprocessing, 
    - The location information is merged to the strength df, 
      based on the activation number.
    - The coordinate information is used 
      to find matching regions in the MNI space, 
      adding extra column of brain location the strength df.    
    '''
    
    # ISO-8859-1 encoding solves the encoding problem
    df_raw = pd.read_csv(csv, encoding='ISO-8859-1')
    df_header = df_raw.ix[:4]
    df_data = df_raw.ix[4:]
    
    # Create 'info' column from the information in the first column
    df_data['info'] = df_data['Latency [ms]'].str.split(' ').str[0]
    df_info_gb = df_data.groupby('info')
    
    # Strength df
    df_strength = df_info_gb.get_group('Strength')
    df_strength['number'] = df_strength['Latency [ms]'].str.split(' ').str[1].astype('int')
    df_strength = df_strength.drop('Latency [ms]', axis=1)
    
    # Normalsed df
    df_normal = df_info_gb.get_group('Normal')
    df_normal['number'] = df_normal['Latency [ms]'].str.split(' ').str[1].astype('int')
    df_normal = df_normal.drop('Latency [ms]', axis=1)
    #df_normal['axis'] = df_normal['Latency [ms]'].str.split(' ').str[2]
    #df_normal = df_normal.pivot_table(index=['info', 'number'], 
                                      #columns='axis', 
                                      #values=[x for x in df_normal.columns if re.search('\d',x)])

    # Location df
    df_location = df_info_gb.get_group('Location')
    df_location['number'] = df_location['Latency [ms]'].str.split(' ').str[1].astype('int')
    df_location['axis'] = df_location['Latency [ms]'].str.split(' ').str[2]
    # the csv has duplication of the coordinates for every latencies
    # select one
    first_num_col = df_location.columns[1]
    df_location = df_location[['info', 'number', 'axis', first_num_col]]
    df_location.columns = ['info', 'number', 'axis', 'coord']
    # x,y,z into columns
    df_location = df_location.pivot_table(index=['info','number'], 
                                          columns='axis', 
                                          values='coord')
    # get location using x,y,z mni coordinates
    df_location['voxel_number'] = df_location.apply(
        lambda row: get_value(HO_cortex, row['x'], row['y'], row['z']), axis=1) 
    
    

    # merge strength with location
    df_strength_location = pd.merge(df_location.reset_index()[['number','x','y','z','voxel_number']],
                                    df_strength,
                                    on='number', how='inner')

    df_norm_strength_location = pd.merge(df_location.reset_index()[['number','x','y','z','voxel_number']],
                                         df_normal,
                                         on='number', how='inner')

    return df_strength_location, df_norm_strength_location

def get_current_vector(csv_location):
    a,b = current_file_preprocessing(csv_location)

    strength_df = a[['voxel_number']+[x for x in a.columns if re.search('\d', x)]]
    strength_array = strength_df.values
    subject_vector = strength_array.ravel()
    
    strength_df_norm = b[['voxel_number']+[x for x in b.columns if re.search('\d', x)]]
    strength_array_norm = strength_df_norm.values
    subject_vector_norm = strength_array_norm.ravel()

    return subject_vector, subject_vector_norm

def peak_preprocessing(textfile):
    with open(textfile, 'r') as f:
        lines = f.readlines()
        for num, line in enumerate(lines):
            if 'channel label' in line:
                break

    num = num + 1 
    print(num)
    #if 'Ctrl' in textfile: 
    #    df = pd.read_csv(textfile, #skipfooter=1,
    #                     sep='\t', 
    #                     skiprows=5, 
    #                     names=['channel', 'x', 'y', 'z', 'minmax', 'latency'],
    #                     encoding='ISO-8859-1')
    #else:

    df = pd.read_csv(textfile, #skipfooter=1,
                     sep='\t', 
                     skiprows=num, 
                     names=['channel', 'x', 'y', 'z', 'minmax', 'latency'],
                     encoding='ISO-8859-1')

    print(df)
    #MGFP1 has only minmax and latency
    df.loc[df['channel']=='MGFP1', 'minmax'] = df.loc[df['channel']=='MGFP1', 'x']
    df.loc[df['channel']=='MGFP1', 'latency'] = df.loc[df['channel']=='MGFP1', 'y']
    df.loc[df['channel']=='MGFP1', 'x'] = None
    df.loc[df['channel']=='MGFP1', 'y'] = None

    df_melt = pd.melt(df, 
                      id_vars='channel', 
                      var_name='data', 
                      value_name='value', 
                      value_vars=['minmax', 'latency']).set_index(['channel', 'data']).T

    return df_melt, df_melt.values

def get_type_group_dict(dataLoc):
    dirs = os.listdir(dataLoc)
    groups = ['Ctrl', 'CHR_FU', 'FEP']
    modalities = ['MMN', 'P300']

    type_group_dict = {}
    for group in groups:
        for modality in modalities:
            type_group_dict['_'.join([modality, group])] = join(dataLoc,
                                                                [x for x in dirs if group in x and modality in x][0])

    return type_group_dict

if __name__ == '__main__':
    HO_cortex_file_loc = '/usr/local/fsl/data/atlases/HarvardOxford/HarvardOxford-cort-maxprob-thr0-1mm.nii.gz'
    # HO_cortex_file_loc = '/Users/kangik/Dropbox/project/2017_08_23_ERP_machine_learning/brain_template/HCP-MMP1_on_MNI152_ICBM2009a_nlin_hd.nii.gz'
    HO_cortex = nb.load(HO_cortex_file_loc)
    HO_cortex_data = HO_cortex.get_data()

    layer_xml = '/usr/local/fsl/data/atlases/HarvardOxford-Cortical.xml'
    layer_dict = get_layer_name_dict(layer_xml)
    layer_dict[0] = 'outside'

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''\
            {codeName} : Preprocess CSD csv files
            ========================================
            '''.format(codeName=os.path.basename(__file__))))

    parser.add_argument(
        '-c', '--inputCSV',
        help='csv_location')
    parser.add_argument(
        '-p', '--peaktxt',
        help='Peak text')
    parser.add_argument(
        '-d', '--inputdir',
        help='Directory location where all subdirectories are saved')
    #parser.add_argument(
        #'-c', '--count',
        #help='count files with the ext in each directory',
        #action='store_true')
    #parser.add_argument(
        #'-e', '--extension',
        #help='Extension to search')
    args = parser.parse_args()

    # Data location
    dataLoc = args.inputdir
    #type_group_dict = get_type_group_dict(dataLoc)*/
    #print(type_group_dict)*/

    #for type_group, dataLoc in type_group_dict.items():
        #print(type_group)

    # list of csv files in the dataLoc
    current_files = [join(dataLoc, x) for x in os.listdir(dataLoc) if x.endswith('csv')]
    peak_files = [join(dataLoc, x) for x in os.listdir(dataLoc) if x.endswith('peak.txt')]
        
    # estimate array size
    prac_vector = get_current_vector(current_files[0])[1]
    size = prac_vector.shape[0]

    # make empty array
    array = np.zeros((len(current_files), size))

    # if the type_group has merged data available
    if not isfile(join(dataLoc, 'all_data.txt')):
        # for every current_file in the type_group location
        for num, current_file in enumerate(current_files):
            print(current_file)
            current_file_root = dirname(current_file)
            file_name = basename(current_file)
            array_file = join(current_file_root, file_name+'_clean')

            if not isfile(array_file):
                print('subject vector will be estimated')
                subject_vector = get_current_vector(current_file)[1]
                np.save(array_file, subject_vector)
            else:
                print('subject vector will be loaded')
                subject_vector = np.loadtxt(array_file)

            # concatenate the subject vector into the array
            try:
                array[num, :] = subject_vector
            except:
                print(current_file + ' has different size')

        #merge all data from the subjects in the dataLoc
        np.savetxt(join(dataLoc, 'all_data.txt'), array)
    else:
        print('Current estimation completed', join(dataLoc, 'all_data.txt'))


    # estimate array size
    prac_vector = peak_preprocessing(peak_files[0])[1]
    size = prac_vector.shape[1]

    # make empty array
    array = np.zeros((len(current_files), size))

    # if the type_group has merged data available
    if not isfile(join(dataLoc, 'all_peaks.txt')):
        # for every current_file in the type_group location
        for num, peak_file in enumerate(peak_files):
            print(peak_file)
            peak_file_root = dirname(peak_file)
            file_name = basename(peak_file)
            array_file = join(peak_file_root, file_name+'_clean')

            if not isfile(array_file):
                print('subject vector will be estimated')
                subject_vector = peak_preprocessing(peak_file)[1]
                np.save(array_file, subject_vector)
            else:
                print('subject vector will be loaded')
                subject_vector = np.loadtxt(array_file)

            # concatenate the subject vector into the array
            try:
                array[num, :] = subject_vector
            except:
                print(peak_file, '***********')
                print(subject_vector.shape)
                print(peak_file + ' has different size')

        #merge all data from the subjects in the dataLoc
        np.savetxt(join(dataLoc, 'all_peaks.txt'), array)
    else:
        print('Peak estimation completed', join(dataLoc, 'all_peaks.txt'))
