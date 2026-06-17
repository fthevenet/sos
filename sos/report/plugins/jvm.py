# This file is part of the sos project: https://github.com/sosreport/sos
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# version 2 of the GNU General Public License.
#
# See the LICENSE file in the source distribution for further information.

import os
import pwd
from sos.report.plugins import PluginOpt, Plugin, IndependentPlugin


class Jvm(Plugin, IndependentPlugin):
    """
    This plugin collects information about instances of the Java Virtual Machine
    running on the system at the time of the report.

    This information is captured by using the 'jcmd' JDK utility with a set number
    of predefined commands.

    If the 'clean' command is provided to
    """

    short_desc = 'Collect information about running Java Virtual Machines'

    plugin_name = 'jvm'
    profiles = ('java',)
    commands = ('jcmd',)

    option_list = [
        PluginOpt('jcmd_timeout', default=10,
                  desc='Timeout (in seconds) for each individual jcmd invocation')
    ]

    def setup(self):
        jcmd_list_output = self.collect_cmd_output('jcmd -l')
        if jcmd_list_output['status'] == 0:
            for jvm in jcmd_list_output['output'].splitlines():
                proc_info = jvm.split()
                pid = proc_info[0]
                main_class = proc_info[1]
                self._log_info(main_class)
                if main_class != 'jdk.jcmd/sun.tools.jcmd.JCmd':
                    # Get target process user to run jcmd as (or attaching to the VM may fail).
                    user_id = os.stat(f'/proc/{pid}').st_uid
                    user_name = pwd.getpwuid(user_id).pw_name
                    # Get a list of commands supported by the target VM.
                    jcmd_help_output = self.exec_cmd(f'/usr/bin/jcmd {pid} help',
                                                     runas=user_name,
                                                     timeout=self.get_option('jcmd_timeout'))
                    if jcmd_help_output['status'] == 0:
                        supported_cmds = set(jcmd_help_output['output'].splitlines()[2:])
                        for cmd in {'VM.version', 'VM.info', 'System.map'}.intersection(supported_cmds):
                            self.add_cmd_output([f'/usr/bin/jcmd {pid} {cmd}'],
                                                suggest_filename=f'{pid}_{main_class}_{cmd}',
                                                runas=user_name,
                                                timeout=self.get_option('jcmd_timeout'))
                    else:
                        self._log_error(
                            f'Failed to retrieve command list for "{pid}" (status={jcmd_help_output['status']}')
        else:
            self._log_error(f'Failed to retrieve a list of running JVMs (status={jcmd_list_output['status']}')

    def postproc(self):
        # Obfuscate the values of all java properties passed to the JVM
        # with '-D' on the command line in the output for VM.info, as they
        # may contain secrets (and we cannot really know which ones do).
        self.do_cmd_output_sub(
            "VM.info",
            r'-D([\w\d_.]*)=("([^"]*)"|\S+)',
            r'-D\1=********'
        )

# vim: set et ts=4 sw=4 :
