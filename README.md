# SensaWeb Geiger Muller Counter data collector for RaspberryPi + USB GMC-320
## sensa-rpi-gmc
This application is intended to run as a daemon on a RaspberryPi with a US?B attached GMC-320, saving radiation data to a redis queue at given time intervals.

It is expected that another daemon will deal with transferring the data from the queue to data collection points (whether that is a GCP Pub/Sub MTTQ endpoint, a file server, an FTP server, a REST or API interface or similar...)

## Installing
### Prerequisites
Please ensure this is run on a RaspBerryPi SOE to this [specification](https://docs.google.com/document/d/1jozOgvoRr-YjEnIei4Qec-8yUqV9Lcj5qD3pq0XaMCU/edit), including:
* a sensaweb user
* a /etc/sensaweb/node_id file created
* redis server, python client and c libs (redis-server, python-redis, libhiredis-dev)
* python libs (python-serial python-pathlib2 python-lockfile python-daemon python-setproctitle)
### Running manually
To run the app manually you first download the app:
```
$ git clone https://github.com/olilogic77/sensa-rpi-gmc
$ cd sensa-rpi-gmc
```
To run the app:
```
$ python main.py
```

This will open the application and run it once. To run it continuously (control+c to exit):
```
$ python main.py -c
$ python main.py --continuous
```

And to execute it as a daemon (`$ pkill sensa-rpi-gmc` to close the daemon):
```
$ python main.py -d
$ python main.py --daemon
```
### the config file
Leave the config file empty to use all the defaults compiled into the application,
add config variables to override compiled values where ever you see Tk.get_config() used.
// TODO! move detail
### Production install
// TODO


## License
See the LICENSE file in this directory
