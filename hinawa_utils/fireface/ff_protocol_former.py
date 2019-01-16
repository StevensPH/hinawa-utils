# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2019 Takashi Sakamoto

from enum import Enum
from math import log10, pow

from hinawa_utils.fireface.ff_protocol_abstract import FFProtocolAbstract

__all__ = ['FFProtocolFormer']


class ClkLabel(Enum):
    INTL = 'Internal'
    ADAT1 = 'ADAT1'
    ADAT2 = 'ADAT2'
    SPDIF = 'S/PDIF'
    WDCLK = 'Word-clock'
    LTO = 'LTO'
    TCO = 'TCO'


class OptionReg():
    __MULTIPLE_OPTION_MASKS = {
        'line-in': {
            'lo-gain':      (0x00000008, 0x00000000, 0x00000000),
            '-10dB':        (0x00000020, 0x00000002, 0x00000000),
            '+4dB':         (0x00000010, 0x00000003, 0x00000000),
        },
        'line-out': {
            '-10dB':        (0x00001000, 0x00000008, 0x00000000),
            '+4dB':         (0x00000800, 0x00000018, 0x00000000),
            'hi-gain':      (0x00000400, 0x00000010, 0x00000000),
        },
        'primary-clk-src': {
            ClkLabel.ADAT1.value:    (0x00000000, 0x00000000, 0x00000000),
            ClkLabel.ADAT2.value:    (0x00000000, 0x00000000, 0x00000400),
            ClkLabel.SPDIF.value:    (0x00000000, 0x00000000, 0x00000c00),
            ClkLabel.WDCLK.value:    (0x00000000, 0x00000000, 0x00001400),
        },
    }

    # bit flags for boolean value.
    __BOOLEAN_OPTION_MASKS = {
        'auto-sync': {
            'internal':     (0x00000000, 0x00000000, 0x00000001),
            'base-441':     (0x00000000, 0x00000000, 0x00000002),
            'base-480':     (0x00000000, 0x00000000, 0x00000004),
            'double':       (0x00000000, 0x00000000, 0x00000008),
            'quadruple':    (0x00000000, 0x00000000, 0x00000010),
        },
        'front-input': {
            'in-1':         (0x00000000, 0x00000800, 0x00000000),
            'in-7':         (0x00000000, 0x00000020, 0x00000000),
            'in-8':         (0x00000000, 0x00000080, 0x00000000),
        },
        'rear-input': {
            'in-1':         (0x00000000, 0x00000004, 0x00000000),
            'in-7':         (0x00000000, 0x00000040, 0x00000000),
            'in-8':         (0x00000000, 0x00000100, 0x00000000),
        },
        'phantom-power': {
            'mic-7':        (0x00000001, 0x00000000, 0x00000000),
            'mic-8':        (0x00000080, 0x00000000, 0x00000000),
            'mic-9':        (0x00000002, 0x00000000, 0x00000000),
            'mic-10':       (0x00000100, 0x00000000, 0x00000000),
        },
        'spdif-in': {
            'optical':      (0x00000000, 0x00000000, 0x00000200),
            'track-maker':  (0x00000000, 0x00000000, 0x40000000),
        },
        'spdif-out': {
            'professional': (0x00000000, 0x00000000, 0x00000020),
            'emphasis':     (0x00000000, 0x00000000, 0x00000040),
            'non-audio':    (0x00000000, 0x00000000, 0x00000080),
            'optical':      (0x00000000, 0x00000000, 0x00000100),
        },
        'instruments': {
            'drive':        (0x00000200, 0x00000200, 0x00000000),
            'limit':        (0x00000000, 0x00000000, 0x00010000),
            'speaker-emu':  (0x00000004, 0x00000000, 0x00000000),
        },
        'wdclk-out': {
            'single-speed': (0x00000000, 0x00000000, 0x00004000),
        },
        'midi-low-addr': {
            '0x00000000':   (0x00000000, 0x00000000, 0x04000000),
            '0x00000080':   (0x00000000, 0x00000000, 0x08000000),
            '0x00000100':   (0x00000000, 0x00000000, 0x10000000),
            '0x00000180':   (0x00000000, 0x00000000, 0x20000000),
        },
        'in-error': {
            'continue':     (0x00000000, 0x00000000, 0x80000000),
        }
    }

    # Helper functions for multiple value options.
    @classmethod
    def get_multiple_option_labels(cls):
        return (cls.__MULTIPLE_OPTION_MASKS.keys())

    @classmethod
    def get_multiple_option_value_labels(cls, target):
        if target not in cls.__MULTIPLE_OPTION_MASKS:
            raise ValueError('Invalid argument for multi option.')
        return (cls.__MULTIPLE_OPTION_MASKS[target].keys())

    @classmethod
    def build_multiple_option(cls, frames, target, val):
        if target not in cls.__MULTIPLE_OPTION_MASKS:
            raise ValueError('Invalid argument for multi option.')
        if val not in cls.__MULTIPLE_OPTION_MASKS[target]:
            raise ValueError('Invalid argument for value of multi option.')
        elems = cls.__MULTIPLE_OPTION_MASKS[target]
        for name, flags in elems.items():
            for i, flag in enumerate(flags):
                frames[i] &= ~flag
        for i, flag in enumerate(elems[val]):
            frames[i] |= flag

    @classmethod
    def parse_multiple_option(cls, frames, target):
        if target not in cls.__MULTIPLE_OPTION_MASKS:
            raise ValueError('Invalid argument for multi option.')
        elems = cls.__MULTIPLE_OPTION_MASKS[target]
        masks = [0x00] * 3
        for name, flags in elems.items():
            for i, flag in enumerate(flags):
                masks[i] |= flag
        for val, flags in elems.items():
            for i, flag in enumerate(flags):
                if frames[i] & masks[i] != flag:
                    break
            else:
                return val
        raise OSError('Unexpected state of bit flags.')

    # Helper functions to handle boolen options.
    @classmethod
    def get_boolean_option_labels(cls):
        return (cls.__BOOLEAN_OPTION_MASKS.keys())

    @classmethod
    def get_boolean_option_item_labels(cls, target):
        if target not in cls.__BOOLEAN_OPTION_MASKS:
            raise ValueError('Invalid argument for bool option.')
        return (cls.__BOOLEAN_OPTION_MASKS[target].keys())

    @classmethod
    def build_boolean_option(cls, frames, target, item, enable):
        if target not in cls.__BOOLEAN_OPTION_MASKS:
            raise ValueError('Invalid argument for bool option.')
        if item not in cls.__BOOLEAN_OPTION_MASKS[target]:
            raise ValueError('Invalid argument for item of bool option.')
        masks = cls.__BOOLEAN_OPTION_MASKS[target][item]
        for i, mask in enumerate(masks):
            frames[i] &= ~mask
            if enable:
                frames[i] |= mask

    @classmethod
    def parse_boolean_option(cls, frames, target, item):
        if target not in cls.__BOOLEAN_OPTION_MASKS:
            raise ValueError('Invalid argument for bool option.')
        if item not in cls.__BOOLEAN_OPTION_MASKS[target]:
            raise ValueError('Invalid argument for item of bool option.')
        masks = cls.__BOOLEAN_OPTION_MASKS[target][item]
        for i, mask in enumerate(masks):
            if frames[i] & mask != mask:
                return False
        return True


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


class StatusReg():
    __SINGLE_STATUS_MASKS = {
        'spdif-rate': {
            '32000':                (0x00004000, 0x00000000),
            '44100':                (0x00008000, 0x00000000),
            '48000':                (0x0000c000, 0x00000000),
            '64000':                (0x00010000, 0x00000000),
            '88200':                (0x00014000, 0x00000000),
            '96000':                (0x00018000, 0x00000000),
            '128000':               (0x0001c000, 0x00000000),
            '176400':               (0x00020000, 0x00000000),
            '192000':               (0x00024000, 0x00000000),
        },
        'referred-rate': {
            '32000':                (0x02000000, 0x00000000),
            '44100':                (0x04000000, 0x00000000),
            '48000':                (0x06000000, 0x00000000),
            '64000':                (0x08000000, 0x00000000),
            '88200':                (0x0a000000, 0x00000000),
            '96000':                (0x0c000000, 0x00000000),
            '128000':               (0x0e000000, 0x00000000),
            '176400':               (0x10000000, 0x00000000),
            '192000':               (0x12000000, 0x00000000),
        },
        'base-freq': {
            '44100':                (0x00000000, 0x00000000),
            '32000':                (0x00000000, 0x00000002),
            '48000':                (0x00000000, 0x00000006),
        },
        'multiplier': {
            'single':               (0x00000000, 0x00000000),
            'double':               (0x00000000, 0x00000008),
            'quadruple':            (0x00000000, 0x00000010),
        },
        'sync-mode': {
            'internal':             (0x00000000, 0x00000001),
        },
        'referred': {
            ClkLabel.ADAT1.value:   (0x00000000, 0x00000000),
            ClkLabel.ADAT2.value:   (0x00400000, 0x00000000),
            ClkLabel.SPDIF.value:   (0x00c00000, 0x00000000),
            ClkLabel.WDCLK.value:   (0x01000000, 0x00000000),
            ClkLabel.TCO.value:     (0x01400000, 0x00000000),
        },
    }

    __MULTIPLE_STATUS_MASKS = {
        'synchronized': {
            ClkLabel.ADAT1.value:   (0x00001000, 0x00000000),
            ClkLabel.ADAT2.value:   (0x00002000, 0x00000000),
            ClkLabel.SPDIF.value:   (0x00040000, 0x00000000),
            ClkLabel.WDCLK.value:   (0x20000000, 0x00000000),
            ClkLabel.TCO.value:     (0x00000000, 0x00400000),
        },
        'locked': {
            ClkLabel.ADAT1.value:   (0x00000400, 0x00000000),
            ClkLabel.ADAT2.value:   (0x00000800, 0x00000000),
            ClkLabel.SPDIF.value:   (0x00080000, 0x00000000),
            ClkLabel.WDCLK.value:   (0x40000000, 0x00000000),
            ClkLabel.TCO.value:     (0x00000000, 0x00800000),
        },
    }

    @classmethod
    def parse(cls, frames):
        status = {}

        for target, elems in cls.__SINGLE_STATUS_MASKS.items():
            masks = [0x00] * 2
            for name, flags in elems.items():
                for i, flag in enumerate(flags):
                    masks[i] |= flag
            for name, flags in elems.items():
                for i, flag in enumerate(flags):
                    if frames[i] & masks[i] != flag:
                        break
                else:
                    status[target] = name

        for target, elems in cls.__MULTIPLE_STATUS_MASKS.items():
            status[target] = {}
            for name, flags in elems.items():
                for i, flag in enumerate(flags):
                    if frames[i] & flag != flag:
                        status[target][name] = False
                        break
                else:
                    status[target][name] = True

        return status


class MeterReg():
    @classmethod
    def parse(cls, spec: dict, frames: list):
        meters = []

        meters['hoge'] = []
        pos = 0
        for i in range(spec['analog']):
            meters['hoge']['analog-{0}'.format(i + 1)] = meters[pos + i * 2 + 1]
            pos += 2
        for i in range(spec['spdif']):
            meters['hoge']['spdif-{0}'.format(i + 1)] = meters[pos + i * 2 + 1]
            pos += 2
        for i in range(spec['adat']):
            meters['hoge']['adat-{0}'.format(i + 1)] = meters[pos + i * 2 + 1]
            pos += 2

        return meters


class FFProtocolFormer(FFProtocolAbstract):
    __REGS = {
        # model_id: (option offset, mixer offset, out offset)
        0x000001:   (0x0000fc88f014, 0x000080080000, 0x000080081f80),
        0x000002:   (0x00008010051c, 0x000080080000, 0x000080080f80),
    }

    __STATUS_REG = 0x0000801c0000

    __SPECS = {
        0x000001: {
            'analog':   10,
            'spdif':    2,
            'adat':     16,
            'stream':   28,
            'avail':    32,
        },
        0x000002: {
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
        if model_id not in self.__REGS:
            raise ValueError('Unsupported model.')
        self.__unit = unit
        self.__regs = self.__REGS[model_id]
        self.__spec = self.__SPECS[model_id]

    def get_multiple_option_labels(self):
        return OptionReg.get_multiple_option_labels()

    def get_multiple_option_value_labels(self, target):
        return OptionReg.get_multiple_option_value_labels(target)

    def set_multiple_option(self, target, val):
        cache = self.__cache['option']
        OptionReg.build_multiple_option(cache, target, val)
        addr = self.__regs[0]
        self.write_to_unit(self.__unit, addr, cache)

    def get_multiple_option(self, target):
        cache = self.__cache['option']
        return OptionReg.parse_multiple_option(cache, target)

    def get_boolean_option_labels(self):
        return OptionReg.get_boolean_option_labels()

    def get_boolean_option_item_labels(self, target):
        return OptionReg.get_boolean_option_item_labels(target)

    def set_boolean_option(self, target, item, enable):
        cache = self.__cache['option']
        OptionReg.build_boolean_option(cache, target, item, enable)
        addr = self.__regs[0]
        self.write_to_unit(self.__unit, addr, cache)

    def get_boolean_option(self, target, item):
        cache = self.__cache['option']
        return OptionReg.parse_boolean_option(cache, target, item)

    def get_mixer_labels(self):
        return MixerReg.get_mixer_labels(self.__spec)

    def get_mixer_src_labels(self):
        return MixerReg.get_mixer_src_labels(self.__spec)

    def set_mixer_src(self, target, src, db):
        offset = MixerReg.calculate_src_offset(self.__spec, target, src)
        addr = self.__regs[1] + offset
        val = self.__build_val_from_db(db)
        self.write_to_unit(self.__unit, addr, [val])

        self.__cache['mixer'][offset // 4] = val

    def get_mixer_src(self, target, src):
        offset = MixerReg.calculate_src_offset(self.__spec, target, src)
        return self.__parse_val_to_db(self.__cache['mixer'][offset // 4])

    def get_out_labels(self):
        return OutReg.get_out_labels(self.__spec)

    def set_out_volume(self, target, db):
        offset = OutReg.calculate_out_offset(self.__spec, target)
        addr = self.__regs[2] + offset
        val = self.__build_val_from_db(db)
        self.write_to_unit(self.__unit, addr, [val])

        self.__cache['out'][offset // 4] = val

    def get_out_volume(self, target):
        offset = OutReg.calculate_out_offset(self.__spec, target)
        return self.__parse_val_to_db(self.__cache['out'][offset // 4])

    def get_sync_status(self):
        frames = self.read_from_unit(self.__unit, self.__STATUS_REG, 2)
        return StatusReg.parse(frames)

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
        cache['option'] = [0x00] * 3
        self.__create_boolean_option_initial_cache(cache['option'])
        self.__create_multiple_option_initial_cache(cache['option'])
        cache['mixer'] = self.__create_mixer_initial_cache()
        cache['out'] = self.__create_out_initial_cache()
        return cache

    def __create_boolean_option_initial_cache(self, cache):
        default_params = {
            'auto-sync': {
                'internal':     True,   'base-441':     True,
                'base-480':     True,   'double':       True,
                'quadruple':    True,
            },
            'front-input': {
                'in-1':         False,  'in-7':         False,
                'in-8':         False,
            },
            'rear-input': {
                'in-1':         True,   'in-7':         True,
                'in-8':         True,
            },
            'phantom-power': {
                'mic-7':        False,  'mic-8':        False,
                'mic-9':        False,  'mic-10':       False,
            },
            'spdif-in': {
                'optical':      False,  'track-maker':  False,
            },
            'spdif-out': {
                'professional': False,  'emphasis':     False,
                'non-audio':    False,  'optical':      False,
            },
            'instruments': {
                'drive':        False,  'limit':        True,
                'speaker-emu':  False,
            },
            'wdclk-out': {
                'single-speed': True,
            },
            'in-error': {
                'continue':     True,
            },
        }
        for target, params in default_params.items():
            for item, enable in params.items():
                OptionReg.build_boolean_option(cache, target, item, enable)

    def __create_multiple_option_initial_cache(self, cache):
        default_params = {
            'line-in':          '-10dB',
            'line-out':         '-10dB',
            'primary-clk-src':  ClkLabel.SPDIF.value,
        }
        for target, value in default_params.items():
            OptionReg.build_multiple_option(cache, target, value)

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
        self.__cache = cache

    def get_cache(self):
        return self.__cache
