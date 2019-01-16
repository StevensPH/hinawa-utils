# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2019 Takashi Sakamoto

from abc import ABCMeta, abstractmethod
from struct import pack, unpack

import gi
gi.require_version('Hinawa', '2.0')
from gi.repository import Hinawa

__all__ = ['FFProtocolAbstract']


class FFProtocolAbstract(metaclass=ABCMeta):
    def write_to_unit(self, unit, addr, frames):
        data = pack('<{0}I'.format(len(frames)), *frames)
        req = Hinawa.FwReq()
        req.write(unit, addr, data)

    def read_from_unit(self, unit, addr, frame_count):
        req = Hinawa.FwReq()
        data = req.read(unit, addr, frame_count * 4)
        return unpack('<{0}I'.format(frame_count), data)

    #
    # Configuration for options.
    #
    @abstractmethod
    def get_multiple_option_labels(self) -> list:
        pass

    @abstractmethod
    def get_multiple_option_value_labels(self, target: str) -> list:
        pass

    @abstractmethod
    def set_multiple_option(self, target: str, val: str) -> list:
        pass

    @abstractmethod
    def get_multiple_option(self, target: str) -> list:
        pass

    @abstractmethod
    def get_boolean_option_labels(self) -> list:
        pass

    @abstractmethod
    def get_boolean_option_item_labels(self, target: str) -> list:
        pass

    @abstractmethod
    def set_boolean_option(self, target: str, item: str, enable: bool):
        pass

    @abstractmethod
    def get_boolean_option(self, target: str, item: str) -> bool:
        pass

    #
    # Configuration for internal multiplexer.
    #
    @abstractmethod
    def get_mixer_labels(self) -> list:
        pass

    @abstractmethod
    def get_mixer_src_labels(self) -> list:
        pass

    @abstractmethod
    def set_mixer_src(self, target: str, src: str, db: float):
        pass

    @abstractmethod
    def get_mixer_src(self, target: str, src: str) -> float:
        pass

    #
    # Configuration for Output.
    #
    @abstractmethod
    def get_out_labels(self):
        pass

    @abstractmethod
    def set_out_volume(self, target: str, db: float):
        pass

    @abstractmethod
    def get_out_volume(self, target: str) -> float:
        pass

    #
    # Status of synchronization.
    #
    @abstractmethod
    def get_sync_status(self):
        pass

    #
    # Misc.
    #
    @abstractmethod
    def get_mute_db(self) -> float:
        pass

    @abstractmethod
    def get_zero_db(self) -> float:
        pass

    @abstractmethod
    def get_min_db(self) -> float:
        pass

    @abstractmethod
    def get_max_db(self) -> float:
        pass

    @abstractmethod
    def create_cache(self) -> dict:
        pass

    @abstractmethod
    def set_cache(self, cache: dict):
        self.__cache = cache

    @abstractmethod
    def get_cache(self) -> dict:
        return self.__cache
