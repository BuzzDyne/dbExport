#!/usr/bin/python3

# Vibsense Report Generator
# Author: David Lucas <david@lynxemi.com>
# Company: Lynxemi Pte Ltd, Singapore
# Date: 2020-02-25

import csv
from MySQLdb import _mysql
import json

db_name = "vibro"
db_host = "vibsense.net"
db_user = "vibro"
db_passwd = "a6u0Ok1yXT1rt4TM"
print("ok")

try:
	db = _mysql.connect(host=db_host, user=db_user, passwd=db_passwd, db=db_name)
except Exception as e:
	print(e)

print("ok")

# Uncomment the following 2 lines for tremack1
# sensors = [51,52,53,54,55]
# fname = "tremack1"

# Uncomment the following 2 lines for indahkiatserang
#sensors=[56,57,58,59,60,61,62,63,64,65,68]
#fname = "indahkiatserang"

# Uncomment the following 2 lines for ikserang2
sensors=[66,69,70,71,72,73,74]
fname = "ikserang2"

# start_date = "2020-02-21 17:00:00" 	# 2020-02-22 00:00:00 IDT
# end_date = "2020-02-22 17:00:00"	    # 2020-02-23 00:00:00 IDT

start_date = "2020-04-26 17:00:00" 	    # 2020-02-23 00:00:00 IDT
end_date = "2020-05-02 17:00:00"	    # 2020-02-28 00:00:00 IDT

indexT = 1
indexI = 0

with open('%s.csv' % (fname), mode='w', newline='') as export_file:
    for sensor in sensors:
        count = db.query("""SELECT * FROM reports JOIN sensors ON reports.sensor = sensors.id WHERE reports.sensor = %d AND reports.timestamp > '%s' AND reports.timestamp < '%s'""" % (sensor, start_date, end_date))
        r=db.use_result()

        export_writer = csv.writer(export_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        export_writer.writerow(["sens_id", "timestamp", "batt", "temp", "x_peak", "y_peak", "z_peak", "x_rms", "y_rms", "z_rms"])

        a=True
        while(a):
            row = r.fetch_row()
            if row == ():
                a = False
            else:
                timestamp = row[0][2].decode('utf-8') # timestamp
                sens_id = row[0][7].decode('utf-8') # sensor.sensor_id
                temp = json.loads(row[0][3])["temp"]
                batt = json.loads(row[0][3])["batt"]
                x_peak = json.loads(row[0][4])["0"]["x"][0]
                y_peak = json.loads(row[0][4])["0"]["y"][0]
                z_peak = json.loads(row[0][4])["0"]["z"][0]
                x_rms = json.loads(row[0][4])["0"]["x"][1]
                y_rms = json.loads(row[0][4])["0"]["y"][1]
                z_rms = json.loads(row[0][4])["0"]["x"][1]

                export_writer.writerow([sens_id, timestamp, batt, temp, x_peak, y_peak, z_peak, x_rms, y_rms, z_rms])
                indexI += 1
                print("{}, Step {}".format(indexT,indexI))

            indexT += 1
		
print("File %s_%s-%s.csv written" % (fname,start_date,end_date))
