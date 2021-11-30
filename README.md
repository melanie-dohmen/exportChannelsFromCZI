# Required Packages (tested version)
- czifile (2019.7.2) 
- pandas (1.3.4) 
- numpy (1.21.4) 
- pillow (8.4.0) 
- tifffile (2021.11.2) 


# Export Channel Images in .tif or .png from CZI Format
Export channels from carl Zeiss image (.czi) formatted files. Needs a comma separated value (see test.csv) file to define the name for each channel.
Also exports a list of generated fileprefixes (without channel subfix and file ending) as all.csv

# How to run
This is the default configuration 
```
CHANNEL_NAME = "ALL"
OUTPUT_TYPE = "TIF"

SLICE = 0

DATA_PATH = ""
CSV_FILE = "test.csv"
OUTPUT_PATH = "channels"

VERBOSE = False
```
Redefine at least CSV_FILE with a path to an appropriate .csv file.
With the example test.csv file below run:
```
 python exportChannelsFromCZI.py
```
This will generate the following files:
```
channels/Image_DAPI.tif
channels/Image_Actin.tif
channels/Image2_DAPI.tif
channels/all.csv:
```
The all.csv list contains:
```
Image
Image2
```

# Define Channel numbers and names (test.csv)
The file to define channel numbers and channel names must have the following (.csv) format:
```
folder,image,channel_nr,channel_name
folder1,Image.czi,0,DAPI
folder1,Image.czi,1,Actin
folder1,Image2.czu,0,DAPI
```


