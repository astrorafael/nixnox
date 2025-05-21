# TODO

* Test ECSV import routine
* Deployment using docker
	- Enviroment variables, sql connection
	- External Volume
* Manual data entry
* Authorised users?

* Protegerese de ECSV invalidos, coger la excepcion
* Listar los N ultimos resultados de sumario y decir cuantas observaciones hay en la base de datos
  (limit, y order by timestamp_1 desc)
* Group by observation_id en lkugar del distinct
* Home page debe de convertirse en Search Page:
	- By Datetime range
	- By Location (coords box o ciudad) (&datetime desc)
	- By Observer (& datetime desc)
	- By Photometer (& datetime desc)
* variables de entorno para distintas configuraciones de BD en .streamlit(/secrets.toml y justfile)
* Dockerfile para desarrollo con sqlite3 y para produccion (maria?)
* desplegar docker en la respberry
* cerfificado real de stars4all?