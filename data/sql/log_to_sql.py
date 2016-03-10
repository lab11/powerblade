import os
import sys
import json
import pymysql.cursors

connection = pymysql.connect(host='localhost', 
	user='root',
	password='mysqlpw',
	db='whisperwood')

powerblades = 0
blees = 0
writecount = 0

#for file in os.listdir("."):
for root, dir, files in os.walk("."):
	for file in files:
		if file.startswith("gateway.log"):
			print()
			print(root)
			print(file)
			for line in open(root + '/' + file,'r'):
				json_data = json.loads(line)
				#print(json_data['device'])
				if json_data['device'] == "PowerBlade":
					#print(json_data)
					sql = "INSERT INTO powerblade_raw VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
					[date,time] = json_data['_meta']['received_time'].split('T')
					time = time[0:-1]
					datetime = date + ' ' + time
					with connection.cursor() as cursor:
						cursor.execute(sql, (json_data['_meta']['gateway_id'].replace(":",""),
							json_data['id'],
							json_data['sequence_number'],
							json_data['rms_voltage'],
							json_data['power'],
							json_data['energy'],
							json_data['power_factor'],
							datetime))
						connection.commit()
					powerblades += 1

				elif json_data['device'] == "BLEES":
					#print(json_data)
					sql = "INSERT INTO blees_raw VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
					[date,time] = json_data['_meta']['received_time'].split('T')
					time = time[0:-1]
					datetime = date + ' ' + time
					with connection.cursor() as cursor:
						cursor.execute(sql, (json_data['_meta']['gateway_id'].replace(":",""),
							json_data['id'],
							json_data['temperature_celcius'],
							json_data['light_lux'],
							json_data['pressure_pascals'],
							json_data['humidity_percent'],
							json_data['acceleration_advertisement'],
							json_data['acceleration_interval'],
							datetime))
						connection.commit()
					blees += 1

				writecount += 1
				if (writecount % 73) == 0:
					sys.stdout.write("Found: %i powerblade packets, %i blees packets \r" % (powerblades, blees) )
					sys.stdout.flush()

print()
