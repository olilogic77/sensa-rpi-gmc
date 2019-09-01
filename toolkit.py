#!/usr/bin/python

import daemon
import datetime
import json
import lockfile
import os
from pathlib2 import Path
import random
import redis
import serial
import setproctitle
import signal
import struct
import sys
import time

class Tk:

    #//
    #// CONFIG
    #//

    __this_path = os.path.dirname(os.path.realpath(__file__))
    __key_sensa_node_id = 'SENSA_NODE_ID'
    __sensa_node_id_etc_path = '/etc/sensaweb/node_id' #// EVERY DEVICE SHOULD HAVE A UNIQUE 8 DIDGIT HEX AT THIS LOCATION
    __config = None
    __proc_name = None #// PLEASE ACCESS WITH Tk.app_get_proc_name()
    __log_file_path = None
    __log_file_next_rotate = None
    __sensa_data_queue_name = None #// PLEASE ACCESS WITH Tk.queue_get_name()
    __queue = None #// PLEASE ACCESS WITH Tk.queue_get()

    with open( os.path.join( __this_path, 'config.json' ) ) as config_file:
        __config = json.load( config_file )

    if not __key_sensa_node_id in __config:
        try:
            node_id = Path( __sensa_node_id_etc_path ).read_text().rstrip('\n').rstrip('\r').rstrip(' ')
            if node_id == '':
                raise Exception()
            __config[__key_sensa_node_id] = node_id
        except:
            print("FAULT: a node id file doesn't exist, can't be read or is empty. '{}'.".format( __sensa_node_id_etc_path ) )
            sys.exit(499)

    @staticmethod
    def get_config( key, default_value ): #// GET THE CONFIG VALUE OR, IF IT DOESN'T EXIST, RETURN A SUPPLIED DEFAULT
        if key in Tk.__config:
             return Tk.__config[ key ]
        return default_value

    @staticmethod
    def get_sensa_node_id(): #// SPECIAL CONFIG SETTNIG THAT MUST EXIST AND IS UNIQUE FOR EVERY DEVICE (RASPBERRYPI)
        return Tk.get_config( Tk.__key_sensa_node_id, '000000' )

    #//
    #// PATH SETUP ON RASPBERRY PI
    #//

    @staticmethod
    def get_path_tmpfs( relative_path='' ): #// HIGHLY ACTIVE IO SHOULD GO TO A RAMDRIVE TO PREVENT SDCARD WEAR.
        return os.path.join( Tk.get_config( 'PATH_TMPFS', '/var/sensaweb-tmpfs' ), relative_path)

    @staticmethod
    def get_path_archive( relative_path='' ): #// VERY RARELY (OR FOR VERY IMPORTANT DATA), SAVE TO THE SDCARD.
        return os.path.join( Tk.get_config( 'PATH_ARCHIVE', '/opt/sensaweb' ), relative_path)

    #//
    #// SENSOR STUFF
    #//

    @staticmethod
    def get_epoch_sec_utc( d=time.time() ): #// UTC SECONDS SINCE EPOCH
        return long( d )

    #// NOT REQUIRED - SWITHC OVER TO USING REDIS FOR QUEUEING DATA
    # @staticmethod
    # def save_sensa_datafile( node_id, sensor_id, file_txt ): #// DATAFILES ARE CREATED WITH THE FILE NAME epochSeconds-nodeId-sensorId-randomAlphas, CONTAINING THE CURRENT READINGS(S)
    #     tme = long(time.time())
    #     rnd = ''.join( random.choice('abcdefghijklmnopqrstuvwxyz') for i in range( 6 ) )
    #     file_name = "{}-{}-{}-{}".format( tme, node_id, sensor_id, rnd )
    #     file_path = os.path.join( Tk.get_path_tmpfs(), Tk.get_config( 'DATAFILE_FOLDER', 'datafile' ), file_name)
    #     Tk.info( 'creating datafile {} [{}]'.format(file_path, file_txt ) )
    #     Tk.write_text_file( file_path, file_txt )

    #//
    #// REDIS LIFO QUEUE
    #//

    @staticmethod
    def queue_get_name():
        if Tk.__sensa_data_queue_name is None:
             Tk.__sensa_data_queue_name = Tk.get_config( 'SENSA_DATA_QUEUE_NAME', 'SENSA_DATA_QUEUE' )
        return Tk.__sensa_data_queue_name

    @staticmethod
    def queue_get():
        if Tk.__queue is None:
            Tk.__queue = redis.Redis()
        return Tk.__queue

    @staticmethod
    def queue_publish( node_id, sensor_id, msg_txt  ):
        tme = long(time.time())
        rnd = ''.join( random.choice('abcdefghijklmnopqrstuvwxyz') for i in range( 6 ) )
        dat = '{}_{}_{}_{}_{}'.format( tme, node_id, sensor_id, msg_txt, rnd )
        Tk.info( 'publishing data to queue: {}'.format( dat ) )
        Tk.queue_get().lpush( Tk.queue_get_name(), dat )

    #//
    #// LOGGING
    #//

    __log_level = 2
    __log_level_text = [ 'DEBUG', 'INFO', 'WARN',  'ERROR', 'FAULT' ]

    DEBUG = 1
    INFO = 2
    WARN = 3
    ERROR = 4
    FAULT = 5

    @staticmethod
    def __validate_level(level): #// LOG LEVELS MUST BE BETWEEN 1 AND 5
        if level<1:
            return 1
        if level>5:
            return 5
        return level

    @staticmethod
    def set_log_level( level ): #// PUBLIC INTERFACE TO SET THE LOG LEVEL
        __log_level = Tk.__validate_level( level )

    @staticmethod
    def is_logging(level): #// RETURNS TRUE IF THE GIVEN LOG LEVEL IS CURRENTLY SET TO BE LOGGED
        lev = Tk.__validate_level( level )
        return ( lev >= Tk.__log_level )

    @staticmethod
    def log( msg, level=2 ):
        if Tk.is_logging( level ):
            stm = datetime.datetime.now().strftime( '%Y%m%d.%H%M%S%z' )
            print( stm + ' ' + Tk.__log_level_text[ level-1 ] + ': ' + msg )
            #// log_file_path
            #// log_file_next_rotate
            #// if log path is null generate log path and set next log rotate
            #// if at next log rotate, set net path, zip existing, movee existing delete existing
            #// TODO: wirte to temp storage and roll to permainent storatage every X hours. (6?)

    @staticmethod
    def debug( msg ): #// CONVENIENCE FUNCTION FOR LOGGING DEBUGS
        Tk.log( msg, 1 )

    @staticmethod
    def info( msg ): #// CONVENIENCE FUNCTION FOR LOGGING INFO
        Tk.log( msg, 2 )

    @staticmethod
    def warn( msg ): #// CONVENIENCE FUNCTION FOR LOGGING WARNINGS
        Tk.log( msg, 3 )

    @staticmethod
    def error( msg ): #// CONVENIENCE FUNCTION FOR LOGGING ERROR
        Tk.log( msg, 4 )

    @staticmethod
    def fault( msg, error_number = 400 ):  #// CONVENIENCE FUNCTION FOR LOGGING FAULTS AND EXITING THE APP
        Tk.log( msg, 5 )
        Tk.is_running = False
        time.sleep( 5 ) #// TRY TO LET THE APP EXIT GRACEFULLY?
        sys.exit( error_number )

    #//
    #// SERIAL COMMS AND DATA CONVERSIONS
    #//

    @staticmethod
    def serial_open( port, baud, timeout=1.0 ): #// OPEN A GIVEN COM PORT (SERIAL PORT) FOR ONGING COMMUNICATION
        try:
            comport = serial.Serial( port, baudrate=baud, timeout=timeout )
            return comport
        except serial.serialutil.SerialException:
            Tk.fault( 'cannot open serial connection, port: {}, baud: {}.'.format( port, baud ) )
            sys.exit(408)

    @staticmethod
    def serial_command( comport, cmd, reply_length ): #// SEND A COMMAND TO AN OPEN COMPORT
        comport.write( '<GETCPM>>' )
        return comport.read( reply_length )

    @staticmethod
    def convert_msf_unsgned_short_to_string( raw ): #// SOMETIMES SERIAL DEVICES SEND WEIRDLY ENCODED RESPONSES - LETS DECODE IT
        return struct.unpack(">H", raw)[0]

    #//
    #// FILES
    #//

    @staticmethod
    def read_text_file( path ):
        try:
            return Path( path ).read_text()
        except:
            return ''

    @staticmethod
    def write_text_file( path, txt ):
        wtr = None
        try:
            wtr = open( path, "w" )
        except IOError:
            os.makedirs( os.path.dirname( path ) )
            wtr = open( path, "w" )
        wtr.write( "{}".format(txt) )
        wtr.close()

    #//
    #// DEAMON
    #//

    is_running = True

    is_continuous = True

    start_type = 'o' #// [ o=once, d=daemon, c=continuous ]

    @staticmethod
    def app_start( fn_main ):
        setproctitle.setproctitle( Tk.app_get_proc_name() )
        Tk.info('application starting [ process_name: {}, node_id: {} ] ...'.format( Tk.app_get_proc_name(), Tk.get_sensa_node_id() ))
        if len( sys.argv ) > 1:
            start_arg = '{}'.format(sys.argv[1]).lower()
            if start_arg == '-c' or start_arg == '--continuous':
                Tk.start_type = 'c'
            if start_arg == '-d' or start_arg == '--daemon':
                Tk.start_type = 'd'
        if Tk.start_type == 'd':
            Tk.app_daemon( fn_main ) #// START A DAEMON THAT CALLSBACK THE MAIN FUNCTION
        else:
            fn_main() #// CALLBACK THE MAIN FUNCTION

    @staticmethod
    def app_pause( sleep_sec = 1 ):
        if Tk.start_type == 'o':
            Tk.is_running = False
        else:
            time.sleep( sleep_sec )

    @staticmethod
    def app_terminate():
         Tk.info('received termination signal...')
         Tk.is_running = False
         time.sleep(5)
         Tk.info('exiting...')
         sys.exit(0)

    @staticmethod
    def app_get_proc_name():
        if Tk.__proc_name==None:
            proc_name = Tk.__this_path
            pos = len( proc_name ) - proc_name.rfind('/') - 1
            proc_name = proc_name[-pos:]
            Tk.__proc_name = Tk.get_config( 'PROCESS_NAME', proc_name )
        return Tk.__proc_name

    @staticmethod
    def app_daemon( fn_main ):
        Tk.info( "Starting Daemon, expect no further output to console..." )
        pid_path = Tk.get_config( 'PID_FILE_PATH', '/var/run/' + Tk.app_get_proc_name() + '.pid' )
        with daemon.DaemonContext(
            working_directory = Tk.__this_path,
            pidfile = lockfile.FileLock( pid_path ),
            umask=0o002,
            detach_process=True,
            signal_map = {
              signal.SIGTERM: Tk.app_terminate,
              signal.SIGTSTP: Tk.app_terminate,
            }
        ):
            fn_main()
