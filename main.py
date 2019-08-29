#!/usr/bin/python

from toolkit import Tk

serial_port      = Tk.get_config( 'SERIAL_PORT', '/dev/ttyUSB0' )
serial_baud      = Tk.get_config( 'SERIAL_BAUD', 115200 )
serial_timeout   = Tk.get_config( 'SERIAL_TIMEOUT', 1.0 )
run_interval_sec = Tk.get_config( 'RUN_INTERVAL_SECONDS', 2.5 )
sensor_id        = Tk.get_config( 'SENSOR_ID', '04' ) #// GMC CPM
node_id          = Tk.get_sensa_node_id()

#// MAIN APPLICATION
def main():
    Tk.info( "Main Loop starts ..." )
    comport = Tk.serial_open( serial_port, serial_baud, serial_timeout )
    while Tk.is_running:
        raw = Tk.serial_command( comport, '<GETCPM>>', 2 )
        if raw=='' or len(raw)<2:
            Tk.error( "cpm reading not valid '{}'".format(val) )
        else:
            val = Tk.convert_msf_unsgned_short_to_string( raw )
            Tk.save_sensa_datafile( node_id, sensor_id, '{:.4f}'.format(val) )
        Tk.app_pause( run_interval_sec )
    Tk.info( 'Main Loop Ends...' )

#// MANAGE APP START UP
if __name__ == "__main__":
        Tk.app_start( main )
