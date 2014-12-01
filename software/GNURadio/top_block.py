#!/usr/bin/env python
##################################################
# Gnuradio Python Flow Graph
# Title: Top Block
# Generated: Sun Nov 30 15:45:48 2014
##################################################

from PyQt4 import Qt
from gnuradio import analog
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import qtgui
from gnuradio import uhd
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser
import ConfigParser
import PyQt4.Qwt5 as Qwt
import sip
import sys
import time

class top_block(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Top Block")
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Top Block")
        try:
             self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except:
             pass
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "top_block")
        self.restoreGeometry(self.settings.value("geometry").toByteArray())


        ##################################################
        # Variables
        ##################################################
        self.sub_carrier_freq = sub_carrier_freq = 1000
        self.send_gain = send_gain = 40
        self.samp_rate = samp_rate = 10000
        self.recieve_gain = recieve_gain = 1
        self._carrier_freq_config = ConfigParser.ConfigParser()
        self._carrier_freq_config.read("default")
        try: carrier_freq = self._carrier_freq_config.getfloat("main", "key")
        except: carrier_freq = 915000000
        self.carrier_freq = carrier_freq
        self._USRP_IP_config = ConfigParser.ConfigParser()
        self._USRP_IP_config.read("default")
        try: USRP_IP = self._USRP_IP_config.get("main", "key")
        except: USRP_IP = "addr=192.168.10.14"
        self.USRP_IP = USRP_IP

        ##################################################
        # Blocks
        ##################################################
        self.tabs = Qt.QTabWidget()
        self.tabs_widget_0 = Qt.QWidget()
        self.tabs_layout_0 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.tabs_widget_0)
        self.tabs_grid_layout_0 = Qt.QGridLayout()
        self.tabs_layout_0.addLayout(self.tabs_grid_layout_0)
        self.tabs.addTab(self.tabs_widget_0, "Plots")
        self.tabs_widget_1 = Qt.QWidget()
        self.tabs_layout_1 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.tabs_widget_1)
        self.tabs_grid_layout_1 = Qt.QGridLayout()
        self.tabs_layout_1.addLayout(self.tabs_grid_layout_1)
        self.tabs.addTab(self.tabs_widget_1, "Settings")
        self.top_layout.addWidget(self.tabs)
        self._sub_carrier_freq_layout = Qt.QVBoxLayout()
        self._sub_carrier_freq_tool_bar = Qt.QToolBar(self)
        self._sub_carrier_freq_layout.addWidget(self._sub_carrier_freq_tool_bar)
        self._sub_carrier_freq_tool_bar.addWidget(Qt.QLabel("Sub-Carrier Freq (Hz)"+": "))
        self._sub_carrier_freq_counter = Qwt.QwtCounter()
        self._sub_carrier_freq_counter.setRange(0, 50000, 1000)
        self._sub_carrier_freq_counter.setNumButtons(2)
        self._sub_carrier_freq_counter.setValue(self.sub_carrier_freq)
        self._sub_carrier_freq_tool_bar.addWidget(self._sub_carrier_freq_counter)
        self._sub_carrier_freq_counter.valueChanged.connect(self.set_sub_carrier_freq)
        self._sub_carrier_freq_slider = Qwt.QwtSlider(None, Qt.Qt.Horizontal, Qwt.QwtSlider.BottomScale, Qwt.QwtSlider.BgSlot)
        self._sub_carrier_freq_slider.setRange(0, 50000, 1000)
        self._sub_carrier_freq_slider.setValue(self.sub_carrier_freq)
        self._sub_carrier_freq_slider.setMinimumWidth(200)
        self._sub_carrier_freq_slider.valueChanged.connect(self.set_sub_carrier_freq)
        self._sub_carrier_freq_layout.addWidget(self._sub_carrier_freq_slider)
        self.tabs_layout_1.addLayout(self._sub_carrier_freq_layout)
        self._send_gain_layout = Qt.QVBoxLayout()
        self._send_gain_tool_bar = Qt.QToolBar(self)
        self._send_gain_layout.addWidget(self._send_gain_tool_bar)
        self._send_gain_tool_bar.addWidget(Qt.QLabel("Send Gain (dB)"+": "))
        self._send_gain_counter = Qwt.QwtCounter()
        self._send_gain_counter.setRange(0, 100, 1)
        self._send_gain_counter.setNumButtons(2)
        self._send_gain_counter.setValue(self.send_gain)
        self._send_gain_tool_bar.addWidget(self._send_gain_counter)
        self._send_gain_counter.valueChanged.connect(self.set_send_gain)
        self._send_gain_slider = Qwt.QwtSlider(None, Qt.Qt.Horizontal, Qwt.QwtSlider.BottomScale, Qwt.QwtSlider.BgSlot)
        self._send_gain_slider.setRange(0, 100, 1)
        self._send_gain_slider.setValue(self.send_gain)
        self._send_gain_slider.setMinimumWidth(200)
        self._send_gain_slider.valueChanged.connect(self.set_send_gain)
        self._send_gain_layout.addWidget(self._send_gain_slider)
        self.tabs_layout_1.addLayout(self._send_gain_layout)
        self._recieve_gain_layout = Qt.QVBoxLayout()
        self._recieve_gain_tool_bar = Qt.QToolBar(self)
        self._recieve_gain_layout.addWidget(self._recieve_gain_tool_bar)
        self._recieve_gain_tool_bar.addWidget(Qt.QLabel("Recieve Gain (dB)"+": "))
        self._recieve_gain_counter = Qwt.QwtCounter()
        self._recieve_gain_counter.setRange(0, 100, 1)
        self._recieve_gain_counter.setNumButtons(2)
        self._recieve_gain_counter.setValue(self.recieve_gain)
        self._recieve_gain_tool_bar.addWidget(self._recieve_gain_counter)
        self._recieve_gain_counter.valueChanged.connect(self.set_recieve_gain)
        self._recieve_gain_slider = Qwt.QwtSlider(None, Qt.Qt.Horizontal, Qwt.QwtSlider.BottomScale, Qwt.QwtSlider.BgSlot)
        self._recieve_gain_slider.setRange(0, 100, 1)
        self._recieve_gain_slider.setValue(self.recieve_gain)
        self._recieve_gain_slider.setMinimumWidth(200)
        self._recieve_gain_slider.valueChanged.connect(self.set_recieve_gain)
        self._recieve_gain_layout.addWidget(self._recieve_gain_slider)
        self.tabs_layout_1.addLayout(self._recieve_gain_layout)
        self.uhd_usrp_source_0_0 = uhd.usrp_source(
        	device_addr=USRP_IP,
        	stream_args=uhd.stream_args(
        		cpu_format="fc32",
        		channels=range(1),
        	),
        )
        self.uhd_usrp_source_0_0.set_samp_rate(samp_rate)
        self.uhd_usrp_source_0_0.set_center_freq(carrier_freq, 0)
        self.uhd_usrp_source_0_0.set_gain(recieve_gain, 0)
        self.uhd_usrp_sink_0 = uhd.usrp_sink(
        	device_addr=USRP_IP,
        	stream_args=uhd.stream_args(
        		cpu_format="fc32",
        		channels=range(1),
        	),
        )
        self.uhd_usrp_sink_0.set_samp_rate(samp_rate)
        self.uhd_usrp_sink_0.set_center_freq(carrier_freq, 0)
        self.uhd_usrp_sink_0.set_gain(send_gain, 0)
        self.uhd_usrp_sink_0.set_bandwidth(samp_rate, 0)
        self.qtgui_const_sink_x_0 = qtgui.const_sink_c(
        	1024, #size
        	"QT GUI Plot", #name
        	1 #number of inputs
        )
        self.qtgui_const_sink_x_0.set_update_time(0.10)
        self.qtgui_const_sink_x_0.set_y_axis(-2, 2)
        self.qtgui_const_sink_x_0.set_x_axis(-2, 2)
        self._qtgui_const_sink_x_0_win = sip.wrapinstance(self.qtgui_const_sink_x_0.pyqwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_const_sink_x_0_win)
        self.analog_sig_source_x_0 = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, sub_carrier_freq, 1, 0)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_sig_source_x_0, 0), (self.uhd_usrp_sink_0, 0))
        self.connect((self.uhd_usrp_source_0_0, 0), (self.qtgui_const_sink_x_0, 0))


# QT sink close method reimplementation
    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "top_block")
        self.settings.setValue("geometry", self.saveGeometry())
        event.accept()

    def get_sub_carrier_freq(self):
        return self.sub_carrier_freq

    def set_sub_carrier_freq(self, sub_carrier_freq):
        self.sub_carrier_freq = sub_carrier_freq
        self._sub_carrier_freq_counter.setValue(self.sub_carrier_freq)
        self._sub_carrier_freq_slider.setValue(self.sub_carrier_freq)
        self.analog_sig_source_x_0.set_frequency(self.sub_carrier_freq)

    def get_send_gain(self):
        return self.send_gain

    def set_send_gain(self, send_gain):
        self.send_gain = send_gain
        self._send_gain_counter.setValue(self.send_gain)
        self._send_gain_slider.setValue(self.send_gain)
        self.uhd_usrp_sink_0.set_gain(self.send_gain, 0)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.uhd_usrp_sink_0.set_samp_rate(self.samp_rate)
        self.uhd_usrp_sink_0.set_bandwidth(self.samp_rate, 0)
        self.analog_sig_source_x_0.set_sampling_freq(self.samp_rate)
        self.uhd_usrp_source_0_0.set_samp_rate(self.samp_rate)

    def get_recieve_gain(self):
        return self.recieve_gain

    def set_recieve_gain(self, recieve_gain):
        self.recieve_gain = recieve_gain
        self._recieve_gain_counter.setValue(self.recieve_gain)
        self._recieve_gain_slider.setValue(self.recieve_gain)
        self.uhd_usrp_source_0_0.set_gain(self.recieve_gain, 0)

    def get_carrier_freq(self):
        return self.carrier_freq

    def set_carrier_freq(self, carrier_freq):
        self.carrier_freq = carrier_freq
        self.uhd_usrp_sink_0.set_center_freq(self.carrier_freq, 0)
        self.uhd_usrp_source_0_0.set_center_freq(self.carrier_freq, 0)

    def get_USRP_IP(self):
        return self.USRP_IP

    def set_USRP_IP(self, USRP_IP):
        self.USRP_IP = USRP_IP

if __name__ == '__main__':
    import ctypes
    import os
    if os.name == 'posix':
        try:
            x11 = ctypes.cdll.LoadLibrary('libX11.so')
            x11.XInitThreads()
        except:
            print "Warning: failed to XInitThreads()"
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    (options, args) = parser.parse_args()
    qapp = Qt.QApplication(sys.argv)
    tb = top_block()
    tb.start()
    tb.show()
    def quitting():
        tb.stop()
        tb.wait()
    qapp.connect(qapp, Qt.SIGNAL("aboutToQuit()"), quitting)
    qapp.exec_()
    tb = None #to clean up Qt widgets

