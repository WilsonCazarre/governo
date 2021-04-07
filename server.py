import subprocess
from typing import Optional

from constants import BASE_DIR
from utils import get_env_variable


class Server:
    def __init__(self, memory):
        self.memory = memory
        self.java_executable = get_env_variable("JAVA_EXECUTABLE")
        self.status = 'stopped'
        self.process: Optional[subprocess.Popen] = None
        self.minecraft_executable = 'server.jar'
        self.server_name = ''
        self.paths = []
        self.discover_paths()

    def run(self, version_idx):
        if not self.process:
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
                                                text=True,
                                                universal_newlines=True,
                                                cwd=w_dir)
            self.status = 'running'

    def discover_paths(self):
        versions_folder = BASE_DIR / 'versions'
        new_paths = [
            p.resolve() for p in versions_folder.iterdir() if p.is_dir()
        ]
        self.paths = new_paths
        return [p.name for p in self.paths]

    def stop(self):
        if self.process:
            self.process.terminate()
            self.process = None

    def log_status(self):
        if self.process:
            return self.process.stdout.readline()


if __name__ == '__main__':
    server = Server('1024M')
    server.discover_paths()
    server.run(0)
