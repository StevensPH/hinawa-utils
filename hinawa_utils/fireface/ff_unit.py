# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from pathlib import Path
from json import load, dump

import gi
gi.require_version('Hinawa', '2.0')
from gi.repository import Hinawa

from hinawa_utils.fireface.ff_config_rom_parser import FFConfigRomParser
from hinawa_utils.fireface.ff_protocol_former import FFProtocolFormer
from hinawa_utils.fireface.ff_protocol_latter import FFProtocolLatter

__all__ = ['FFUnit']


class FFUnit(Hinawa.SndUnit):
    __MODELS = {
        0x000001:   ('Fireface800', FFProtocolFormer),
        0x000002:   ('Fireface400', FFProtocolFormer),
        0x000004:   ("FirefaceUCX", FFProtocolLatter),
    }

    def __init__(self, path):
        super().__init__()
        self.open(path)
        self.listen()

        parser = FFConfigRomParser()
        info = parser.parse_rom(self.get_config_rom())
        model_id = info['model_id']
        if model_id not in self.__MODELS:
            raise OSError('Unsupported model.')

        self.__name = self.__MODELS[model_id][0]
        self.__protocol = self.__MODELS[model_id][1](self, model_id)

        guid = self.get_property('guid')
        self.__path = Path('/tmp/hinawa-{0:08x}'.format(guid))

        if self.__path.exists() and self.__path.is_file():
            cache = self.__read_cache_from_file()
            self.__protocol.set_cache(cache)
        else:
            cache = self.__protocol.create_cache()
            self.__protocol.set_cache(cache)
            self.__load_cache_to_unit()

    def __read_cache_from_file(self):
        with open(self.__path, 'r') as fd:
            cache = load(fd)
        return cache

    def __write_cache_to_file(self):
        with open(self.__path, 'w+') as fd:
            dump(self.__protocol.get_cache(), fd)

    def __load_cache_to_unit(self):
        for target in self.get_multiple_option_labels():
            val = self.get_multiple_option(target)
            self.set_multiple_option(target, val)
        for target in self.get_boolean_option_labels():
            for item in self.get_boolean_option_item_labels(target):
                enable = self.get_boolean_option(target, item)
                self.set_boolean_option(target, item, enable)
        for target in self.get_mixer_labels():
            for src in self.get_mixer_src_labels():
                db = self.get_mixer_src(target, src)
                self.set_mixer_src(target, src, db)
        for target in self.get_out_labels():
            db = self.get_out_volume(target)
            self.set_out_volume(target, db)

    def get_model_name(self):
        return self.__name

    #
    # Configuration for options.
    #
    def get_multiple_option_labels(self):
        return self.__protocol.get_multiple_option_labels()

    def get_multiple_option_value_labels(self, target):
        return self.__protocol.get_multiple_option_value_labels(target)

    def set_multiple_option(self, target, val):
        self.__protocol.set_multiple_option(target, val)
        self.__write_cache_to_file()

    def get_multiple_option(self, target):
        return self.__protocol.get_multiple_option(target)

    def get_boolean_option_labels(self):
        return self.__protocol.get_boolean_option_labels()

    def get_boolean_option_item_labels(self, target):
        return self.__protocol.get_boolean_option_item_labels(target)

    def set_boolean_option(self, target, item, enable):
        self.__protocol.set_boolean_option(target, item, enable)
        self.__write_cache_to_file()

    def get_boolean_option(self, target, item):
        return self.__protocol.get_boolean_option(target, item)

    #
    # Configuration for internal multiplexer.
    #
    def get_mixer_labels(self):
        return self.__protocol.get_mixer_labels()

    def get_mixer_src_labels(self):
        return self.__protocol.get_mixer_src_labels()

    def get_mixer_mute_db(self):
        return self.__protocol.get_mute_db()

    def get_mixer_min_db(self):
        return self.__protocol.get_min_db()

    def get_mixer_max_db(self):
        return self.__protocol.get_max_db()

    def set_mixer_src(self, target, src, db):
        self.__protocol.set_mixer_src(target, src, db)
        self.__write_cache_to_file()

    def get_mixer_src(self, target, src):
        return self.__protocol.get_mixer_src(target, src)

    #
    # Configuration for output.
    #
    def get_out_labels(self):
        return self.__protocol.get_out_labels()

    def set_out_volume(self, target, db):
        self.__protocol.set_out_volume(target, db)
        self.__write_cache_to_file()

    def get_out_volume(self, target):
        return self.__protocol.get_out_volume(target)

    #
    # Status of synchronization.
    #
    def get_sync_status(self):
        return self.__protocol.get_sync_status()

    #
    # Helper methods.
    #
    def get_db_mute(self):
        return self.__protocol.get_mute_db()

    def get_db_zero(self):
        return self.__protocol.get_zero_db()

    def get_db_min(self):
        return self.__protocol.get_min_db()

    def get_db_max(self):
        return self.__protocol.get_max_db()
