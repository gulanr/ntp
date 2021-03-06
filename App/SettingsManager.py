from configparser import ConfigParser
import configparser
from dataclasses import dataclass

@dataclass
class Settings:
    profile_index: str
    developer_mode: bool


class SettingsManager:

    profile_index = 0

    daq_port = 'COM0'
    tsc_port = 'COM1'
    developer_mode = False

    @classmethod
    def create_settings_file(cls):
        settings = ConfigParser()

        settings.add_section('main')

        settings.set('main', 'profile_index', str(cls.profile_index))
        settings.set('main', 'developer_mode', str(cls.developer_mode))

        file_name = 'Settings.ini'

        with open(file_name, 'w') as f:
            settings.write(f)
    
    @classmethod
    def open_settings_file(cls):
        parser = ConfigParser()
        parser.read('Settings.ini')
        
        try:
            profile_index = int(parser.get('main', 'profile_index'))
            developer_mode = ('True' == parser.get('main', 'developer_mode'))
                   
        except configparser.NoSectionError:
            profile_index = cls.profile_index
            developer_mode = cls.developer_mode

        
        settings = Settings(profile_index, developer_mode)

        return settings

    @classmethod
    def save_profile_index(cls, profile_index):
        cls.profile_index = profile_index

        cls.create_settings_file()

    @classmethod
    def save_developer_mode(cls, in_developer_mode: bool):
        cls.developer_mode = in_developer_mode
        cls.create_settings_file()