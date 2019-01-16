# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2019 Takashi Sakamoto

from enum import Enum
from struct import pack, unpack
from array import array

import gi
gi.require_version('Hinawa', '2.0')
from gi.repository import Hinawa

__all__ = ['SSLDuendeProtocol']


class CmdCode(Enum):
    PROG_LOAD       = 0x05
    CONF            = 0x32
    USED_COUNT      = 0x37
    PROG_REGISTRY   = 0x41

class StatusCode(Enum):
    SUCCESS = 0x08
    LOADED  = 0x0c

class SSLDuendeProtocol():
    __BASE_ADDR = 0xffffe0300000
    __PARAM_OFFSET = 0x0004
    __METADATA_OFFSET = 0x0800

    @classmethod
    def __command_request(cls, unit, req, cmd, args, status, resp_quads):
        frames = bytearray()
        frames += pack('>I', cmd.value)
        frames += pack('>{0}I'.format(len(args)), *args)
        req.write(unit, cls.__BASE_ADDR, frames)

        quad_count = 1 + resp_quads
        resp = req.read(unit, cls.__BASE_ADDR, quad_count * 4)
        frames = unpack('>{0}I'.format(quad_count), resp)
        if frames[0] != status.value:
            raise OSError('Fail to execute request.')
        return frames[1:]


    @classmethod
    def read_metadata(cls, unit: Hinawa.FwUnit):
        metadata = {}

        # Response subaction is often delayed.
        req = Hinawa.FwReq(timeout=100)

        addr = cls.__BASE_ADDR + cls.__METADATA_OFFSET
        resp = req.read(unit, addr, 128)

        letters = bytearray()
        for i in range(0, 16):
            letters.extend(list(reversed(resp[4 * i:4 * i + 4])))
        literal = letters.decode('utf-8').rstrip('\0')
        entries = literal.split(' ')
        metadata['firmware'] = {}
        for entry in entries:
            tokens = entry.split('=')
            metadata['firmware'][tokens[0]] = tokens[1]

        # Not yet cleared.
        #frames = unpack('>16I', resp[64:])
        #for f in frames:
        #    print('{:08x}'.format(f))

        return metadata

    @classmethod
    def get_program_registry(cls, unit: Hinawa.FwUnit, index: int):
        if index < 0 or index > 0x1f:
            raise ValueError('Invalid argument for index of program.')

        args = array('I')
        args.append(index)

        req = Hinawa.FwReq(timeout=100)
        params = cls.__command_request(unit, req, CmdCode.PROG_REGISTRY, args,
                                       StatusCode.SUCCESS, 2)

        registry = {}
        registry['index'] = index
        registry['authorized'] = bool(params[0])
        registry['remaining'] = params[1]
        return registry

    @classmethod
    def get_used_count(cls, unit: Hinawa.FwUnit):
        args = array('I')
        args.append(8)
        args.append(0)

        req = Hinawa.FwReq(timeout=100)
        params = cls.__command_request(unit, req, CmdCode.USED_COUNT, args,
                                       StatusCode.SUCCESS, 2)
        return params[0]

    @classmethod
    def load_program(cls, unit: Hinawa.FwUnit, index: int, count: int):
        if index != 1:
            raise ValueError('Invalid argument for index of program.')
        if ch not in (1, 2):
            raise ValueError('Invalid argument for number of channels.')
        args = array('I')
        args.append(0xffffffff)
        args.append(index)      # load if greater than zero.
        args.append(count)

        # Response subaction is often delayed.
        req = Hinawa.FwReq(timeout= 200)
        params = cls.__command_request(unit, req, CmdCode.PROG_LOAD, args,
                                       StatusCode.LOADED, 3)
        if params[0] != 0x01:
            raise OSError('Unexpected response.')
        return params[2]

    @classmethod
    def unload_program(cls, unit: Hinawa.FwUnit, tag: int, ch: int):
        args= array('I')
        args.append(tag)
        args.append(0)  # unload if zero.
        args.append(ch)

        # Response subaction is often delayed.
        req = Hinawa.FwReq(timeout= 200)
        params = cls.__command_request(unit, req, CmdCode.PROG_LOAD, args,
                                       StatusCode.LOADED, 3)
        if params[1] != 0x04:
            raise OSError('Unexpected response.')
        return params[2]
