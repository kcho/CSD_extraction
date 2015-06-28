# CSD_extraction
----------------


1. Extract x, y, z coordinates from all ROIs in dipole csv, source csv file
2. Find the matching strength in currnet csv file
3. Extract the time series
4. Save into a csv file

### Three csv files are created
```
1. output.csv : strength time series for dipole locations
2. current_output.csv : strength time series for CSD location from source file
2. dipole_output.csv : strength time series for CSD location from source file
```



## Usage

    CSD_extraction -s source_file.csv -c current_file.csv -d dipole_file.csv -o out.csv


## Updates needed

- source file is not used yet
- printing stage progression is needed
- options for choosing dipole, source dipole or source current is needed.
