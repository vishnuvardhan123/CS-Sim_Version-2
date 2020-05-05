

from PyQt5 import \
    QtWidgets  # Trying to import Qtwidgets from PySide2. For this we need both PySide2 and Qt designer app installed and configured
from app import Simulator
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import binascii
import socket
import struct
import sys
import time
import traceback
import os, re, threading
from Multi_Class import Msg_Header


class WorkerSignals( QObject ):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        `tuple` (exctype, value, traceback.format_exc() )

    result
        `object` data returned from processing, anything

    progress
        `int` indicating % progress

    '''
    finished = pyqtSignal()
    error = pyqtSignal( tuple )
    result = pyqtSignal( object )
    progress = pyqtSignal( int )


class Worker( QRunnable ):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super( Worker, self ).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        # self.kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them


        try:
            result = self.fn( *self.args, **self.kwargs )
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit( (exctype, value, traceback.format_exc()) )
        else:
            self.signals.result.emit( result )  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done
        
multicast_group = '226.10.0.1'
server_address = ('10.1.1.1', 10001)

# Create the socket
sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )

# Bind to the server address
sock.bind( server_address )

# Tell the operating system to add the socket to the multicast group
# on all interfaces.
group = socket.inet_aton( multicast_group )
mreq = struct.pack( '4sL', group, socket.INADDR_ANY )
sock.setsockopt( socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq )

# Health Message
ok = '0100'
nok = '0000'

global Sw_ascii, IFUC_1_hlt_bytes, IFUC_2_hlt_bytes, IFUC_1_slt_bytes, \
    IFUC_2_slt_bytes, IFUC_1_lnk_bytes, IFUC_2_lnk_bytes, IFUC_1_sw_bytes, IFUC_2_sw_bytes


class MyQtApp( Simulator.Ui_MainWindow,
               QtWidgets.QMainWindow ):  # Creating Class for the gui app as MyQtApp and adding cucs main window and qtwidget main window
    def __init__(
            self, *args, **kwargs):  # creating function for initiating the program. All actions will be triggered under this program
        super( MyQtApp, self ).__init__(*args, **kwargs)  # Initiating MyQtApp
        self.setupUi( self )  # Setting up Ui file
        self.setWindowTitle(
            "IFUC Health Message - Build Ver-0.2" )  # Setting up title and build number for Gui Title Window
        self.PB_Start.clicked.connect(self.multicast_start)
        # self.timer()
        self.threadpool = QThreadPool()
        print( "Multithreading with maximum %d threads" % self.threadpool.maxThreadCount() )


        print( '\nwaiting to receive message', file=sys.stderr )

    def multicast_recv(self):

        global IFUC_1_Slot, IFUC_2_Slot

        while True:

            data, address = sock.recvfrom( 1024 )

            # print('received %s bytes from %s' % (len(data), address), file=sys.stderr)
            # print(data, file=sys.stderr)

            hex_bytes = binascii.hexlify( data ).decode( 'utf-8' )
            IFUC_1_hlt_bytes = ""
            IFUC_2_hlt_bytes = ""
            IFUC_1_slt_bytes = ""   
            IFUC_2_slt_bytes = ""
            IFUC_1_lnk_bytes = ""
            IFUC_2_lnk_bytes = ""
            IFUC_1_sw_bytes = ""
            IFUC_2_sw_bytes = ""

            if hex_bytes[0:2] == Msg_Header.Msg_ID.IFUC1_ID and hex_bytes[4:8] == Msg_Header.Msg_Code.IFUC_STS:
                IFUC_1_hlt_bytes: str = hex_bytes
            elif hex_bytes[0:2] == Msg_Header.Msg_ID.IFUC2_ID and hex_bytes[4:8] == Msg_Header.Msg_Code.IFUC_STS:
                IFUC_2_hlt_bytes: str = hex_bytes
            elif hex_bytes[0:2] == Msg_Header.Msg_ID.IFUC1_ID and hex_bytes[4:8] == Msg_Header.Msg_Code.IFUC_SLT_STS:
                IFUC_1_slt_bytes: str = hex_bytes
            elif hex_bytes[0:2] == Msg_Header.Msg_ID.IFUC2_ID and hex_bytes[4:8] == Msg_Header.Msg_Code.IFUC_SLT_STS:
                IFUC_2_slt_bytes: str = hex_bytes
            elif hex_bytes[0:2] == Msg_Header.Msg_ID.IFUC1_ID and hex_bytes[4:8] == Msg_Header.Msg_Code.IFUC_LNK_STS:
                IFUC_1_lnk_bytes: str = hex_bytes
            elif hex_bytes[0:2] == Msg_Header.Msg_ID.IFUC2_ID and hex_bytes[4:8] == Msg_Header.Msg_Code.IFUC_LNK_STS:
                IFUC_2_lnk_bytes: str = hex_bytes
            elif hex_bytes[0:2] == Msg_Header.Msg_ID.IFUC1_ID and hex_bytes[4:8] == Msg_Header.Msg_Code.IFUC_SW:
                IFUC_1_sw_bytes: str = hex_bytes
            elif hex_bytes[0:2] == Msg_Header.Msg_ID.IFUC2_ID and hex_bytes[4:8] == Msg_Header.Msg_Code.IFUC_SW:
                IFUC_2_sw_bytes: str = hex_bytes

            # IFUC 1 & 2 Health and Mode status

            if len(IFUC_1_hlt_bytes) > 0:

                if hex_bytes[0:2] == Msg_Header.Msg_ID.IFUC1_ID and hex_bytes[16:20] == ok:
                    IFUC_1_Health: str = "Health OK"
                    #print( "IFUC 1 " + IFUC_1_Health )
                    self.IFUC_1_HLT.setText(IFUC_1_Health)

                elif hex_bytes[0:2] == Msg_Header.Msg_ID.IFUC1_ID and hex_bytes[16:20] == nok:
                    IFUC_1_Health = "Health Not OK"
                    #print( "IFUC 1 " + IFUC_1_Health )
                    self.IFUC_1_HLT.setText( IFUC_1_Health )

                else:
                    pass

            if len( IFUC_1_hlt_bytes ) > 0:

                if hex_bytes[0:2] == Msg_Header.Msg_ID.IFUC1_ID and hex_bytes[20:24] == ok:
                    IFUC_1_Mode: str = "Main"
                    #print( "IFUC 1 " + IFUC_1_Mode )
                    self.IFUC_1_MD.setText(IFUC_1_Mode)

                elif hex_bytes[0:2] == Msg_Header.Msg_ID.IFUC1_ID and hex_bytes[20:24] == nok:
                    IFUC_1_Mode: str = "Backup"
                    #print( "IFUC 1 " + IFUC_1_Mode )
                    self.IFUC_1_MD.setText(IFUC_1_Mode)

                else:
                    pass

            if len(IFUC_2_hlt_bytes) > 0:

                if hex_bytes[0:2] == Msg_Header.Msg_ID.IFUC2_ID and hex_bytes[16:20] == ok:
                    IFUC_2_Health: str = "Health OK"
                    #print( "IFUC 2 " + IFUC_2_Health )
                    self.IFUC_2_HLT.setText(IFUC_2_Health)

                elif hex_bytes[0:2] == Msg_Header.Msg_ID.IFUC2_ID and hex_bytes[16:20] == nok:
                    IFUC_2_Health: str = "Health Not OK"
                    #print( "IFUC 2 " + IFUC_2_Health )
                    self.IFUC_2_HLT.setText( IFUC_2_Health )

                else:
                    pass

            if len( IFUC_2_hlt_bytes ) > 0:

                if hex_bytes[0:2] == Msg_Header.Msg_ID.IFUC2_ID and hex_bytes[20:24] == ok:
                    IFUC_2_Mode: str = "Main"
                    #print( "IFUC 2 " + IFUC_2_Mode )
                    self.IFUC_1_MD_2.setText(IFUC_2_Mode)

                elif hex_bytes[0:2] == Msg_Header.Msg_ID.IFUC2_ID and hex_bytes[20:24] == nok:
                    IFUC_2_Mode: str = "Backup"
                    #print( "IFUC 2 " + IFUC_2_Mode )
                    self.IFUC_1_MD_2.setText( IFUC_2_Mode )

                else:
                    pass

            # IFUC Slot Status Program:

            param_data = [hex_bytes[16:20], hex_bytes[20:24], hex_bytes[24:28], hex_bytes[28:32],
                          hex_bytes[32:36], hex_bytes[36:40]]
            IFUC_1_Slot = []
            IFUC_2_Slot = []

            if len( IFUC_1_slt_bytes ) > 0:

                if hex_bytes[0:2] == Msg_Header.Msg_ID.IFUC1_ID and hex_bytes[4:8] == Msg_Header.Msg_Code.IFUC_SLT_STS:
                    counter = 1
                    for item in param_data:
                        if item == '0000':
                            slot_status = ["ON"]
                            IFUC_1_Slot += slot_status

                        else:
                            slot_status = ["OFF"]
                            IFUC_1_Slot += slot_status

                        counter += 1
                else:
                    pass

            if len( IFUC_2_slt_bytes ) > 0:

                if hex_bytes[0:2] == Msg_Header.Msg_ID.IFUC2_ID and hex_bytes[4:8] == Msg_Header.Msg_Code.IFUC_SLT_STS:
                    counter = 1
                    for item in param_data:
                        if item == '0000':
                            #slot_status = ["IFUC 2 Slot " + str( counter ) + " ON"]
                            slot_status = ["ON"]
                            IFUC_2_Slot += slot_status

                        else:
                            #slot_status = ["IFUC 2 Slot " + str( counter ) + " OFF"]
                            slot_status = ["OFF"]
                            IFUC_2_Slot += slot_status

                        counter += 1
                else:
                    pass

            if len( IFUC_1_Slot ) > 0:
                #print( IFUC_1_Slot )
                self.IFUC_1_S1.setText(IFUC_1_Slot[0])
                self.IFUC_1_S2.setText(IFUC_1_Slot[1])
                self.IFUC_1_S3.setText(IFUC_1_Slot[2])
                self.IFUC_1_S4.setText(IFUC_1_Slot[3])
                self.IFUC_1_S5.setText(IFUC_1_Slot[4])
                self.IFUC_1_S6.setText(IFUC_1_Slot[5])

            elif len( IFUC_2_Slot ) > 0:
                #print( IFUC_2_Slot )
                self.IFUC_2_S1.setText( IFUC_2_Slot[0] )
                self.IFUC_2_S2.setText( IFUC_2_Slot[1] )
                self.IFUC_2_S3.setText( IFUC_2_Slot[2] )
                self.IFUC_2_S4.setText( IFUC_2_Slot[3] )
                self.IFUC_2_S5.setText( IFUC_2_Slot[4] )
                self.IFUC_2_S6.setText( IFUC_2_Slot[5] )
            else:
                pass

            # IFUC Link Status Program:

            IFUC_1_Link = []
            IFUC_2_Link = []

            if len( IFUC_1_lnk_bytes ) > 0:

                if hex_bytes[0:2] == Msg_Header.Msg_ID.IFUC1_ID and hex_bytes[4:8] == Msg_Header.Msg_Code.IFUC_LNK_STS:
                    counter = 1
                    for item in param_data:
                        if item == '0100':
                            link_status = ["ON"]
                            IFUC_1_Link += link_status

                        else:
                            link_status = ["OFF"]
                            IFUC_1_Link += link_status

                        counter += 1

                else:
                    pass


            if len( IFUC_2_lnk_bytes ) > 0:

                if hex_bytes[0:2] == Msg_Header.Msg_ID.IFUC2_ID and hex_bytes[4:8] == Msg_Header.Msg_Code.IFUC_LNK_STS:
                    counter = 1
                    for item in param_data:
                        if item == '0100':
                            link_status = ["ON"]
                            IFUC_2_Link += link_status

                        else:
                            link_status = ["OFF"]
                            IFUC_2_Link += link_status

                        counter += 1

                else:
                    pass

            if len( IFUC_1_Link ) > 0:
                #print( IFUC_1_Link )
                self.IFUC_1_L1.setText(IFUC_1_Link[0])
                self.IFUC_1_L2.setText(IFUC_1_Link[1])
                self.IFUC_1_L3.setText(IFUC_1_Link[2])
                self.IFUC_1_L4.setText(IFUC_1_Link[3])
                self.IFUC_1_L5.setText(IFUC_1_Link[4])
                self.IFUC_1_L6.setText(IFUC_1_Link[5])

            elif len( IFUC_2_Link ) > 0:
                #print( IFUC_2_Link )
                self.IFUC_2_L1.setText( IFUC_2_Link[0] )
                self.IFUC_2_L2.setText( IFUC_2_Link[1] )
                self.IFUC_2_L3.setText( IFUC_2_Link[2] )
                self.IFUC_2_L4.setText( IFUC_2_Link[3] )
                self.IFUC_2_L5.setText( IFUC_2_Link[4] )
                self.IFUC_2_L6.setText( IFUC_2_Link[5] )
            else:
                pass

            # IFUC Software Status Program

            if len( IFUC_1_sw_bytes ) > 0:

                if hex_bytes[0:2] == Msg_Header.Msg_ID.IFUC1_ID and hex_bytes[4:8] == Msg_Header.Msg_Code.IFUC_SW:

                    Sw_data = hex_bytes[16:]
                    day = int( Sw_data[:2], 16 )
                    month = int( Sw_data[2:4], 16 )
                    year_cons = Sw_data[6:8] + Sw_data[4:6]
                    year = int( year_cons, 16 )
                    Sw_date = str( day + month + year )

                    SW_Ver = str( Sw_data[8:] )

                    Sw_ascii = ""

                    for i in range( 0, len( SW_Ver ), 2 ):
                        # extract two characters from hex string
                        part = SW_Ver[i: i + 2]

                        # change it into base 16 and
                        # typecast as the character
                        ch = chr( int( part, 16 ) )

                        # add this char to final ASCII string
                        Sw_ascii += ch

                    #print( "IFUC 1 Software Release Date is ", day, "-", month, "-", year, " and Version is ", Sw_ascii )
                    date_of_Rel = (str(day) + "-" + str(month) + "-" + str(year))
                    self.IFUC_1_DoR.setText(date_of_Rel)
                    self.IFUC_1_Sw.setText(Sw_ascii)

            if len( IFUC_2_sw_bytes ) > 0:

                if hex_bytes[0:2] == Msg_Header.Msg_ID.IFUC2_ID and hex_bytes[4:8] == Msg_Header.Msg_Code.IFUC_SW:

                    Sw_data = hex_bytes[16:]
                    day = int( Sw_data[:2], 16 )
                    month = int( Sw_data[2:4], 16 )
                    year_cons = Sw_data[6:8] + Sw_data[4:6]
                    year = int( year_cons, 16 )
                    Sw_date = str( day + month + year )

                    SW_Ver = str( Sw_data[8:] )

                    Sw_ascii = ""

                    for i in range( 0, len( SW_Ver ), 2 ):
                        # extract two characters from hex string
                        part = SW_Ver[i: i + 2]

                        # change it into base 16 and
                        # typecast as the character
                        ch = chr( int( part, 16 ) )

                        # add this char to final ASCII string
                        Sw_ascii += ch

                    #print( "IFUC 2 Software Release Date is ", day, "-", month, "-", year, " and Version is ", Sw_ascii )
                    date_of_Rel = (str( day ) + "-" + str( month ) + "-" + str( year ))
                    self.IFUC_2_DoR.setText( date_of_Rel )
                    self.IFUC_2_Sw.setText( Sw_ascii )

            if len(IFUC_1_hlt_bytes) < 0 or len(IFUC_1_hlt_bytes):
                gui_update = Worker(self.msg_check)
                self.threadpool.start(gui_update)
            # progress_callback.emit(True)
            pass

    def msg_check(self):
        """
        To Check and refresh GUI is no data received.
        """
        ifuc1hltdata = IFUC_1_hlt_bytes
        ifuc2hltdata = IFUC_2_hlt_bytes

        time.sleep(5)

        if not len( ifuc1hltdata ) >= 0:
            self.IFUC_1_HLT.clear()
            self.IFUC_1_MD.clear()
            self.IFUC_1_S1.clear()
            self.IFUC_1_S2.clear()
            self.IFUC_1_S3.clear()
            self.IFUC_1_S4.clear()
            self.IFUC_1_S5.clear()
            self.IFUC_1_S6.clear()
            self.IFUC_1_L1.clear()
            self.IFUC_1_L2.clear()
            self.IFUC_1_L3.clear()
            self.IFUC_1_L4.clear()
            self.IFUC_1_L5.clear()
            self.IFUC_1_L6.clear()
            self.IFUC_1_DoR.clear()
            self.IFUC_1_Sw.clear()

        if len(ifuc2hltdata) < 0:
            time.sleep(5)

        if len(ifuc2hltdata) < 0:
            self.IFUC_2_HLT.clear()
            self.IFUC_1_MD_2.clear()
            self.IFUC_2_S1.clear()
            self.IFUC_2_S2.clear()
            self.IFUC_2_S3.clear()
            self.IFUC_2_S4.clear()
            self.IFUC_2_S5.clear()
            self.IFUC_2_S6.clear()
            self.IFUC_2_L1.clear()
            self.IFUC_2_L2.clear()
            self.IFUC_2_L3.clear()
            self.IFUC_2_L4.clear()
            self.IFUC_2_L5.clear()
            self.IFUC_2_L6.clear()
            self.IFUC_2_DoR.clear()
            self.IFUC_2_Sw.clear()

    def multicast_start(self):
        worker = Worker(self.multicast_recv)
        self.threadpool.start(worker)

        #worker1 = Worker(self.msg_check)
        #self.threadpool.start(worker1)




if __name__ == '__main__':  # Required to start QtDesigner app to open up the designed GUI
    app = QtWidgets.QApplication( sys.argv )
    qt_app = MyQtApp()
    qt_app.show()
    app.exec_()
