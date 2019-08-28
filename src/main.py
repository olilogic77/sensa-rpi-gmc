
from toolkit import Tk

serial_port = Tk.get_config( 'SERIAL_PORT', '/dev/ttyUSB0' )
serial_baud = Tk.get_config( 'SERIAL_BAUD', 115200 )
serial_timeout = Tk.get_config( 'SERIAL_TIMEOUT', 1.0 )
run_continuously = Tk.get_config( 'RUN_CONTINUOUSLY', False )
run_interval_sec = Tk.get_config( 'RUN_INTERVAL_SECONDS', 2.5 )
running = True

def main():
    Tk.info( "Application Starts [node_id: {}]...".format( Tk.get_sensa_node_id() ) )
    #//
    global running
    node_id = Tk.get_sensa_node_id()
    sensor_id = Tk.get_config( 'SENSOR_ID', '04' )
    device = Tk.open_serial( serial_port, serial_baud, serial_timeout )
    while running:
        #//
        device.write('<GETCPM>>')
        raw = device.read(2)
        if raw=='' or len(raw)<2:
            Tk.error( "cpm reading not valid '{}'".format(val) )
        else:
            val = struct.unpack( ">H", raw)[0]
            Tk.save_sensa_datafile( node_id, sensor_id, val )
        #//
        if not run_continuously:
            running = False
        if running:
            sleep( run_interval_sec )
    #//
    Tk.info( 'Application Ends...' )
