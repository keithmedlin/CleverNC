# Clever Automation Script
Automation script to prepare and upload files to Clever.

When deploying this script, you will need to create the following folders:
* imports/
* uploads/

Be sure to install dependencies that will be needed as well:
* paramiko
* chardet
* configparser

## Import Files
There are 4 required files to run this script:
* Sections & Enrollments from PowerSchool
* All Students in the grade levels you are supporting in Clever
* The Student password file, linking students between this file and the All Students file via their student id number.
* All Teachers

### Sections & Enrollments
In PowerSchool, you'll need to create an Export Template through the Data Export Manager that pulls the following columns from the "Student Information" Category and the Export From "Student: Course Data" -
* CC.DCID
* CC.COURSE_NUMBER
* CC.SECTIONID
* TEACHERS.SIF_STATEPRID
* STUDENTS.STUDENT_NUMBER
* STUDENTS.GRADE_LEVEL
* COURSES.COURSE_NAME
* SECTIONS.GRADE_LEVEL

Make sure that the "School Years" are updated to reflect the current school year or you may pull older school year sections.

As you filter, you'll want to configure your filters to ensure that CC.SECTIONID > = 1 to ensure you're getting a valid section.

This file will create the courses and sections and enroll students in them within Clever. It does 99% of the work and usually issues that come up with data in Clever can be traced back to this file.

### All Students File
In PowerSchool, you'll need to create an Export Template through the Data Export Manager that pulls the following columns from the "PowerSchool Data Sets" Category and the Export From "Student Email" -
* Student_Number
* First_Name
* Last_Name
* Email
* SchoolID

This file is used to help enroll students in courses and the number found in the Student_Number field is used to match the password found in the Student Password File. 

We typically do not filter this file, but your mileage may vary.

### Student Password File
In whatever password management solution you use, you'll need to export a file that contains the following columns for every student that will be active in Clever - 
* Last Name as "Surname"
* First Name as "GivenName"
* Password as "AccountPassword"
* Email as "EmailAddress"
* Student ID Number as "EmployeeNumber"
* Grade as "GradeLevel"

These fields are used to validate data in the script and to ensure the right student is getting the right password.

### Teachers_Export File
In PowerSchool, you'll need to create an Export Template through the Data Export Manager that pulls the following columns from the "Staff Information" Category and the Export From "Teachers" -
* TEACHERS.SIF_StatePrid
* TEACHERS.SchoolID
* TEACHERS.Email_Addr
* TEACHERS.Last_Name
* TEACHERS.First_Name
* TEACHERS.Status

You'll want to filter by SchoolID > = 1 with a Status = 1 or you may end up with a bunch of conflicting information in your file.

## Application Configuration

### sample-config.ini
This file contains your configuration to locate the various files necessary to make this script work. You do not need to add quotes becuase all data in the ini file are treated as strings.  Once completed, rename the file to config.ini and place it in the same directory as cleverAutomation.py.

### schools-sample.json
This file contains the dictionary where you will set up your schools and school codes. The file MUST be configured with the key as the school id number and then, in order the "School_id", "School_name", and "School_number" columns. Once completed, rename the file to schools.json and place it in the same directory as cleverAutomation.py.

### schooladmins-sample.json
This file contains the dictionary to set up clever admins in the admins file that gets uploaded. You can give the dictionary keys any name that you can keep track of, but we landed on school abbreviations and numbers. The columns, in order are "School_id", "Admin_email", "Staff_id", "First_name", and "Last_name."
