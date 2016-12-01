# CSD_extraction
----------------

## CSD_three_inputs.py

    1. Extract x, y, z coordinates from all ROIs in dipole csv, source csv file created from Curry
    2. Find the matching strength in currnet csv file
    3. Extract the time series
    4. Save into a csv file

### Three csv files are created
```
output.csv            # strength time series for dipole locations
current_output.csv    # strength time series for CSD location from source file
dipole_output.csv     # strength time series for CSD location from source file
```

## CSD_current_reformat.py

    ** requires name inputs without the "_current.csv" **

    1. Rearranges the current source to have talairach location
    2. List of the areas that you want to extract could be specified
    3. Save the rearranged to a csv file

## CSD_extract_max.py
    
    1. Extracts maximum strength in each side / regions of the table from CSD_current_reformat.py




## Usage

    CSD_extraction -s source_file.csv -c current_file.csv -d dipole_file.csv -o out.csv

or

    CSD_extraction -i kcho


## Updates needed
- printing stage progression is needed
- options for choosing dipole, source dipole or source current is needed.
