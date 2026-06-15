# This file is part of the sos project: https://github.com/sosreport/sos
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# version 2 of the GNU General Public License.
#
# See the LICENSE file in the source distribution for further information.

from sos.report.plugins import PluginOpt, Plugin, IndependentPlugin


class Jvm(Plugin, IndependentPlugin):
    """
    This plugin collects information about instances of the Java Virtual Machine
    running on the system at the time of the report.

    This information is captured by using the 'jcmd' JDK utility with a set number
    of predefined commands. Data collection can be extended by passing extra jcmd
    commands as arguments.
    """

    short_desc = 'Collect information about running Java Virtual Machines'

    plugin_name = 'jvm'
    profiles = ('java')
    commands = ('jcmd',)
    # files = ('/usr/bin/jcmd',)

    option_list = [
        PluginOpt('extraCmds', default='',
                  desc='Extra jcmd commands to run for all running JVMs, separated by a space')
    ]

    def setup(self):
        cmds = ['VM.info', 'System.map'] + self.sanitize_commands(self.get_option('extraCmds'))
        jvms = self.collect_cmd_output('jcmd')
        if jvms['status'] == 0:
            for jvm in jvms['output'].splitlines()[1:]:
                pid = jvm.split()
                if pid[1] != 'jdk.jcmd/sun.tools.jcmd.JCmd':
                    stat = self.collect_cmd_output(f'stat -c "%u" /proc/{pid[1]}')
                    if stat['status'] == 0:
                        uid = jvms['output'].splitlines()[1:]
                        id = self.collect_cmd_output(f'id -un {uid}')
                        if id['status'] == 0:
                            uname = id['output'].splitlines()[1:]
                            for cmd in cmds:
                                self.add_cmd_output([
                                    f'jcmd {pid[0]} {cmd}'
                                ],
                                    suggest_filename=f'{pid[0]}_{pid[1]}_{cmd}',
                                    runas=uname,
                                    timeout=30)

        def sanitize_commands(self, cmds: str):
            valid_cmds = ('Compiler.CodeHeap_Analytics',
                          'Compiler.codecache',
                          'Compiler.codelist',
                          'Compiler.directives_add',
                          'Compiler.directives_clear',
                          'Compiler.directives_print',
                          'Compiler.directives_remove',
                          'Compiler.memory',
                          'Compiler.perfmap',
                          'Compiler.queue',
                          'GC.class_histogram',
                          'GC.finalizer_info',
                          'GC.heap_dump',
                          'GC.heap_info',
                          'GC.run',
                          'GC.run_finalization',
                          'JFR.check',
                          'JFR.configure',
                          'JFR.dump',
                          'JFR.start',
                          'JFR.stop',
                          'JFR.view',
                          'JVMTI.agent_load',
                          'JVMTI.data_dump',
                          'ManagementAgent.start',
                          'ManagementAgent.start_local',
                          'ManagementAgent.status',
                          'ManagementAgent.stop',
                          'System.dump_map',
                          'System.map',
                          'System.native_heap_info',
                          'System.trim_native_heap',
                          'Thread.dump_to_file',
                          'Thread.print',
                          'Thread.vthread_pollers',
                          'Thread.vthread_scheduler',
                          'VM.cds',
                          'VM.class_hierarchy',
                          'VM.classes',
                          'VM.classloader_stats',
                          'VM.classloaders',
                          'VM.command_line',
                          'VM.dynlibs',
                          'VM.events',
                          'VM.flags',
                          'VM.info',
                          'VM.log',
                          'VM.metaspace',
                          'VM.native_memory',
                          'VM.set_flag',
                          'VM.stringtable',
                          'VM.symboltable',
                          'VM.system_properties',
                          'VM.systemdictionary',
                          'VM.uptime',
                          'VM.version')
            output = []
            for cmd in cmds.split():
                if cmd in valid_cmds:
                    output.append(cmd)
                else:
                    self._log_warn(f'{cmd} is not a valid jcmd command')
            return output

    # vim: set et ts=4 sw=4 :
