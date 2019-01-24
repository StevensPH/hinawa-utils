# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from re import match

import gi
gi.require_version('Hinawa', '2.0')
from gi.repository import Hinawa

from hinawa_utils.dg00x.config_rom_parser import Dg00xConfigRomParser

__all__ = ['Dg00xUnit']


class Dg00xUnit(Hinawa.SndDg00x):
    __BASE_ADDR = 0xffffe0000000

    SUPPORTED_SAMPLING_RATES = (44100, 48000, 88200, 96000)
    SUPPORTED_CLOCK_SOURCES = ('Internal', 'S/PDIF', 'ADAT', 'Word-clock')
    SUPPORTED_OPTICAL_INTERFACES = ('ADAT', 'S/PDIF')

    def __init__(self, path):
        if match('/dev/snd/hwC[0-9]*D0', path):
            super().__init__()
            self.open(path)
            if self.get_property('type') != 5:
                raise ValueError('The character device is not for Dg00x unit')
            self.listen()
        elif match('/dev/fw[0-9]*', path):
            # Just using parent class.
            super(Hinawa.FwUnit, self).__init__()
            Hinawa.FwUnit.open(self, path)
            Hinawa.FwUnit.listen(self)
        else:
            raise ValueError('Invalid argument for character device')

        parser = Dg00xConfigRomParser()
        info = parser.parse_rom(self.get_config_rom())
        self._model_name = info['model-name']

    def _read_transaction(self, offset, size):
        req = Hinawa.FwReq()
        addr = self.__BASE_ADDR + offset
        return req.read(self, addr, size)

    def _write_transaction(self, offset, size):
        req = Hinawa.FwReq()
        addr = self.__BASE_ADDR + offset
        return req.write(self, addr, size)

    def set_clock_source(self, source):
        if source not in self.SUPPORTED_CLOCK_SOURCES:
            raise ValueError('Invalid argument for clock source.')
        data = bytearray(4)
        data[3] = self.SUPPORTED_CLOCK_SOURCES.index(source)
        self._write_transaction(0x0118, data)

    def get_clock_source(self):
        data = self._read_transaction(0x0118, 4)
        if data[3] >= len(self.SUPPORTED_CLOCK_SOURCES):
            raise OSError('Unexpected value for clock source.')
        return self.SUPPORTED_CLOCK_SOURCES[data[3]]

    def set_local_sampling_rate(self, rate):
        if rate not in self.SUPPORTED_SAMPLING_RATES:
            raise ValueError('Invalid argument for local sampling rate.')
        data = bytearray(4)
        data[3] = self.SUPPORTED_SAMPLING_RATES.index(rate)
        self._write_transaction(0x0110, data)

    def get_local_sampling_rate(self):
        data = self._read_transaction(0x0110, 4)
        if data[3] >= len(self.SUPPORTED_SAMPLING_RATES):
            raise OSError('Unexpected value for local sampling rate.')
        return self.SUPPORTED_SAMPLING_RATES[data[3]]

    def get_external_sampling_rate(self):
        data = self._read_transaction(0x0114, 4)
        if data[3] >= len(self.SUPPORTED_SAMPLING_RATES):
            raise OSError('Unexpected value for external sampling rate.')
        return self.SUPPORTED_SAMPLING_RATES[data[3]]

    def check_external_input(self):
        data = self._read_transaction(0x012c, 4)
        return data[3] > 0

    def set_opt_iface(self, mode):
        if mode not in self.SUPPORTED_OPTICAL_INTERFACES:
            raise ValueError('Invalid argument for optical interface mode.')
        data = bytearray(4)
        data[3] = self.SUPPORTED_OPTICAL_INTERFACES.index(mode)
        self._write_transaction(0x011c, data)

    def get_opt_iface(self):
        data = self._read_transaction(0x011c, 4)
        if data[3] >= len(self.SUPPORTED_OPTICAL_INTERFACES):
            raise ValueError('Unexpected value for optical interface mode.')
        return self.SUPPORTED_OPTICAL_INTERFACES[data[3]]

    def set_mixer_mode(self, mode):
        if mode > 0:
            mode = 1
        else:
            mode = 0
        data = bytearray(4)
        data[3] = mode
        self._write_transaction(0x0124, data)

    def get_mixer_mode(self):
        data = self._read_transaction(0x0124, 4)
        return (data[3] > 0)
