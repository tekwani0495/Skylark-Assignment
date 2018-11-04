from os import chdir,getcwd #for navigating directories
from math import sin, cos, sqrt, asin, radians #used in determining the distance between coordinates
import glob #used to traverse the images
import pysubs2 #used in parsing the srt file
import piexif #used in reading the exif data from the images
import csv #used to read the assets csv file, and the save the data
import simplekml #used to write the kml data for the drone
from  tkinter import * #used for the GUI
from tkinter import filedialog
import tkinter, tkconstants, filedialog #used for basic GUI elements

def main():

    main_dir=getcwd() #gets current directory, to move back to when saving files

    print ("How many videos do you want to run the program for?")

    valid_entry=False #used with try and catch block to get proper input

    while (valid_entry!=True): #try/catch for getting number of videos
        try:
            number_of_vids=int(input()) #stores number of videos as string
            if(number_of_vids>0):
                valid_entry=True
        except:
            print ("Please enter it in integer digits")

    number_of_vids_integer=int(number_of_vids) #stores number of videos as integer

    for counter_1 in range(number_of_vids_integer): #main loop, this runs till all videos and points of interest have been covered

        print ("Please select the folder of images for video %s"%((counter_1+1)))

        image_dir = Tk()
        image_dir.withdraw()
        image_dir.lift()
        image_dir.title('Select the image folder')
        image_dir_path = filedialog.askdirectory() #This is used to find the directory which contains the pictures. The GUI used is from Tkinter
        image_dir.destroy()

        chdir(image_dir_path) #moves into image directory so that glob can work easily

        all_image_gps_data=[] #list to hold the image name, latitude and longitude in that order

        for filename in glob.iglob('./*.jpg'): #this loop goes through all the images and gets the lat/long via piexif
            exif_data_placeholder=exif_data_pull(filename)

            all_image_gps_data.append(exif_data_placeholder)

        chdir(main_dir)

        print ("What distance (in metres) do you want to set for the video?")

        valid_entry=False

        while(valid_entry!=True): #try/catch to get the distance for images

            try:
                video_distance=int(input())
                if(video_distance>0):
                    valid_entry=True
            except:
                print ("Please enter it in integer digits")

        print ("Please select the srt file for the video")

        srt_file_select=Tk()
        srt_file_select.withdraw()
        srt_file_select.lift()
        srt_filename=filedialog.askopenfilename(initialdir = image_dir_path, title = "Select SRT file",filetypes = (("SRT File","*.SRT"),("all files","*.*")))
        srt_file_select.destroy() #GUI via tkinter to select the srt file

        srt_data=srt_data_pull(srt_filename) #send filename to receive the data
	
        srt_full_data=distance_compare(srt_data,all_image_gps_data,video_distance) #this gets the data of which images are within range at what seconds
        write_to_csv(zip(*srt_full_data),"Images at Video Timings",counter_1) #sends data to be stored in csv

        print ("What distance (in metres) do you want to set for the points of interest?")

        valid_entry=False

        while(valid_entry!=True): #try/catch to get the distance for points of itnerest

            try:
                poi_distance=int(input())
                if(poi_distance>0):
                    valid_entry=True
            except:
                print ("Please enter it in integer digits")

        print ("Please select the csv file for the points of interest")

        csv_file_select=Tk()
        csv_file_select.withdraw()
        csv_file_select.lift()
        csv_filename=filedialog.askopenfilename(initialdir = image_dir_path, title = "Select CSV file",filetypes = (("Comma Separated Values","*.csv"),("all files","*.*")))
        csv_file_select.destroy() #GUI via tkinter to select the csv file

        csv_data=csv_data_pull(csv_filename) #sends filename to get the data
        csv_full_data=distance_compare(csv_data,all_image_gps_data,poi_distance) #this gets the data of images within range of points of itnerest
        write_to_csv(zip(*csv_full_data),"Images near Points of Interest",counter_1) #sends data to be stores in csv

        create_kml(zip(*all_image_gps_data),"KML File of Drone Flight",counter_1) #sends coordinates and image names to create a kml of the drone flight path

    input("All done. Press enter to exit") #self explanatory

def exif_data_pull(image_name): #function to get gps data from an image. uses piexif

    exif_dict = piexif.load(image_name) #copies dictionary of all imag eexif data

    gps_data_dump = exif_dict.pop("GPS") #dictionary key is 'gps' for gps data

    try: #the program was running into nulls at the end of the folder. this block prevents that from stopping execution, and saves gps data to be parsed further on
        latitude=[gps_data_dump[2][0],gps_data_dump[2][1],gps_data_dump[2][2]]

        longitude=[gps_data_dump[4][0],gps_data_dump[4][1],gps_data_dump[4][2]]

        gps_data=[]

        gps_data.append(float(latitude[0][0]))
        gps_data.append(float(latitude[1][0]))
        gps_data.append(float(latitude[2][0]))

        gps_data.append(float(longitude[0][0]))
        gps_data.append(float(longitude[1][0]))
        gps_data.append(float(longitude[2][0]))

        gps_data_true=dms_to_dd(gps_data[0],gps_data[1],gps_data[2],gps_data[3],gps_data[4],gps_data[5]) #the data is in dms format initially, whereas the other files use dd.
    except:
        print ("End of files")
        gps_data_true=0

    if (gps_data_true==0):
        return []

    return image_name,gps_data_true[0],gps_data_true[1]

def dms_to_dd(deg_1,min_1,sec_1,deg_2,min_2,sec_2): #this function converts gps co ordinates from dms to dd format

    placeholder_1=float(min_1+(sec_1/60))
    placeholder_1=float(deg_1+(placeholder_1/60))

    placeholder_2=float(min_2+(sec_2/60))
    placeholder_2=float(deg_2+(placeholder_2/60))

    return placeholder_1,placeholder_2

def get_gps_distance(latitude_1,longitude_1,latitude_2,longitude_2): #this function returns the gps distance between two latitudes and longitudes using the Haversine formula
    approx_earth_radius = 6372.8

    lat_1=float(radians(latitude_1))
    lat_2=float(radians(latitude_2))
    difference_latitude =float(radians(latitude_2-latitude_1))
    difference_longitude =float(radians(longitude_2-longitude_1))

    placeholder_1 =float(sin(difference_latitude / 2)**2 + cos(lat_1) * cos(lat_2) * sin(difference_longitude / 2)**2)
    placeholder_2 =float(2*asin(sqrt(placeholder_1)))

    gps_distance=approx_earth_radius*placeholder_2

    return gps_distance

def is_within_distance(main_gps,list_gps,distance_to_check): #this functions runs the coordinates against the list extracted from the exif data, checkign which images are enarby

    within_range=[]

    for counter_1 in range((len(list_gps))):
        found_gps_distance=(get_gps_distance(main_gps[0],main_gps[1],list_gps[counter_1][1],list_gps[counter_1][2])/1000)

        if(found_gps_distance<distance_to_check):

            within_range.append(str(list_gps[counter_1][0]))
            within_range.append("|")

    return within_range

def srt_data_pull(srt_file): #this function pulls the time and coordinates from the srt files, using pysubs2
    subs_file=pysubs2.load("./software_dev/videos/DJI_0301.SRT")
    ordered_subs_lat=[]
    ordered_subs_long=[]
    ordered_subs_time=[]

    for line in subs_file:
        ordered_subs_time.append((int(line.start))/1000) #time is extracted in milliseconds. we need it in seconds, so it's rounded down.
        text_placeholder=(line.text).split(',')
        ordered_subs_lat.append(float(text_placeholder[0]))
        ordered_subs_long.append(float(text_placeholder[1]))

    ordered_subs_final=[ordered_subs_time,ordered_subs_lat,ordered_subs_long]

    return ordered_subs_final

def write_to_csv(data_to_write,title,serial_number): #this function writes the data to csv files, placed in the same directory as the python script

    title=title+str(serial_number) #title formatting

    csv_file=open('%s.csv'%title,'w')
    with csv_file:
        writer=csv.writer(csv_file,dialect='excel')
        writer.writerows(data_to_write)
    csv_file.close()

    current_dir=getcwd()

    print ("File saved at %s"%current_dir)

def distance_compare(data_list_1,data_list_2,distance): #this runs two lists against each other, getting all locations in the second within range of each location of the first.
    location_list=[]
    image_list=[]

    for counter_1 in range(len(data_list_1[0])):
        location_data_holder=[data_list_1[1][counter_1],data_list_1[2][counter_1]]
        image_holder=is_within_distance(location_data_holder,data_list_2,distance)

        location_list.append(data_list_1[0][counter_1])
        image_list.append(str(image_holder))
    final_data=[location_list,image_list]

    return final_data

def csv_data_pull(csv_file): #pulls the data from the csv file. make sure the titles of the columns are accurate

    location_list=[]
    lat_list=[]
    long_list=[]

    with open(csv_file) as file_to_read:
        reader = csv.DictReader(file_to_read)
        for row in reader:
            location_list.append(row['asset_name'])
            lat_list.append(float(row['latitude']))
            long_list.append(float(row['longitude']))

    full_csv_data= [location_list,lat_list,long_list]

    return full_csv_data

def create_kml(data_to_write,title,serial_number): #creates a kml file via simplekml
    title=title+str(serial_number)
    title=title+".kml"
    kml=simplekml.Kml()

    for row in data_to_write:
        kml.newpoint(name=row[0], coords=[(row[2],row[1])]) #the data is stored in the list as name/lat/long, but kml files store it as name/long/lat
    kml.save(title)

    current_dir=getcwd()

    print ("File saved at %s"%current_dir)

main() #for simple execution
