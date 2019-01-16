# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2019 Takashi Sakamoto

from enum import Enum
from math import log10, pow

from hinawa_utils.fireface.ff_protocol_abstract import FFProtocolAbstract

__all__ = ['FFProtocolLatter']


class ClkLabels(Enum):
    INTL = 'Internal'
    SPDIF = 'S/PDIF'
    ADAT = 'ADAT'
    WDCLK = 'Word-clock'


class OptionReg():
    __MULTIPLE_OPTION_MASKS = {
        'sample-rate': {
            '32000':            0x00000000,
            '44100':            0x00000002,
            '48000':            0x00000004,
            '64000':            0x00000008,
            '88200':            0x0000000a,
            '96000':            0x0000000c,
            '128000':           0x00000010,
            '176400':           0x00000012,
            '192000':           0x00000014,
        },
        'primary-clk-src': {
            ClkLabels.INTL.value:   0x00000000,
            ClkLabels.SPDIF.value:  0x00000400,
            ClkLabels.ADAT.value:   0x00000800,
            ClkLabels.WDCLK.value:  0x00000c00,
        },
        'spdif-out': {
            'consumer':         0x00000000,
            'professional':     0x00000020,
        },
        'optical-out': {
            'ADAT':             0x00000000,
            'S/PDIF':           0x00000100,
        },
        'midi-low-addr': {
            '0x00000000':       0x00002000,
            '0x00000080':       0x00004000,
            '0x00000100':       0x00008000,
            '0x00000180':       0x00010000,
        },
    }

    __BOOLEAN_OPTION_MASKS = {
        'dsp': {
            'eq+dyn':           0x00000040,
        },
        'wdclk-in': {
            'termination':      0x00000008,
        },
        'wdclk-out': {
            'single-speed':     0x00000010,
        },
    }

    # Helper functions for multiple value options.
    @classmethod
    def get_multiple_option_labels(cls) -> list:
        return list(cls.__MULTIPLE_OPTION_MASKS.keys())

    @classmethod
    def get_multiple_option_value_labels(cls, target: str) -> list:
        if target not in cls.__MULTIPLE_OPTION_MASKS:
            raise ValueError('Invalid argument for multi option.')
        return list(cls.__MULTIPLE_OPTION_MASKS[target].keys())

    @classmethod
    def build_multiple_option(cls, frame: int, target: str, val: str):
        if target not in cls.__MULTIPLE_OPTION_MASKS:
            raise ValueError('Invalid argument for multi option.')
        if val not in cls.__MULTIPLE_OPTION_MASKS[target]:
            raise ValueError('Invalid argument for value of multi option.')

        elems = cls.__MULTIPLE_OPTION_MASKS[target]
        for name, flag in elems.items():
            frame &= ~flag
        frame |= elems[val]

        return frame

    @classmethod
    def parse_multiple_option(cls, frame: int, target: str):
        if target not in cls.__MULTIPLE_OPTION_MASKS:
            raise ValueError('Invalid argument for multi option.')

        elems = cls.__MULTIPLE_OPTION_MASKS[target]
        mask = 0x00
        for name, flag in elems.items():
            mask |= flag

        for val, flag in elems.items():
            if frame & mask == flag:
                return val

        raise OSError('Unexpected state of bit flags.')

    # Helper functions to handle boolen options.
    @classmethod
    def get_boolean_option_labels(cls) -> list:
        return list(cls.__BOOLEAN_OPTION_MASKS.keys())

    @classmethod
    def get_boolean_option_item_labels(cls, target: str):
        if target not in cls.__BOOLEAN_OPTION_MASKS:
            raise ValueError('Invalid argument for bool option.')
        return list(cls.__BOOLEAN_OPTION_MASKS[target].keys())

    @classmethod
    def build_boolean_option(cls, frame: int, target: str, item: str,
                             enable: bool):
        if target not in cls.__BOOLEAN_OPTION_MASKS:
            raise ValueError('Invalid argument for bool option.')
        if item not in cls.__BOOLEAN_OPTION_MASKS[target]:
            raise ValueError('Invalid argument for item of bool option.')

        mask = cls.__BOOLEAN_OPTION_MASKS[target][item]
        frame &= ~mask
        if enable:
            frame |= mask

        return frame

    @classmethod
    def parse_boolean_option(cls, frame: int, target: str, item: str):
        if target not in cls.__BOOLEAN_OPTION_MASKS:
            raise ValueError('Invalid argument for bool option.')
        if item not in cls.__BOOLEAN_OPTION_MASKS[target]:
            raise ValueError('Invalid argument for item of bool option.')

        mask = cls.__BOOLEAN_OPTION_MASKS[target][item]

        return bool(frame & mask)


class StatusReg():
    __BOOLEAN_STATUS_MASKS = {
        'coaxial-rate': {
            '32000':            0x00000000,
            '44100':            0x00001000,
            '48000':            0x00002000,
            '64000':            0x00004000,
            '88200':            0x00005000,
            '96000':            0x00006000,
            '128000':           0x00008000,
            '176400':           0x00009000,
            '192000':           0x0000a000,
        },
        'referred-clock': {
            ClkLabels.ADAT.value:   0x00000200,
            ClkLabels.SPDIF.value:  0x00000400,
            ClkLabels.WDCLK.value:  0x00000600,
            ClkLabels.INTL.value:   0x00000e00,
        },
        'optical-in': {
            'S/PDIF':           0x00000000,
            'ADAT':             0x00000100,
        },
        'word-clock-rate': {
            '32000':            0x00000000,
            '44100':            0x00100000,
            '48000':            0x00200000,
            '64000':            0x00400000,
            '88200':            0x00500000,
            '96000':            0x00600000,
            '128000':           0x00800000,
            '176400':           0x00900000,
            '192000':           0x00a00000,
        },
        'optical-rate': {
            '32000':            0x00000000,
            '44100':            0x00010000,
            '48000':            0x00020000,
            '64000':            0x00040000,
            '88200':            0x00050000,
            '96000':            0x00060000,
            '128000':           0x00080000,
            '176400':           0x00090000,
            '192000':           0x000a0000,
        },
        'referred-rate': {
            '32000':            0x00000000,
            '44100':            0x01000000,
            '48000':            0x02000000,
            '64000':            0x04000000,
            '88200':            0x05000000,
            '96000':            0x06000000,
            '128000':           0x08000000,
            '176400':           0x09000000,
            '192000':           0x0a000000,
        },
    }

    __MULTIPLE_STATUS_MASKS = {
        'synchronized': {
            ClkLabels.SPDIF.value:  0x00000010,
            ClkLabels.ADAT.value:   0x00000020,
            ClkLabels.WDCLK.value:  0x00000040,
        },
        'locked': {
            ClkLabels.SPDIF.value:  0x00000001,
            ClkLabels.ADAT.value:   0x00000002,
            ClkLabels.WDCLK.value:  0x00000004,
        },
    }

    @classmethod
    def parse(cls, frame):
        status = {}

        for target, elems in cls.__BOOLEAN_STATUS_MASKS.items():
            mask = 0x00
            for name, flag in elems.items():
                mask |= flag

            for name, flag in elems.items():
                if frame & mask == flag:
                    status[target] = name
                    break

        for target, elems in cls.__MULTIPLE_STATUS_MASKS.items():
            status[target] = {}
            for name, flag in elems.items():
                status[target][name] = bool(frame & flag == flag)

        return status


class MixerReg():
    @classmethod
    def __generate_labels(cls, spec, category):
        labels = []
        for i in range(spec[category]):
            labels.append('{0}-{1}'.format(category, i + 1))
        return labels

    @classmethod
    def get_mixer_labels(cls, spec: dict):
        labels = cls.__generate_labels(spec, 'analog')
        labels += cls.__generate_labels(spec, 'spdif')
        labels += cls.__generate_labels(spec, 'adat')
        return labels

    @classmethod
    def get_mixer_src_labels(cls, spec: dict):
        labels = cls.__generate_labels(spec, 'analog')
        labels += cls.__generate_labels(spec, 'spdif')
        labels += cls.__generate_labels(spec, 'adat')
        labels += cls.__generate_labels(spec, 'stream')
        return labels

    @classmethod
    def calculate_src_offset(cls, spec: dict, dst: str, src: str):
        """
        Register layout.
             =+=========+=
              | inputs  | <= avail
        dst-0 +---------+
              | streams | <= avail
             =+=========+=
              | inputs  |
        dst-1 +---------+
              | streams |
             =+=========+=
        ...
             =+=========+=
              | inputs  |
        dst-n +---------+
              | streams |
             =+=========+=
        """

        dsts = cls.get_mixer_labels(spec)
        srcs = cls.get_mixer_src_labels(spec)
        if dst not in dsts:
            raise ValueError('Invalid argument for destination of mixer.')
        if src not in srcs:
            raise ValueError('Invalid argument for source of mixer.')

        offset = dsts.index(dst) * spec['avail'] * 2 * 4

        if src.find('stream-') == 0:
            offset += spec['avail'] * 4
            srcs = cls.__generate_labels(spec, 'stream')

        return offset + srcs.index(src) * 4


class OutReg():
    @classmethod
    def get_out_labels(cls, spec: dict):
        labels = []
        for i in range(spec['analog']):
            labels.append('analog-{0}'.format(i + 1))
        for i in range(spec['spdif']):
            labels.append('spdif-{0}'.format(i + 1))
        for i in range(spec['adat']):
            labels.append('adat-{0}'.format(i + 1))
        return labels

    @classmethod
    def calculate_out_offset(cls, spec: dict, target):
        targets = cls.get_out_labels(spec)
        return targets.index(target) * 4


class FFProtocolLatter(FFProtocolAbstract):
    __OPTION_REG = 0xffff00000014
    __STATUS_REG = 0x0000801c0000

    __SPECS = {
        0x000004: {
            'analog':   8,
            'spdif':    2,
            'adat':     8,
            'stream':   18,
            'avail':    18,
        },
    }

    __MUTE_VAL = 0x00000000
    __ZERO_VAL = 0x00008000
    __MIN_VAL = 0x00000001
    __MAX_VAL = 0x00010000

    def __init__(self, unit, model_id):
        if model_id not in self.__SPECS:
            raise ValueError('Unsupported model.')
        self.__unit = unit
        self.__spec = self.__SPECS[model_id]

        self.__cache = {'option' : 0x00000000, }

    def get_multiple_option_labels(self):
        return OptionReg.get_multiple_option_labels()

    def get_multiple_option_value_labels(self, target):
        return OptionReg.get_multiple_option_value_labels(target)

    def set_multiple_option(self, target, val):
        cache = self.__cache['option']
        cache = OptionReg.build_multiple_option(cache, target, val)
        self.write_to_unit(self.__unit, self.__OPTION_REG, [cache])
        self.__cache['option'] = cache

    def get_multiple_option(self, target):
        cache = self.__cache['option']
        return OptionReg.parse_multiple_option(cache, target)

    def get_boolean_option_labels(self):
        return OptionReg.get_boolean_option_labels()

    def get_boolean_option_item_labels(self, target):
        return OptionReg.get_boolean_option_item_labels(target)

    def set_boolean_option(self, target, item, enable):
        cache = self.__cache['option']
        cache = OptionReg.build_boolean_option(cache, target, item, enable)
        self.write_to_unit(self.__unit, self.__OPTION_REG, [cache])
        self.__cache['option'] = cache

    def get_boolean_option(self, target, item):
        cache = self.__cache['option']
        return OptionReg.parse_boolean_option(cache, target, item)

    def get_mixer_labels(self):
        return MixerReg.get_mixer_labels(self.__spec)

    def get_mixer_src_labels(self):
        return MixerReg.get_mixer_src_labels(self.__spec)

    def set_mixer_src(self, target, src, db):
        pass

    def get_mixer_src(self, target, src):
        return 0

    def get_out_labels(self):
        return OutReg.get_out_labels(self.__spec)

    def set_out_volume(self, target, db):
        pass

    def get_out_volume(self, target):
        return 0

    def get_sync_status(self):
        frames = self.read_from_unit(self.__unit, self.__STATUS_REG, 1)
        return StatusReg.parse(frames[0])

    def get_mute_db(self):
        return self.__parse_val_to_db(self.__MUTE_VAL)

    def get_zero_db(self):
        return self.__parse_val_to_db(self.__ZERO_VAL)

    def get_min_db(self):
        return self.__parse_val_to_db(self.__MIN_VAL)

    def get_max_db(self):
        return self.__parse_val_to_db(self.__MAX_VAL)

    def __build_val_from_db(self, db: float):
        if db == float('-inf'):
            return self.__MUTE_VAL
        return int(self.__ZERO_VAL * pow(10, db / 20))

    def __parse_val_to_db(self, val: int):
        if val == self.__MUTE_VAL:
            return float('-inf')
        return 20 * log10(val / self.__ZERO_VAL)

    def create_cache(self):
        cache = {}
        option  = self.__create_boolean_option_initial_cache(0x00000000)
        cache['option'] = self.__create_multiple_option_initial_cache(option)
        cache['mixer'] = self.__create_mixer_initial_cache()
        cache['out'] = self.__create_out_initial_cache()
        return cache

    def __create_boolean_option_initial_cache(self, cache):
        default_params = {
            'dsp': {
                'eq+dyn':       False,
            },
            'wdclk-in': {
                'termination':  True,
            },
            'wdclk-out': {
                'single-speed': False,
            },
        }
        for target, params in default_params.items():
            for item, enable in params.items():
                cache = OptionReg.build_boolean_option(cache, target, item,
                                                       enable)
        return cache

    def __create_multiple_option_initial_cache(self, cache):
        default_params = {
            'spdif-out':        'consumer',
            'optical-out':      'ADAT',
            'midi-low-addr':    '0x00000000',
        }
        for target, value in default_params.items():
            cache = OptionReg.build_multiple_option(cache, target, value)

        return cache

    def __create_mixer_initial_cache(self):
        targets = self.get_mixer_labels()
        srcs = self.get_mixer_src_labels()
        cache = [0x00] * (len(targets) * 2 * self.__spec['avail'])
        for i, target in enumerate(targets):
            for src in srcs:
                # Supply diagonal stream sources to each mixers.
                if src != 'stream-{0}'.format(i + 1):
                    val = self.__MUTE_VAL
                else:
                    val = self.__ZERO_VAL
                offset = MixerReg.calculate_src_offset(self.__spec, target, src)
                cache[offset // 4] = val
        return cache

    def __create_out_initial_cache(self):
        targets = self.get_out_labels()
        cache = [0x00] * len(targets)
        for target in targets:
            offset = OutReg.calculate_out_offset(self.__spec, target)
            cache[offset // 4] = self.__ZERO_VAL
        return cache

    def set_cache(self, cache):
        if self.__unit.get_property('streaming'):
            state = self.get_sync_status()
            rate = state['referred-rate']
            src = state['referred-clock']
        else:
            rate = '44100'
            src = ClkLabels.INTL.value
        frame = cache['option']
        frame = OptionReg.build_multiple_option(frame, 'sample-rate', rate)
        frame = OptionReg.build_multiple_option(frame, 'primary-clk-src', src)
        cache['option'] = frame

        self.__cache = cache

    def get_cache(self):
        return self.__cache
