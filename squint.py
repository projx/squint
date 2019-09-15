#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author:       Kelvin W
# Date:         2019
# Description:  A script for scheduling and managing individual Blink Security Cameras - A feature
#               often requested, but yet to officially appear.
#
#               NOTE: this script uses an unofficial API, use this script wisely, if you hammer
#                     the Blink servers, then they will likely disable your account. It is recommended
#                     the scheduling features of this script, are set on a cron ran at most once an hour

import yaml
import json
import pickle
import sys
import os
import argparse
import click
import time
import datetime

from pprint import pprint
from blinkpy import blinkpy


"""
GLOBAL CONSTANTS
"""
CONFIG_LOCAL_PATH = "/etc/squint.yml"


"""
SquintSchedulerConfig -

All of Squints configuration is still in a single dictionary, this class is a wrapper for that, with 
fuctions generating the config, loading and setting different attributes
"""

class SquintConfigManager():
    format = ""
    config = dict()
    config_path = CONFIG_LOCAL_PATH

    def __init__(self, data_format="yml"):
        self.config["auth"] = dict()
        self.config["cameras"] = dict()
        self.format = data_format

    def __serialise(self):
        if self.format == "yml":
            return yaml.dump(self.config,default_flow_style=False)
        elif self.format == "json":
            return json.dumps(self.config, indent=4)
        else:
            print("No config format specified")

    def __unserialise(self, input):
        if self.format == "yml":
            return yaml.load(input, Loader=yaml.FullLoader)
        elif self.format == "json":
            return json.loads(input)
        else:
            print("No format specified")

    def __get_os_path(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        return dir_path

    def get_config_path(self):
        return self.__get_os_path() + self.config_path

    def get_username(self):
        return self.config["auth"]["username"]

    def get_password(self):
        return self.config["auth"]["password"]

    def save_to_file(self):
        output = self.__serialise()
        path = self.get_config_path()
        with open(path, 'w') as filehandle:
            filehandle.write(output)

    def load_from_file(self):
        path = self.get_config_path()
        with open(path, 'r') as filehandle:
            filecontent = filehandle.read()
        
        self.config = self.__unserialise(filecontent)

    def add_credentials(self, username, password):
        self.config["auth"]["username"] = username
        self.config["auth"]["password"] = password

    def get_cameras(self):
        return self.config["cameras"]

    def add_camera(self, name, sync_module):
        camera = dict()
        camera["name"] = name
        camera["sync_module"] = sync_module
        camera["schedules"] = dict()
        self.config["cameras"][name] = camera

    def add_camera_schedule(self, camera_name, schedule_name, from_time, until_time, motion_detect):
        schedule =  dict()
        schedule["schedule_name"] = schedule_name
        schedule["from_time"] = from_time
        schedule["until_time"] = until_time
        schedule["motion_detect"] = motion_detect
        camera_config = self.config["cameras"][camera_name]
        camera_config["schedules"][schedule_name] = schedule

    def add_default_options(self):
        """
        Some default settings related to schedule execution, only used when building fresh configuration
        """

    def populate_from_blink(self, cameras, schedules):
        """ 
        Extracts camera and associated sync_module from dataset returned by Blink, these are used
        to build out the basic config file. In addition, the schedule is used to add a boilerplate
        schedule for each camera
        
        :param cameras: This is the Blink.cameras dict return by Blink 
        :param schedules: A dict with boilderplate schedule for each camera
        :return:
        """
        for name, camera in cameras.items():
            sync_module = camera.attributes["sync_module"]
            self.add_camera(name, sync_module)
            for schedule in schedules:
                self.add_camera_schedule(name, schedule["schedule_name"],
                                             schedule["from_time"], schedule["until_time"], schedule["motion_detect"])


class SquintConnectionManager:

    use_local = False
    blink = ""

    def __init__(self, use_local = False):
        self.use_local = use_local

    def pickle_path(self):
        return os.path.dirname(os.path.realpath(__file__)) + "/blink_results.obj"

    def pickle_save(self):
        with open(self.pickle_path(), 'wb') as filehandle:
            pickle.dump(self.blink, filehandle)

    def pickle_load(self):
        with open(self.pickle_path(), 'rb') as filehandle:
            self.blink = pickle.load(filehandle)

    def connect(self, username, password):
        if self.use_local==True:
            click.echo("Loading locally Blink test object from " + self.pickle_path())
            self.pickle_load()
        else:
            click.echo("Opening connection to Blink servers")
            self.blink = blinkpy.Blink(username=username, password=password)
            self.blink.start()

    def set_motion_detect(self, camera_name, new_status):
        camera = self.blink.cameras[camera_name]
        current_status = camera.attributes["motion_enabled"]

        if current_status != new_status:
            print("{} is currently {}, changing this to {}".format(camera_name, current_status, new_status))
            camera.set_motion_detect(new_status)
            time.sleep(2)
        else:
            print("{} is already currently {}, leaving as-is".format(camera_name, current_status))


class SquintScheduleManager:

    def execute(self, connection, config):
        cameras = config.get_cameras()
        current_time = datetime.datetime.now().strftime("%H%M")

        update_queue = dict()

        # Extract schedules that we need to honour, these are added to updated_list, then actioned later
        for camera_name, camera in cameras.items():
            for schedule_name, schedule in camera["schedules"].items():
                from_time = schedule["from_time"]
                until_time = schedule["until_time"]
                if  from_time <=  current_time <= until_time:
                    click.echo('Added "{}" schedule {} to the queue'.format(camera_name, schedule_name))
                    update_queue[camera_name] = schedule

        if len(update_queue) == 0:
            click.echo("No schedules found for this period")
            return
        else:
            click.echo("Schedules Found: {}".format(len(update_queue)))
            click.echo("connecting to Blink servers")
            connection.connect(config.get_username(), config.get_password())

            for camera_name, schedule in update_queue.items():
                connection.set_motion_detect(camera_name, schedule["motion_detect"])


@click.group()
@click.version_option()
def cli():
    """Blink Manager
    The cli tool for scheduling your Blink Cameras...
    """


"""
 ARGS: Configuration
"""
@cli.group('config')
def config():
    """Manage the Blink Manager configuration file"""

@config.command('generate')
@click.argument('username')
@click.argument('password')
@click.option('--testresponse', "-t", is_flag=True, default=False, help='Test with locally saved response '
                                                                 '(generated with "debug save"), rather '
                                                                 'than contacting Blink servers')
def config_generate(username, password, testresponse):
    """Generates a basic config, including per-camera schedule. It does this by connecting to your Blink account
    and extracting the necessary data.

    Required Arguments:

    USERNAME for your Blink Security account\n
    PASSWORD for your Blink Security account
    """

    schedules = [{"schedule_name" : "00-NIGHT", "from_time":"0000", "until_time":'''0659''', "motion_detect" : True},
                {"schedule_name" : "01-DAY","from_time":"0700", "until_time":"2259", "motion_detect" : False},
                {"schedule_name" : "02-EVENING", "from_time":"2300", "until_time":"2359", "motion_detect" : True}]

    click.echo("Opening connection to Blink servers")

    config = SquintConfigManager("yml")
    click.echo("Generating configuration")
    config.add_credentials(username, password)

    connection = SquintConnectionManager(testresponse)
    connection.connect(config.get_username(), config.get_password())

    config.populate_from_blink(connection.blink.cameras, schedules)
    click.echo("Saving config to: " + config.get_config_path())
    config.save_to_file()

    click.echo("Finished saving!")
    click.echo('The generated config is a boilerplate with a basic example schedule, '
               'please update this to meets your needs. Once done you can use "execute simulate" command to test it')


"""
 ARGS: Push
"""
@cli.group('push')
def push():
    """Push configuration changes to Blink"""

@push.command('execute')
@click.option('--testresponse', "-t", is_flag=True, default=False, help='Test with locally saved response '
                                                                 '(generated with "debug save"), rather '
                                                                 'than contacting Blink servers')
def  push_execute(testresponse):
    """Execute the configuration push to Blink """
    config = SquintConfigManager("yml")
    config.load_from_file()

    connection = SquintConnectionManager(testresponse)
    scheduler = SquintScheduleManager()
    scheduler.execute(connection, config)

@push.command('simulate')
@click.option('--testresponse', "-t", is_flag=True, default=False, help='Test with locally saved response '
                                                                 '(generated with "debug save"), rather '
                                                                 'than contacting Blink servers')
def  push_simulate(testresponse):
    """Simulate the configuration push to Blink"""
    click.echo("Still deciding if this is needed.. for now, please use 'push execute -t' for testing")
    # config = SquintConfigManager("yml")
    # config.load_from_file()
    #
    # connection = SquintConnectionManager(testresponse)
    # scheduler = SquintScheduleManager()
    # scheduler.execute(connection, config)


"""
 ARGS: Debug
"""
@cli.group("debug")
def debug():
    """Avoid hammering Blink servers, save Blinks response locally testing"""

@debug.command('save')
def  debug_save():
    """Retrieve data from Blink, save locally for testing"""
    click.echo("Loading configuration")
    config = SquintConfigManager("yml")
    config.load_from_file()

    click.echo("Opening connection to Blink servers")
    connection = SquintConnectionManager()
    connection.connect(config.get_username(), config.get_password())

    click.echo("Saving Blink results to file")
    connection.pickle_save()
    click.echo("Blink results saved to " + connection.pickle_path())


if __name__ == '__main__':
    cli()
