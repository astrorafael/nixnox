# TODO
* New GeoCoords enum {SINGLE, MEDIAN}. coords_meas column in Location
* Fill temperature_1 with median(T_sensor)
* Add gps_latitude, gps_longitude, gps_masl to Measurement (only for TAS)
* Import --ammend to get bat_volt
* Three types of export:
	- Database mirror
	- Compact, with lots of metadata and no GPS Coords nor T_Sensor
	- Tabular, with all flags in data columns, and descriptive flags in columns and no metadata
* Import:
	- tailored to the Photometer type
	- --ammend option to get bat_volt from .txt file
	- include individual GPS readings for TAS
	- Compute median of T_sensor -> temperature_1
	- Compute median of GPS readings -> Location
