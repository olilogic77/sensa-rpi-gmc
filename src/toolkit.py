import datetime
import json
import serial
import sys
import os
import time
import random
from pathlib2 import Path

class Tk:

    #//
    #// CONFIG
    #//

    __this_path = os.path.dirname(os.path.realpath(__file__))
    __key_sensa_node_id = 'SENSA_NODE_ID'
    __sensa_node_id_etc_path = '/etc/sensaweb/node_id'
    __config = None

    with open( os.path.join( __this_path, '../config/config.json' ) ) as config_file:
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
    def get_config( key, default_value ):
        if key in Tk.__config:
             return Tk.__config[ key ]
        return default_value

    @staticmethod
    def get_sensa_node_id():
        return Tk.get_config( Tk.__key_sensa_node_id, '000000' )

    #//
    #// PATH SETUP ON RASPBERRY PI
    #//

    @staticmethod
    def get_path_tmpfs( relative_path='' ):
        return os.path.join( Tk.get_config( 'PATH_TMPFS', '/var/sensaweb-tmpfs' ), relative_path)

    @staticmethod
    def get_path_archive( relative_path='' ):
        return os.path.join( Tk.get_config( 'PATH_ARCHIVE', '/opt/sensaweb' ), relative_path)

    #//
    #// SENSOR STUFF
    #//

    @staticmethod
    def get_epoch_sec_utc( d=time.time() ):
        return long( d )

    @staticmethod
    def save_sensa_datafile( node_id, sensor_id, file_txt ):
        tme = long(time.time())
        rnd = ''.join( random.choice('abcdefghijklmnopqrstuvwxyz') for i in range( 6 ) )
        file_name = "{}-{}-{}-{}".format( tme, node_id, sensor_id, rnd )
        file_path = os.path.join( Tk.get_path_tmpfs(), Tk.get_config( 'DATAFILE_FOLDER', 'datafile' ), file_name)
        Tk.info( 'creating datafile {}'.format(file_path) )
        Tk.write_text_file( file_path, file_txt )
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
    def __validate_level(level):
        if level<1:
            return 1
        if level>5:
            return 5
        return level

    @staticmethod
    def set_log_level( level ):
        __log_level = Tk.__validate_level( level )

    @staticmethod
    def is_logging(level):
        lev = Tk.__validate_level( level )
        return ( lev >= Tk.__log_level )

    @staticmethod
    def log( msg, level=2 ):
        if Tk.is_logging( level ):
            stm = datetime.datetime.now().strftime( '%Y%m%d.%H%M%S%z' )
            print( stm + ' ' + Tk.__log_level_text[ level-1 ] + ': ' + msg )

    @staticmethod
    def debug( msg ):
        Tk.log( msg, 1 )

    @staticmethod
    def info( msg ):
        Tk.log( msg, 2 )

    @staticmethod
    def warn( msg ):
        Tk.log( msg, 3 )

    @staticmethod
    def error( msg ):
        Tk.log( msg, 4 )

    @staticmethod
    def fault( msg, error_number = 400 ):
        Tk.log( msg, 5 )
        sys.exit( error_number )

    #//
    #// SERIAL COMMS
    #//

    @staticmethod
    def open_serial( port, baud, timeout=1.0 ):
        try:
            comport = serial.Serial( port, baudrate=baud, timeout=timeout )
            return comport
        except serial.serialutil.SerialException:
            Tk.fault( 'cannot open serial connection, port: {}, baud: {}.'.format( port, baud ) )
            sys.exit(408)

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
        wtr.write( "".format(txt) )
        wtr.close()
