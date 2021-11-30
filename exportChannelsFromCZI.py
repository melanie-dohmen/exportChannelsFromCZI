#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jul 9 2019 Created
Nov 30 2021 Publication

@author: Melanie Dohmen

This script exports separate channel images as .tif or .png files from
a .czi (Carl Zeiss image format) files. The name and corresponding nr
of each channel must be given in a .csv file, including a header,
with the following format:

folder,image,channel_nr,channel_name
folder1,Image.czi,0,DAPI
folder1,Image.czi,1,Actin
folder1,Image2.czi,0,DAPI
...

Zeiss Microscopes can store multiple channels as separate blocks in a 
.czi file or as an additional dimension C in the raw image array.
This script is able to detect and read both correctly. 
The csv file allows to conveniently name the exported channels correctly.


Only one or all channels in the .csv can be exported.
The path of the data DATA_PATH, the output path to where the 
exported images are written, the complete path of the csv file CSV_FILE,
must be given in the CONFIGURATION part. In case of 3D images, a slice
number can be given, starting at 1. SLICE = 0 will export all slices as
a sequence of .png files or a 3D TIF image. 


"""

from czifile import CziFile # read .czi image
import os # create output directory
import numpy as np # reshape raw image
import pandas as pd # read csv
from PIL import Image # png export
from tifffile import imwrite # tif export


##################
# Configuration: #
##################

# export only one channel with selected name
# or all channels
CHANNEL_NAME = "ALL"

# select output format
OUTPUT_TYPE = "TIF"
#OUTPUT_TYPE = "PNG"


# for 3D .czi files, select 2D slice to export
# (starting with 1)
# or select all slices in case single_slice = 0
# this is ignored for 2D .czi files
SLICE = 1


DATA_PATH = ""
CSV_FILE = "test.csv"
OUTPUT_PATH = "channels"


# print out image dimensions for each image
VERBOSE = False


if __name__ == "__main__":


    # check output file type
    if OUTPUT_TYPE not in ["TIF", "PNG"]:
        print("unexpected output file type ", OUTPUT_TYPE)
        
    # read .csv file with pandas
    csv_file = pd.read_csv(CSV_FILE)

    # create output directory:
    abort = False
    if os.path.exists(OUTPUT_PATH):
        print("Output directory", OUTPUT_PATH, "already exists! Overwrite?")
        overwrite = input("Type 'y' or 'n': ")
        if overwrite == "y":
            os.makedirs(OUTPUT_PATH, exist_ok=True)
        else:
            abort = True
            print("Aborted.")
    else:
        os.mkdir(OUTPUT_PATH)

    if not abort:

        # first get list of all prefix entries in .csv
        image_names_list = []
        images_not_found = 0
        for row in csv_file.iterrows():
            # get image filenames, remove ending .czi
            filename = row[1]['image'][:-4]
            if filename not in image_names_list:
                if CHANNEL_NAME == "ALL" or row[1]['channel_name'] == CHANNEL_NAME:
                    if os.path.exists(os.path.join(DATA_PATH,row[1]['folder'],row[1]['image'])):
                        image_names_list.append(filename)
                    else:
                        print("===== WARNING ====")
                        print("File ", os.path.join(DATA_PATH,row[1]['folder'], row[1]['image']), " does not exist")
                        images_not_found += 1
                        
        print_str = "\n"+str(len(image_names_list))+"/"
        print_str = print_str+str(len(image_names_list)+images_not_found)
        print_str = print_str+" images found in "+CSV_FILE+"\n"
        if CHANNEL_NAME == "ALL":
            print(print_str)
        else:
            print(print_str, " with channel name ", CHANNEL_NAME)
            
        # count exported images per channel
        count_channels = {}
        written_image_names_list = []
        
        # read all images and export selected channels   
        for row in csv_file.iterrows():  
            if row[1]['image'][:-4] in image_names_list and (row[1]['channel_name'] == CHANNEL_NAME or CHANNEL_NAME=="ALL"):
                
                filename = os.path.join(row[1]['folder'], row[1]['image'])
        
                with CziFile(DATA_PATH+filename) as czi:
                    if VERBOSE:
                        print("Reading... ", filename)
                    metadata_dict = czi.metadata(raw=False) 
                    image = czi.asarray()
                                
                    filename_prefix = row[1]['image'][:-4]
                    # Remove file extension '.czi':
                    #filename_prefix = filename_prefix[:-4]
    
                    # Read meta data about dimension sizes:
                    try:
                        sizeC = int(metadata_dict["ImageDocument"]["Metadata"]["Information"]["Image"]["SizeC"])
                    except:
                        sizeC = 1
                    sizeX = int(metadata_dict["ImageDocument"]["Metadata"]["Information"]["Image"]["SizeX"])
                    sizeY = int(metadata_dict["ImageDocument"]["Metadata"]["Information"]["Image"]["SizeY"])
                    try:
                        sizeZ = int(metadata_dict["ImageDocument"]["Metadata"]["Information"]["Image"]["SizeZ"])
                    except:
                        # image seems to be 2D
                        sizeZ = 1
                    if VERBOSE:
                        print("metadata size: ",sizeC, ",",sizeZ,",", sizeY, ",",sizeX," vs. raw image size: ", image.shape) 
                                
                    # There are two possibilities to store multiple channels in a
                    # .czi file. Either in separate blocks or as additional
                    # dimension in the image array
                    channels_stored_in_blocks = False
        
        
                    # reformat image array dimensions to CZYX
                    channel_available = True
                    image = image.squeeze()
                    if sizeC != image.shape[0] and sizeC == len(czi.filtered_subblock_directory):
                        if VERBOSE:
                            print("Assuming channels stored in blocks")
                        channels_stored_in_blocks = True
                        image = np.expand_dims(image,0)
                    elif sizeC != image.shape[0]:
                        print("===== WARNING ====")
                        print("Found ", sizeC,  " channels in meta data of ", filename, ",")
                        print("but image shape is ", image.shape)
                        channel_available = False
                        sizeC  == 0
                    if sizeZ == 1:
                        image = np.expand_dims(image,1)
        
                    if VERBOSE:
                        print("Extracted dimensions (CZYX): ", image.shape)
                    
                    # Check if channel nr is not higher than number of available channels
                    if row[1]['channel_nr'] < sizeC:
                        if channels_stored_in_blocks:
                            
                            # Read image data from block in main memory
                            image_block = czi.filtered_subblock_directory[row[1]['channel_nr']].data_segment().data()
                            reduced_image = image_block.squeeze()
                            # add Z dimension in dimension 0 (channel already selected)
                            if sizeZ == 1:
                                reduced_image = np.expand_dims(reduced_image,0)
                        else:
                            reduced_image = image[row[1]['channel_nr'],:,:,:]
                    else:
                        print("===== WARNING ====")
                        print("Found ", sizeC,  " channels in ", filename, ",")
                        print("but desired channel ", row[1]['channel_name']," has nr ", row[1]['channel_nr'])
                        channel_available = False
                    
                    
                    # export channel image(s):
                    if channel_available:
                        if OUTPUT_TYPE == "TIF":
                            if sizeZ == 1: # image is 2D, ignore SLICE
                                imwrite(os.path.join(OUTPUT_PATH,filename_prefix+"_"+row[1]['channel_name']+".tif"),reduced_image[0,:,:])
                            elif SLICE == 0: # save complete Z-Stack:
                                imwrite(os.path.join(OUTPUT_PATH,filename_prefix+"_"+row[1]['channel_name']+".tif"),reduced_image)
                            else: # single slice index starts with 1, numpy array with index 0 
                                imwrite(os.path.join(OUTPUT_PATH,filename_prefix+"_"+row[1]['channel_name']+"_Z"+str(SLICE)+".tif"),reduced_image[SLICE-1,:,:])
                        else: # OUTPUT_TYPE == "PNG"
                            if sizeZ == 1: # image is 2D, ignore SLICE
                                pil_image_slice = Image.fromarray(reduced_image[0,:,:])
                                pil_image_slice.save(os.path.join(OUTPUT_PATH,filename_prefix+"_"+row[1]['channel_name']+".png"))
                            elif SLICE == 0: # save all slices in separate png file
                               for z in range(sizeZ):
                                    # save slice images, starting with slice index 1
                                    pil_image_slice = Image.fromarray(reduced_image[z,:,:])
                                    pil_image_slice.save(os.path.join(OUTPUT_PATH,filename_prefix+"_"+row[1]['channel_name']+"_Z"+str(z+1)+".png"))
                            else: # single slice index starts with 1, numpy array with index 0 
                                pil_image_slice = Image.fromarray(reduced_image[SLICE-1,:,:])
                                pil_image_slice.save(os.path.join(OUTPUT_PATH,filename_prefix+"_"+row[1]['channel_name']+"_Z"+str(SLICE)+".png"))
                            
                        # count exported channels by name  
                        try:
                            c = count_channels[row[1]['channel_name']]
                        except KeyError:
                            c = 0
                            count_channels[row[1]['channel_name']] = 0
                        count_channels[row[1]['channel_name']] = c + 1
                        if filename_prefix not in written_image_names_list:
                            written_image_names_list.append(filename_prefix)
    
        print("Exported:")
        for exported_channel in count_channels.keys():
            print(count_channels[exported_channel], " ", exported_channel, " channel images")
        
        print("from ", len(written_image_names_list), " image files.")
            
        # Save list of prefixes in all.csv:
        with open(OUTPUT_PATH+"/all.csv","w+") as all_csv_file:
            for image_name in written_image_names_list:
                all_csv_file.write(image_name+"\n")  
    
    
    

























