import arcpy
import os

# Open an InsertCursor.
# Specify the location for the desired feature. The sample inserts the values into the field, NAME and SHAPE.

cursor = arcpy.da.InsertCursor("ntp_2025_2036",
                               ("OID_ntpliste","Delstrekning", "SHAPE@"))

# Insert new rows that include the county name and the x and y coordinate
# pair that represents the county center

for row in delstrekninger:
    rad = [row[0]['oid'], row[0]['delstrekning'], row[0]['geometri']]
    cursor.insertRow(row)

# Delete cursor object

del cursor
