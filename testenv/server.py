# -*- coding: utf-8 -*-

import os
import os.path
import shlex
import subprocess
import sys
import six

from . import utils


class Server(object):

    command = None
    start_timeout = 5
    pid = None
    pidfile = None
    stdout = None
    stderr = None
    environ = None
    address = None
    after = None

    def __init__(self, runner, name, cfg):
        self.runner = runner
        self.name = name
        self.basedir = os.path.join(self.runner.basedir, self.name)
        self.init(**cfg)
        if isinstance(self.after, list):
            pass
        elif self.after is None:
            self.after = []
        else:
            self.after = [self.after]

    def init(self, **kwargs):
        for k, v in six.iteritems(kwargs):
            setattr(self, k, v)

    def confpath(self, path):
        return self.runner.confpath(path)

    def basepath(self, path):
        if os.path.isabs(path):
            return path
        else:
            return os.path.join(self.basedir, path)

    def prepare(self):
        os.makedirs(self.basedir)

    def start(self):
        if self.stdout is not None:
            self.stdout = open(self.basepath(self.stdout), 'w')
        if self.stderr is not None:
            self.stderr = open(self.basepath(self.stderr), 'w')
        sys.stderr.write(" ".join(self.command) + "\n")
        p = subprocess.Popen(self.command, stdout=self.stdout, stderr=self.stderr, env=self.environ, cwd=self.basedir)
        if self.pidfile is not None:
            self.pid = utils.wait_for_pid(self.pidfile, maxtime=self.start_timeout)
            if self.pid is None:
                raise Exception("server {0} didn't started (pidfile)"
                        " in {1} seconds".format(self.name, self.start_timeout))
        else:
            self.pid = p.pid
        sys.stderr.write("pid = " + str(self.pid) + "\n")

    def is_ready(self):
        if self.address is not None:
            return utils.wait_for_socket(self.address, maxtime=0)
        return True

    def wait_ready(self):
        res = utils.wait_for(self.is_ready, maxtime=self.start_timeout)
        if not res:
            raise Exception("server {0} didn't got ready in {1} seconds".format(self.name, self.start_timeout))

    def fill(self):
        pass  # optional

    def ctrl(self, *args):
        pass  # optional

    def is_running(self):
        if self.pid is None:
            return False
        return utils.is_running(self.pid)

    def stop(self):
        utils.stop_with_signal(self.pid, is_child=(self.pidfile is None))


class GenericServer(Server):

    CONFIGTYPES = {
        'ini': utils.write_ini,
        'yaml': utils.write_yaml,
    }

    config = None

    def init(self, **kwargs):
        assert 'command' in kwargs, "command option missed"
        command = kwargs['command']
        assert isinstance(command, six.string_types + (list,)), "command should be a string or array"
        if isinstance(command, six.string_types):
            command = shlex.split(command)
        binary = utils.find_binary(command[0], cwd=self.runner.confdir)
        assert binary is not None, "Can't find executable for " + command[0]
        command[0] = binary
        kwargs['command'] = command
        if 'config' in kwargs:
            assert type(kwargs['config']) == dict, "config option should be a dict"
            assert 'configfile' in kwargs, "configfile option missed"
            assert 'configtype' in kwargs, "configtype option missed"
            assert kwargs['configtype'] in self.CONFIGTYPES, \
                "configtype {0} is not supported".format(kwargs['configtype'])
        if 'stdout' in kwargs:
            assert isinstance(kwargs['stdout'], six.string_types), "stdout option should be a string"
        else:
            kwargs['stdout'] = self.basepath(self.name + '.log')
        if 'stderr' in kwargs:
            assert isinstance(kwargs['stderr'], six.string_types), "stderr option should be a string"
        else:
            kwargs['stderr'] = self.basepath(self.name + '.log')
        if 'pidfile' in kwargs:
            assert isinstance(kwargs['pidfile'], six.string_types), "pidfile option should be a string"
        if 'environ' in kwargs:
            assert isinstance(kwargs['environ'], dict), "environ option should be a dict"
        if 'start_timeout' in kwargs:
            assert isinstance(kwargs['start_timeout'], int), "start_timeout option should be a dict"
        super(GenericServer, self).init(**kwargs)

    def prepare(self):
        super(GenericServer, self).prepare()
        if self.config is not None:
            config_writer = self.CONFIGTYPES[self.configtype]
            config_writer(self.basepath(self.configfile), self.config)
