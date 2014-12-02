#!/usr/bin/env python
##################################################
# Gnuradio Python Flow Graph
# Title: Top Block
# Generated: Tue Dec  2 16:35:21 2014
##################################################

from PyQt4 import Qt
from gnuradio import analog
from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import filter
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
        self._update_period_config = ConfigParser.ConfigParser()
        self._update_period_config.read("default")
        try: update_period = self._update_period_config.getfloat("main", "key")
        except: update_period = 0.001
        self.update_period = update_period
        self.sub_carrier_freq = sub_carrier_freq = 1000
        self.send_gain = send_gain = 0
        self.samp_rate = samp_rate = 20000
        self.rms_alpha = rms_alpha = 0.01
        self.recieve_gain = recieve_gain = 1
        self._fft_size_config = ConfigParser.ConfigParser()
        self._fft_size_config.read("default")
        try: fft_size = self._fft_size_config.getfloat("main", "key")
        except: fft_size = 8192
        self.fft_size = fft_size
        self.data_rate = data_rate = 0.1
        self._carrier_freq_config = ConfigParser.ConfigParser()
        self._carrier_freq_config.read("default")
        try: carrier_freq = self._carrier_freq_config.getfloat("main", "key")
        except: carrier_freq = 916000000
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
        self._rms_alpha_tool_bar = Qt.QToolBar(self)
        self._rms_alpha_tool_bar.addWidget(Qt.QLabel("rms_alpha"+": "))
        self._rms_alpha_line_edit = Qt.QLineEdit(str(self.rms_alpha))
        self._rms_alpha_tool_bar.addWidget(self._rms_alpha_line_edit)
        self._rms_alpha_line_edit.returnPressed.connect(
        	lambda: self.set_rms_alpha(eng_notation.str_to_num(self._rms_alpha_line_edit.text().toAscii())))
        self.tabs_layout_1.addWidget(self._rms_alpha_tool_bar)
        self.qtgui_waterfall_sink_x_1 = qtgui.waterfall_sink_c(
        	8096, #size
        	firdes.WIN_BLACKMAN_hARRIS, #wintype
        	carrier_freq, #fc
        	samp_rate, #bw
        	"QT GUI Plot", #name
                1 #number of inputs
        )
        self.qtgui_waterfall_sink_x_1.set_update_time(0.01)
        self._qtgui_waterfall_sink_x_1_win = sip.wrapinstance(self.qtgui_waterfall_sink_x_1.pyqwidget(), Qt.QWidget)
        self.tabs_layout_0.addWidget(self._qtgui_waterfall_sink_x_1_win)
        self.qtgui_time_sink_x_0 = qtgui.time_sink_f(
        	302400, #size
        	samp_rate, #samp_rate
        	"QT GUI Plot", #name
        	3 #number of inputs
        )
        self.qtgui_time_sink_x_0.set_update_time(0.10)
        self.qtgui_time_sink_x_0.set_y_axis(-1, 1)
        self.qtgui_time_sink_x_0.enable_tags(-1, True)
        self.qtgui_time_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self._qtgui_time_sink_x_0_win = sip.wrapinstance(self.qtgui_time_sink_x_0.pyqwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_time_sink_x_0_win)
        self.qtgui_freq_sink_x_0 = qtgui.freq_sink_c(
        	1024, #size
        	firdes.WIN_BLACKMAN_hARRIS, #wintype
        	carrier_freq, #fc
        	samp_rate, #bw
        	"QT GUI Plot", #name
        	3 #number of inputs
        )
        self.qtgui_freq_sink_x_0.set_update_time(0.10)
        self.qtgui_freq_sink_x_0.set_y_axis(-140, 10)
        self._qtgui_freq_sink_x_0_win = sip.wrapinstance(self.qtgui_freq_sink_x_0.pyqwidget(), Qt.QWidget)
        self.tabs_layout_0.addWidget(self._qtgui_freq_sink_x_0_win)
        self._data_rate_tool_bar = Qt.QToolBar(self)
        self._data_rate_tool_bar.addWidget(Qt.QLabel("Data Rate (Hz)"+": "))
        self._data_rate_line_edit = Qt.QLineEdit(str(self.data_rate))
        self._data_rate_tool_bar.addWidget(self._data_rate_line_edit)
        self._data_rate_line_edit.returnPressed.connect(
        	lambda: self.set_data_rate(eng_notation.str_to_num(self._data_rate_line_edit.text().toAscii())))
        self.tabs_layout_1.addWidget(self._data_rate_tool_bar)
        self.blocks_sub_xx_0 = blocks.sub_ff(1)
        self.blocks_rms_xx_1 = blocks.rms_cf(0.1)
        self.blocks_rms_xx_0 = blocks.rms_cf(0.1)
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_vff((-500, ))
        self.band_pass_filter_0_0 = filter.fir_filter_ccf(1, firdes.band_pass(
        	1, samp_rate, 1175, 1225, 25, firdes.WIN_HAMMING, 6.76))
        self.band_pass_filter_0 = filter.fir_filter_ccf(1, firdes.band_pass(
        	1, samp_rate, 475, 525, 25, firdes.WIN_HAMMING, 6.76))
        self.analog_sig_source_x_1 = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, sub_carrier_freq, 1, 0)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.uhd_usrp_source_0_0, 0), (self.band_pass_filter_0, 0))
        self.connect((self.analog_sig_source_x_1, 0), (self.uhd_usrp_sink_0, 0))
        self.connect((self.uhd_usrp_source_0_0, 0), (self.band_pass_filter_0_0, 0))
        self.connect((self.uhd_usrp_source_0_0, 0), (self.qtgui_freq_sink_x_0, 2))
        self.connect((self.band_pass_filter_0, 0), (self.blocks_rms_xx_0, 0))
        self.connect((self.band_pass_filter_0_0, 0), (self.blocks_rms_xx_1, 0))
        self.connect((self.blocks_rms_xx_1, 0), (self.qtgui_time_sink_x_0, 0))
        self.connect((self.blocks_rms_xx_0, 0), (self.qtgui_time_sink_x_0, 1))
        self.connect((self.blocks_rms_xx_1, 0), (self.blocks_sub_xx_0, 0))
        self.connect((self.blocks_rms_xx_0, 0), (self.blocks_sub_xx_0, 1))
        self.connect((self.band_pass_filter_0, 0), (self.qtgui_freq_sink_x_0, 1))
        self.connect((self.band_pass_filter_0_0, 0), (self.qtgui_freq_sink_x_0, 0))
        self.connect((self.blocks_sub_xx_0, 0), (self.blocks_multiply_const_vxx_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.qtgui_time_sink_x_0, 2))
        self.connect((self.uhd_usrp_source_0_0, 0), (self.qtgui_waterfall_sink_x_1, 0))


# QT sink close method reimplementation
    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "top_block")
        self.settings.setValue("geometry", self.saveGeometry())
        event.accept()

    def get_update_period(self):
        return self.update_period

    def set_update_period(self, update_period):
        self.update_period = update_period

    def get_sub_carrier_freq(self):
        return self.sub_carrier_freq

    def set_sub_carrier_freq(self, sub_carrier_freq):
        self.sub_carrier_freq = sub_carrier_freq
        self._sub_carrier_freq_counter.setValue(self.sub_carrier_freq)
        self._sub_carrier_freq_slider.setValue(self.sub_carrier_freq)
        self.analog_sig_source_x_1.set_frequency(self.sub_carrier_freq)

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
        self.analog_sig_source_x_1.set_sampling_freq(self.samp_rate)
        self.band_pass_filter_0.set_taps(firdes.band_pass(1, self.samp_rate, 475, 525, 25, firdes.WIN_HAMMING, 6.76))
        self.band_pass_filter_0_0.set_taps(firdes.band_pass(1, self.samp_rate, 1175, 1225, 25, firdes.WIN_HAMMING, 6.76))
        self.qtgui_freq_sink_x_0.set_frequency_range(self.carrier_freq, self.samp_rate)
        self.uhd_usrp_source_0_0.set_samp_rate(self.samp_rate)
        self.qtgui_waterfall_sink_x_1.set_frequency_range(self.carrier_freq, self.samp_rate)
        self.qtgui_time_sink_x_0.set_samp_rate(self.samp_rate)

    def get_rms_alpha(self):
        return self.rms_alpha

    def set_rms_alpha(self, rms_alpha):
        self.rms_alpha = rms_alpha
        self._rms_alpha_line_edit.setText(eng_notation.num_to_str(self.rms_alpha))

    def get_recieve_gain(self):
        return self.recieve_gain

    def set_recieve_gain(self, recieve_gain):
        self.recieve_gain = recieve_gain
        self._recieve_gain_counter.setValue(self.recieve_gain)
        self._recieve_gain_slider.setValue(self.recieve_gain)
        self.uhd_usrp_source_0_0.set_gain(self.recieve_gain, 0)

    def get_fft_size(self):
        return self.fft_size

    def set_fft_size(self, fft_size):
        self.fft_size = fft_size

    def get_data_rate(self):
        return self.data_rate

    def set_data_rate(self, data_rate):
        self.data_rate = data_rate
        self._data_rate_line_edit.setText(eng_notation.num_to_str(self.data_rate))

    def get_carrier_freq(self):
        return self.carrier_freq

    def set_carrier_freq(self, carrier_freq):
        self.carrier_freq = carrier_freq
        self.uhd_usrp_sink_0.set_center_freq(self.carrier_freq, 0)
        self.qtgui_freq_sink_x_0.set_frequency_range(self.carrier_freq, self.samp_rate)
        self.uhd_usrp_source_0_0.set_center_freq(self.carrier_freq, 0)
        self.qtgui_waterfall_sink_x_1.set_frequency_range(self.carrier_freq, self.samp_rate)

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

