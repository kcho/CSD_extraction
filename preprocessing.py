import numpy as np
import pandas as pd
import nibabel as nb
import matplotlib.pyplot as plt
import re
import os
from os.path import join
from xml.dom import minidom
from nipy.core.api import Image, vox2mni, rollimg, xyz_affine, as_xyz_image

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
    
    # Normalsed df
    df_normal = df_info_gb.get_group('Normal')
    df_normal['number'] = df_normal['Latency [ms]'].str.split(' ').str[1].astype('int')
    df_normal['axis'] = df_normal['Latency [ms]'].str.split(' ').str[2]
    df_normal = df_normal.pivot_table(index=['info', 'number'], 
                                      columns='axis', 
                                      values=[x for x in df_normal.columns if re.search('\d',x)])
    return df_strength_location, df_normal

def get_current_vector(csv_location):
    a,b = current_file_preprocessing(csv_location)
    strength_df = a[['voxel_number']+[x for x in a.columns if re.search('\d', x)]]
    strength_array = strength_df.values
    subject_vector = strength_array.ravel()
    
    return subject_vector

def peak_preprocessing(textfile):
    df = pd.read_csv(text_data_loc, #skipfooter=1,
                 sep='\t', 
                 skiprows=5, 
                 names=['channel', 'x', 'y', 'z', 'minmax', 'latency'],
                 encoding='ISO-8859-1')

    #MGFP1 has only minmax and latency
    df.loc[df['channel']=='MGFP1', 'minmax'] = df.loc[df['channel']=='MGFP1', 'x']
    df.loc[df['channel']=='MGFP1', 'latency'] = df.loc[df['channel']=='MGFP1', 'y']

    df_melt = pd.melt(df, 
                      id_vars='channel', 
                      var_name='data', 
                      value_name='value', 
                      value_vars=['minmax', 'latency']).set_index(['channel', 'data']).T
    return df_melt.values



