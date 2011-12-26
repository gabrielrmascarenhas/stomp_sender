#!/usr/bin/python -W ignore
# coding: utf-8

import sys
import time
import stomp


class StompConnectionException(Exception):
    def __init__(self, error_message):
        self.error_message = error_message

    
    def __str__(self):
        return repr(self.error_message)


class StompMessageException(StompConnectionException):
    pass


def process_brokers(param):
    list_of_brokers = []
    brokers = param.split(',')
    for broker in brokers:
        broker = broker.strip()
        if ':' not in broker:
            hostname = broker
            port = 61613
        else:
            data = broker.split(':')
            hostname = data[0]
            port = int(data[1])
        list_of_brokers.append((hostname, port))
    return list_of_brokers


def process_params(params):
    key_value = {}
    for param in params:
        data = param.split('=')
        if len(data) == 1:
            continue
        key = data[0]
        if key[:2] == '--':
            key = key[2:]
        key_value[key] = '='.join(data[1:])
    return key_value


def send_message_via_stomp(brokers, headers, params):
    exception = None
    for broker in brokers:
        #t0 = time.time()
        amq = stomp.Connection([broker], reconnect_sleep_max=0)
        try:
            amq.start()
            amq.connect()
        except:
            exception = StompConnectionException('Exception1 when trying to connect to STOMP server %s.' % str(broker))
            continue
        if not amq.is_connected():
            exceptiom = StompConnectionException('Exception2 when trying to connect to STOMP server %s.' % str(broker))
            continue
        try:
            amq.send(str(params), headers)
        except:
            exception = StompMessageException('Exception when trying to send message to STOMP server %s.' % str(broker))
            continue
        amq.stop() #close connection in a clean way
        #print time.time() - t0
        return
    raise exception


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Usage: %s <event_type> [--activemq-server=hostname_or_IP[:port[, failover-server[:port][, ...]]]] [property1="value1" [property2="value2" ...]]' % \
              sys.argv[0]
        print 'The option activemq-server, if not supplied, is defined as "localhost".'
        sys.exit(2)
    
    event_type = sys.argv[1]
    params = process_params(sys.argv[2:])
    if 'activemq-server' in params:
        brokers = process_brokers(params['activemq-server'])
        del params['activemq-server']
    else:
        brokers = [('localhost', 61613)]
    headers = {'destination': '/queue/events', 'timestamp': int(time.time() * 1000), 'eventtype': event_type}
    if 'headers' in params:
        if ',' in params['headers']:
            keys_and_values = params['headers'].split(',')
        else:
            keys_and_values = [params['headers']]
        for kv in keys_and_values:
            if not kv:
                continue
            dados = kv.split(':')
            key = dados[0].strip()
            value = dados[1].strip()
            headers[key] = value
        del params['headers']

    try:
        send_message_via_stomp(brokers, headers, params)
	print params #TODO: adicionar opção "-v" para mostrar o evento enviado
    except (StompConnectionException, StompMessageException):
        print 'Error connecting or sending message to STOMP sender'
        sys.exit(1)
