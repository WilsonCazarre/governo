import subprocess
from typing import Optional

from constants import BASE_DIR
from utils import get_env_variable


class Server:
    def __init__(self, memory):
        self.memory = memory
        self.java_executable = get_env_variable("JAVA_EXECUTABLE")
        self.process: Optional[subprocess.Popen] = subprocess.Popen(
            ['dir'], shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE
        )
        self.minecraft_executable = 'server.jar'
        self.server_name = ''
        self.paths = []
        self.discover_paths()

    def run(self, version_idx):
        if self.process.poll() == 0:
            w_dir = self.paths[version_idx]
            command = [self.java_executable,
                       f'-Xmx{self.memory}',
                       f'-Xms{self.memory}',
                       '-jar',
                       f'{w_dir}/{self.minecraft_executable}',
                       'nogui']
            with open('server_log.txt', 'w') as log_file:
                self.process = subprocess.Popen(command,
                                                stdout=log_file,
                                                stderr=log_file,
                                                stdin=subprocess.PIPE,
                                                text=True,
                                                universal_newlines=True,
                                                cwd=w_dir)
                print(f'Started new process: {self.process}')

    def discover_paths(self):
        versions_folder = BASE_DIR / 'versions'
        new_paths = [
            p.resolve() for p in versions_folder.iterdir() if p.is_dir()
        ]
        self.paths = new_paths
        return [p.name for p in self.paths]

    def stop(self):
        if self.process.poll() is None:
            self.process.communicate('/stop\n')
            print(f'Stopping process: {self.process}')


if __name__ == '__main__':
    server = Server('1024M')
    server.discover_paths()
    server.run(0)
