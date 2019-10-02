#!/usr/local/bin/python3

"""cleverAutomation.py - This script facilitates the ETL process needed to load data for Clever.com. Data is extracted
from PowerSchool export files, transformed into the proper csv files by this script, and uploaded to Clever and renamed
to ensure archival access to older files in case of data issues."""

__author__ = "Keith Medlin"
__copyright__ = "Chahtam County Schools 2019"
__credits__ = ["Keith Medlin", "Chatham County Schools"]
__license__ = "GNU GENERAL PUBLIC LICENSE 3.o"
__version__ = "1.2.1"
__maintainer__ = "Keith Medlin"
__email__ = "kmedlin@chatham.k12.nc.us"
__status__ = "Production"

import paramiko
import csv
import chardet
from datetime import datetime, timedelta
from os import rename, mkdir, path, rmdir
import shutil
import configparser
import json

# Set the the configuparser
config = configparser.ConfigParser()
config.read('config.ini')

# If the script directories do not exist, create them with the user 
# authorized to run this script.
if not path.exists("imports"): mkdir("imports")
if not path.exists("uploads"): mkdir("uploads")

# Set the current date to open and process files from PowerSchool
runDate = datetime.now().strftime('%Y-%m-%d')
# Set yesterday's date to archive existing files (if any exist)
yesterday = (datetime.now() - timedelta(1)).strftime('%m%d%y')

# Set the archive directory for files generated today. If it exists, remove it.
archiveDir = "uploads/uploaded-"+runDate
if path.exists(archiveDir):
    shutil.rmtree(archiveDir)
else:
    pass

# Generic function to download files based on the importFiles dictionary
def getfile(host, port, filepath, localpath, filename, username, password):
    paramiko.util.log_to_file(filename + '-dl.log')
    transport = paramiko.Transport(host, port)
    transport.connect(username=username, password=password)
    sftp = paramiko.SFTPClient.from_transport(transport)
    sftp.get(filepath + "/" + filename, localpath + filename)
    sftp.close()
    transport.close()


# Generic function to send files to Clever
def sendclever(localfile, remotefile):
    # Send the Clever files from Hopper to Clever's sFTP
    paramiko.util.log_to_file('paramiko-up.log')
    # Configure Paramiko
    host = config['clever']['host']
    port = int(config['clever']['port'])
    transport = paramiko.Transport(host, port)
    # Log into the server
    username = config['clever']['username']
    password = config['clever']['password']
    transport.connect(username=username, password=password)
    # Connect to Clever
    sftp = paramiko.SFTPClient.from_transport(transport)
    # Upload (put) the file
    localPath = localfile
    remotePath = remotefile
    sftp.put(localPath, remotePath)
    # Close the connection
    sftp.close()
    transport.close()

# Generic search function where you tell it which dictionary to lookup and the lookup term, and it'll return the key
# for the matched dictionary entry.
def search(my_dict, lookup, valueid):
    for key, value in my_dict.items():
        for v in value:
            v = str(v)
            if lookup in v:
                return value[valueid]

# Get the encoding of a file & return the encoding type
def get_encoding(sourcefile):
    rawdata = open(sourcefile, "rb").read()
    source_encoding = chardet.detect(rawdata)
    encoded_as = source_encoding['encoding']
    return encoded_as


# Check the current record for a student ID matching one of the student IDs
# that opted out of even being passed along to Clever.
def allow_student(student):
    found = False
    for key, value in opt_out.items():
        current_student = int(student)
        optout = int(value[0])
        if (current_student == optout):
            found = True
    if (found is True):
        return True
    else:
        return False

# Set our expected files for the day:
importFiles = {
    "teachersFile": [config['teachersfile']['host'], int(config['teachersfile']['port']), config['teachersfile']['remote_dir'], 
                    config['teachersfile']['local_dir'], config['teachersfile']['filename'], config['teachersfile']['username'], 
                    config['teachersfile']['password']],
    "homeroomsFile": [config['homeroomsfile']['host'], int(config['homeroomsfile']['port']), config['homeroomsfile']['remote_dir'], 
                    config['homeroomsfile']['local_dir'], config['homeroomsfile']['filename'], config['homeroomsfile']['username'], 
                    config['homeroomsfile']['password']],
    "studentsFile": [config['studentsfile']['host'], int(config['studentsfile']['port']), config['studentsfile']['remote_dir'], 
                    config['studentsfile']['local_dir'], config['studentsfile']['filename'], config['studentsfile']['username'], 
                    config['studentsfile']['password']]
}

uploadFiles = ["teachers.csv", "students.csv", "admins.csv", "schools.csv", "sections.csv",
               "enrollments.csv"]

# School dictionary - This can be edited to update school information should anything need to change for alignment
# or district growth.  The headers list generates the header for the output CSV file.
schoolsHeader = ["School_id", "School_name", "School_number"]

with open("schools.json", "r") as schools_file:
    schools = json.load(schools_file)

# Admin dictionary - This list is for the school-based admins.  It should be updated to accurately reflect the tech that
#  is acting as the clever admin for the school.  NOTE: Updates in the School List need to be reflected in the
# Admin List. The schoolAdminsHeader is the header file for the CSV output.
schoolAdminsHeader = ["School_id", "Admin_email", "Staff_id", "First_name", "Last_name"]
with open("schooladmins.json", "r") as admins_file:
    schoolAdmins = json.load(admins_file)


# Download the files necessary to process from the server(s)
for key, value in importFiles.items():
    getfile(value[0], value[1], value[2], value[3], value[4], value[5], value[6])

# Opt Out Dictionary - This will remove students who should not even be passed
# along to Clever by PowerSchool ID. It is found in the opt-out.json file.
with open("opt-out.json", "r") as optout_file:
    opt_out = json.load(optout_file)

# Create the admins.csv file
with open('admins.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(schoolAdminsHeader)
    for key, items in schoolAdmins.items():
        w.writerow(items)

# Create the schools.csv file
with open('schools.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(schoolsHeader)
    for key, items in schools.items():
        w.writerow(items)

# Read the Teacher Export file from PowerSchool into a dictionary.
readTeacher = csv.DictReader(open('imports/'+importFiles["teachersFile"][4]))
teacherList = {}
for row in readTeacher:
    key = row.pop('TEACHERS.SIF_StatePrid')
    if key in teacherList:
        # duplicate row handling logic here if we need it later...
        pass
    teacherList[key] = row

# Read the Sections Export File from PowerSchool into a dictionary.
readSection = csv.DictReader(open('imports/'+importFiles["homeroomsFile"][4]))
sectionList = {}
for row in readSection:
    key = row.pop('CC.DCID')
    if key in sectionList:
        # duplicate row handling logic here if we need it later...
        pass
    sectionList[key] = row

# Read the Student Export from PowerSchool into a dictionary.
file_encoding = get_encoding('imports/'+importFiles["studentsFile"][4])
readStudent = csv.DictReader(open('imports/'+importFiles["studentsFile"][4], encoding=file_encoding))
studentList = {}
for row in readStudent:
    key = row.pop('Student_Number')
    if key in studentList:
        # duplicate row handling logic here if we need it later...
        pass
    if (allow_student(key)==False):
        studentList[key] = row

# Write the teachers.csv file
with open('teachers.csv', 'w', newline='') as f:
    w = csv.writer(f)
    addedTeachers = []
    # Write the header
    w.writerow(['School_id', 'Teacher_id', 'Teacher_number', 'Teacher_email', 'First_name', 'Last_name', 'Username'])
    for key, value in teacherList.items():
        lookup = str(value['TEACHERS.SchoolID'])
        if search(schools, lookup, 0):
            # Get the school number
            schoolid = search(schools, lookup, 0)
            if value['TEACHERS.Email_Addr'] not in addedTeachers:
                if not not value['TEACHERS.Email_Addr']:
                    # If the teacher was found at a valid school from the school list, then write it to the file
                    addedTeachers.append(value['TEACHERS.Email_Addr'])
                    username = value['TEACHERS.Email_Addr'].split('@')[0]
                    w.writerow([schoolid, key, key, value['TEACHERS.Email_Addr'], value['TEACHERS.First_Name'],
                            value['TEACHERS.Last_Name'], username])
            else:
                pass
f.close()

# Write the students.csv file
with open('students.csv', 'w', newline='') as f:
    w = csv.writer(f)
    # Write the header
    w.writerow(['School_id', 'Last_name', 'First_name', 'Username',
                'Student_id', 'Student_email', 'Grade'])
    for key, value in studentList.items():
        lookup = str(value['SchoolID'])
        currentStudent = key
        # Ensure that the student has both a valid school and e-mail address before proceeding
        if lookup and currentStudent:
            if search(schools, lookup, 0):
                # Get the school ID number
                schoolId = search(schools, lookup, 0)
                # Set the student password and student grade from the current student's dictionary
                # entry
                studentGrade = value["Grade_Level"]
                # If the student was found at a valid school AND has
                # an e-mail address from the school list, write to the file
                w.writerow([schoolId, value['Last_Name'], value['First_Name'], value['Email'], 
                key, value['Email'], studentGrade])
f.close()

# Write the sections.csv file
with open('sections.csv', 'w', newline='') as f:
    w = csv.writer(f)
    # Write the header
    w.writerow(['School_id', 'Section_id', 'Teacher_id', 'Grade', 'Course_name', 'Course_number'])
    teacherSections = []
    for key, value in sectionList.items():
        lookup = str(value['TEACHERS.SIF_STATEPRID'])
        if lookup in teacherList:
            # Get the school ID number
            schoolid = teacherList.get(lookup, 0)
            if value['STUDENTS.GRADE_LEVEL'] == "0":
                crsGrade = "Kindergarten"
            else:
                crsGrade = value['STUDENTS.GRADE_LEVEL']
            # If the student was found at a valid school from the school list, write to the file
            row = ([schoolid['TEACHERS.SchoolID'], value['CC.SECTIONID'], value['TEACHERS.SIF_STATEPRID'],
                    crsGrade, value['COURSES.COURSE_NAME'], value['CC.COURSE_NUMBER']])
            # Eliminate any duplicate rows, only keep the first instance since this is just by sections
            # and not by student enrollments.
            if row not in teacherSections:
                teacherSections.append(row)
                w.writerow(row)
            else:
                continue
f.close()


# Write the enrollments.csv file
with open('enrollments.csv', 'w', newline='') as f:
    w = csv.writer(f)
    # Write the header
    w.writerow(['School_id', 'Section_id', 'Student_id'])
    for key, value in sectionList.items():
        currentStudent = studentList.get(value['STUDENTS.STUDENT_NUMBER'])
        if currentStudent is not None:
            w.writerow([currentStudent['SchoolID'], value['CC.SECTIONID'], value['STUDENTS.STUDENT_NUMBER']])
f.close()

# Send the files to Clever
for readyfile in uploadFiles:
    sendclever(readyfile, readyfile)
    pass

# Rename and move the files after they've been sent to Clever in a directory
# inside uploads that will allow you to see historical files.
for readyfile in uploadFiles:
    archiveName = readyfile[:-4]+runDate+".csv"
    rename(readyfile, archiveName)
    archiveDir = "uploads/uploaded-"+runDate
    if path.exists(archiveDir):
        pass
    else:
        mkdir(archiveDir)
    archFile = archiveDir+archiveName
    shutil.move(archiveName, archiveDir)
    