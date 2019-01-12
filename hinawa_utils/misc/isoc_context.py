# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2019 Takashi Sakamoto

__all__ = ['IsocContext']

class IsocContext():
    __O_MASK = 0x00000fff
    __C_MASK = 0x01fff000
    __S_MASK = 0xfe000000

    __O_WIDTH = 12
    __C_WIDTH = 13
    __S_WIDTH = 7

    __O_MAX = 3072
    __C_MAX = 8000
    __S_MAX = 8

    __TICKS_PER_SEC = 8000 * 3072 * 8

    __RATES = {
        0x00:   32000,
        0x01:   44100,
        0x02:   48000,
        0x03:   88200,
        0x04:   96000,
        0x05:   176400,
        0x06:   192000,
    }

    __SYT_INTERVALS = {
        0x00:   8,
        0x01:   8,
        0x02:   8,
        0x03:   16,
        0x04:   16,
        0x05:   32,
        0x06:   32,
    }

    def __init__(self, ch):
        self.__ch = ch
        self.__tstamp = None
        self.__delay = None
        self.__accum = None
        self.__reset_cycle = None
        self.__db_count = 0

    @staticmethod
    def header():
        return ('s- c--- o--- | '
                'tstamp--- elps | '
                'delay gap- | '
                'accumdif | '
                'db dbcnt-')

    @staticmethod
    def separator():
        return ('-- ---- ---- | '
                '--------- ---- | '
                '----- ---- | '
                '-------- | '
                '-- ------')

    @classmethod
    def parse_cycle_start(cls, cycle_start):
        sec = (cycle_start & cls.__S_MASK) >> (cls.__C_WIDTH + cls.__O_WIDTH)
        cycle = (cycle_start & cls.__C_MASK) >> cls.__O_WIDTH
        return sec, cycle

    def parse(self, quads_per_payload, sec, cycle, cip0, cip1):
        db, db_count = self.__calculate_db_count(cycle, quads_per_payload, cip0)

        syt = cip1 & 0x0000ffff
        if syt != 0x0000ffff:
            t_s, t_c, t_o, tstamp, elapse = self.__parse_tstamp(sec, cycle, syt)
            delay, delay_gap = self.__calculate_delay(sec, cycle, tstamp)
            accum, accum_diff = self.__calculate_accum(tstamp, cip1)
            tmpl = ('{0: >2d} {1: >4d} {2: >4d} | '
                    '{3: >9d} {4: >4d} | '
                    '{5: >5d} {6: >4d} | '
                    '{7: >8.2f}')
            phrase = tmpl.format(t_s, t_c, t_o,
                                 tstamp, elapse,
                                 delay, delay_gap, accum_diff)
            self.__tstamp = tstamp
            self.__delay = delay
            self.__accum = accum
            if self.__reset_cycle == None:
                self.__reset_cycle = cycle
        else:
            phrase = ('-- ---- ---- | '
                      '--------- ---- | '
                      '----- ---- | '
                      '--------')

        return '{0} | {1: >2d} {2: >6d} '.format(phrase, db, db_count)

    def __parse_tstamp(self, sec, cycle, syt):
        t_offset = syt & self.__O_MASK
        t_cycle = cycle
        syt_cycle = (syt & self.__C_MASK) >> self.__O_WIDTH
        if syt_cycle < t_cycle & 0xf:
            t_cycle += 0xe  # roundup.
        t_cycle = (t_cycle & 0x1ff0) | syt_cycle
        t_sec = sec
        if t_cycle >= self.__C_MAX:
            t_cycle %= self.__C_MAX
            t_sec += 1
        t_sec %= self.__S_MAX

        tstamp = (t_sec * self.__C_MAX + t_cycle) * self.__O_MAX + t_offset
    
        if self.__tstamp != None:
            if tstamp >= self.__tstamp:
                elapse = tstamp - self.__tstamp
            else:
                elapse = self.__TICKS_PER_SEC + tstamp - self.__tstamp
        else:
            elapse = 0

        return t_sec, t_cycle, t_offset, tstamp, elapse

    def __calculate_delay(self, sec, cycle, tstamp):
        start = (sec % self.__S_MAX * self.__C_MAX + cycle) * self.__O_MAX
        if start < tstamp:
            delay = tstamp - start
        else:
            delay = self.__TICKS_PER_SEC + tstamp - start

        if self.__delay != None:
            if delay > self.__delay:
                delay_gap = delay - self.__delay
            else:
                delay_gap = self.__O_MAX + delay - self.__delay
        else:
            delay_gap = 0

        return delay, delay_gap

    def __calculate_accum(self, tstamp, cip1):
        sfc = (cip1 & 0x00ff0000) >> 16
        rate = self.__RATES[sfc]
        syt_interval = self.__SYT_INTERVALS[sfc]

        if self.__accum != None:
            accum = self.__C_MAX * self.__O_MAX * syt_interval / rate + self.__accum
            accum %= self.__TICKS_PER_SEC
            if abs(accum - tstamp) < self.__TICKS_PER_SEC / 2:
                accum_diff = accum - tstamp
            else:
                accum_diff = self.__TICKS_PER_SEC + accum - tstamp
        else:
            accum = tstamp
            accum_diff = 0

        return accum, accum_diff

    def __calculate_db_count(self, cycle, quads_per_payload, cip0):
        quads_per_db = (cip0 & 0x00ff0000) >> 16
        dbs_per_payload = (quads_per_payload - 2) // quads_per_db

        if self.__reset_cycle != None:
            db_count = self.__db_count
            db_count += dbs_per_payload
            if self.__reset_cycle != cycle:
                self.__db_count = db_count
            else:
                self.__db_count = 0
        else:
            db_count = 0

        return dbs_per_payload, db_count
