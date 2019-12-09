import pyvisa

class Chroma63800:
    def __init__(self, device, peak_current=10):
        self.rm = pyvisa.ResourceManager('@py')
        self.inst = self.rm.open_resource(device, write_termination='\n', read_termination='\n', baud_rate=57600)
        idn = self.inst.query('*IDN?')
        if 'Chroma' not in idn and '63802' not in idn:
            raise ValueError('You did not select a Chroma Load Emulator');
        self.set_ipmax(peak_current)

    def set_mode(self, mode):
        if mode == 'power':
            self.inst.write(':LOAD:MODE POW')
        elif mode == 'current':
            self.inst.write(':LOAD:MODE CURR')
    def set_ipmax(self, ipmax):
        self.inst.write(':LOAD:CURR:PEAK:MAX ' + str(ipmax))
    def set_cfpf_mode(self, mode):
        if mode == 'cf':
            self.inst.write(':SYST:SET:CFPF:MODE CF')
        elif mode == 'pf':
            self.inst.write(':SYST:SET:CFPF:MODE PF')
        elif mode == 'both':
            self.inst.write(':SYST:SET:CFPF:MODE BOTH')
    def set_current(self, current):
        self.set_mode('current')
        self.inst.write(':LOAD:CURR ' + str(current))
    def set_power(self, power):
        self.set_mode('power')
        self.inst.write(':LOAD:POW ' + str(power))
    def set_pf(self, pf):
        self.set_cfpf_mode('pf')
        self.inst.write(':PFAC ' + str(pf))

    def load_on(self):
        self.inst.write(':LOAD 1')
    def load_off(self):
        self.inst.write(':LOAD 0')

    def measure_voltage(self):
        return float(self.inst.query(':MEAS:VOLT?'))
    def measure_current(self):
        return float(self.inst.query(':MEAS:CURR?'))
    def measure_apparent_power(self):
        return float(self.inst.query(':MEAS:POW:APP?'))
    def measure_reactive_power(self):
        return float(self.inst.query(':MEAS:POW:REAC?'))
    def measure_real_power(self):
        return float(self.inst.query(':MEAS:POW:REAL?'))
    def measure_pf(self):
        return float(self.inst.query(':MEAS:POW:PFAC?'))
    def measure_all(self):
        return (self.measure_voltage(), self.measure_current(), self.measure_apparent_power(), self.measure_real_power(), self.measure_reactive_power(), self.measure_pf())

