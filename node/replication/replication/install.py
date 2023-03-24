'''Python module to connect to a future node and launch the installation of a DVIC node.'''

import subprocess
import os
#! https://stackoverflow.com/questions/19900754/python-subprocess-run-multiple-shell-commands-over-ssh
#! Has to check some security issues with this module

path = '/home/wanikatako/'

class InstallationHandler():
    def __init__(self, usr : str = 'root', ip : str = None) -> None:
        self.usr = usr
        self.ip = ip
        self.ssh_connection = None

    def _start_connection(self) -> subprocess.Popen :
        '''.Start the ssh connection to the node.'''
        ssh_command = f'ssh {self.usr}@{self.ip}'
        self.ssh_connection = subprocess.Popen(ssh_command,
                                    stdin=subprocess.PIPE, 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE,
                                    shell=True) #! It seems that shell=False is more secure than shell=True and avoid shell injection
        # Write a log into a file to ensure that the connection is established
        # self.ssh_connection.stdin.write(b'echo "Connection established" > /home/wanikatako/log.txt\n')
        # self.ssh_connection.stdin.flush()
        return self.ssh_connection

    def _copy_installation_script(self) -> None:
        '''Copy the installation script to the node.'''

        #! Remove unessecary code
        path_to_dir = os.path.dirname(os.path.abspath(__file__))
        #remove the last part of the path to get the path to the ressources folder
        path_to_isntall_script = os.path.dirname(path_to_dir) + '/resources' +  '/install_script.sh'
        #! End of unessecary code

        scp_command = f'scp ../resources/install_script.sh {self.usr}@{self.ip}:{path}\n'
        scp_connection = subprocess.run(scp_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

    def _run_command_ssh(self, command : str) -> None:
        '''Run a command on the node.'''
        command += '\n'
        print(command.encode())
        self.ssh_connection.stdin.write(command.encode())
        self.ssh_connection.stdin.flush()


        
     
    def _close_connection(self) -> None :
        '''Close the ssh connection to the node.'''
        # Send a SIGTERM to the process
        self.ssh_connection.terminate()
        print("Connection closed")

    def installation(self) -> None:
        '''Start the installation of the node.'''
        print("Copying the installation script to the node...")
        self._copy_installation_script()
        print("Initializing connection...")
        self.ssh_connection = self._start_connection()
        print(f"Connection established as {self.usr}")
        print("Starting the installation...")
        self._run_command_ssh(f'bash {path}install_script.sh')
        print("Installation finished")
        self._close_connection()
        
        
        

if __name__ == '__main__':
    usr = InstallationHandler('wanikatako', 'localhost')
    # usr.installation()
    usr._start_connection()
    usr._run_command_ssh('bash /home/wanikatako/install_script.sh')
