#!/usr/bin/env python
# -*- coding: utf-8; -*-
"""
Copyright (C) 2013 - Kaan Özdinçer <kaanozdincer@gmail.com>

This file is part of rabbitmq-collect-plugin.

rabbitmq-collectd-plugin is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

rabbitmq-collectd-plugin is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>

"""

import collectd
import urllib2
import json


NAME = 'rabbitmq'
HOST = 'localhost'
PORT = '15672'
USER = 'guest'
PASS = 'guest'
VHOST = urllib2.quote('/', safe='')
VERBOSE = False
QUEUE = None


def get_rabbitmqctl_queue_status():
    """Get all statistics with rabbitmq-manager api"""
    stats = {}

    url_overview = 'http://%s:%s/api/queues/%s/%s' % (HOST, PORT, VHOST, QUEUE)
    passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
    passman.add_password(None, url_overview, USER, PASS)
    authhandler = urllib2.HTTPBasicAuthHandler(passman)
    opener = urllib2.build_opener(authhandler)
    urllib2.install_opener(opener)
    queue_overview = json.load(urllib2.urlopen(url_overview))

    # queue stats
    stats['messages'] = int(queue_overview['messages'])
    stats['messages_unacknowledged'] = int(queue_overview['messages_unacknowledged'])
    stats['messages_ready'] = int(queue_overview['messages_ready'])
    stats['consumers'] = int(queue_overview['messages_ready'])
    stats['deliver_rate'] = int(queue_overview['message_stats']['deliver_details']['rate'])
    stats['publish_rate'] = int(queue_overview['message_stats']['publish_details']['rate'])

    return stats


def configure_callback(conf):
    """Config data from collectd"""
    log('verb', 'configure_callback Running')
    global NAME, HOST, PORT, VHOST, QUEUE, USER, PASS, VERBOSE
    for node in conf.children:
        if node.key == 'Name':
            NAME = node.values[0]
        elif node.key == 'Host':
            HOST = node.values[0]
        elif node.key == 'Port':
            PORT = int(node.values[0])
        elif node.key == 'User':
            USER = node.values[0]
        elif node.key == 'Pass':
            PASS = node.values[0]
        elif node.key == 'Verbose':
            VERBOSE = node.values[0]
        elif node.key == 'Vhost':
            VHOST = urllib2.quote(node.values[0], safe="")
        elif node.key == 'Queue':
            QUEUE = urllib2.quote(node.values[0], safe="")
        else:
            log('warn', 'Unknown config key: %s' % node.key)
    
    if QUEUE is None:
        log('err', 'Queue parameter is mandatory')


def read_callback():
    """Send rabbitmq stats to collectd"""
    log('verb', 'read_callback Running')
    info = get_rabbitmqctl_queue_status()

    # Send keys to collectd
    for key, value in info:
        log('verb', 'Sent value: %s %i' % (key, value))
        value = collectd.Values(plugin=NAME)
        value.type = 'gauge'
        value.type_instance = key
        value.values = [int(value)]
        value.dispatch()


def log(t, message):
    """Log messages to collect logger"""
    if t == 'err':
        collectd.error('%s: %s' % (NAME, message))
    elif t == 'warn':
        collectd.warning('%s: %s' % (NAME, message))
    elif t == 'verb':
        if VERBOSE == True:
            collectd.info('%s: %s' % (NAME, message))
    else:
        collectd.info('%s: %s' % (NAME, message))


# Register to collectd
collectd.register_config(configure_callback)
collectd.warning('Initialising %s' % NAME)
collectd.register_read(read_callback)
