import shutil
from datetime import datetime
from typing import Optional

from discord.ext import commands, tasks
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from constants import BASE_DIR
from server import Server


class Backups(commands.Cog):
    def __init__(self, bot, server: Server):
        self.bot: commands.Bot = bot
        self.bot.remove_command("help")
        self.governo_server = server
        self.drive: Optional[GoogleDrive] = None
        self.create_service()
        self.backup_running_server.start()

    def create_service(self):
        gauth = GoogleAuth()
        gauth.LocalWebserverAuth()

        self.drive = GoogleDrive(gauth)

    def get_backup_folder(self) -> str:
        files = self.drive.ListFile({"q": "title='backups'"}).GetList()
        try:
            return files[0].get("id")
        except IndexError:
            print(
                "Backup folder not found on Google Drive, "
                "creating a new one"
            )

        folder_metadata = {
            "title": "backups",
            "mimeType": "application/vnd.google-apps.folder",
        }
        file = self.drive.CreateFile(metadata=folder_metadata)
        file.Upload()
        return file.get("id")

    @tasks.loop(minutes=2)
    async def backup_running_server(self):
        if self.governo_server.process.poll() is None:
            server_name = self.governo_server.server_name
            print(f"Starting server backup for: '{server_name}'")

            self.governo_server.execute_command(
                "/say Starting Server Backup... "
                "I may lagged out, and I'm sorry"
            )

            backup_root = self.get_backup_folder()
            world_folders = self.discover_world_folders()
            world = [w for w in world_folders if w.parent.name == server_name][
                0
            ]
            if world:
                folders = self.drive.ListFile(
                    {
                        "q": f"'{backup_root}' "
                        f"in parents and trashed=false and title='{server_name}'"
                    }
                ).GetList()
                try:
                    world_backup = folders[0]
                except IndexError:
                    folder_metadata = {
                        "title": server_name,
                        "mimeType": "application/vnd.google-apps.folder",
                        "parents": [{"id": backup_root}],
                    }
                    world_backup = self.drive.CreateFile(
                        metadata=folder_metadata
                    ).Upload()

                folder_id = world_backup.get("id")
                file_title = datetime.now().strftime("%Y%m%d - %H%M")
                zip_world = shutil.make_archive(file_title, "zip", world)
                file_metadata = {
                    "title": f"{file_title}.zip",
                    "parents": [{"id": folder_id}],
                }
                backup_file = self.drive.CreateFile(metadata=file_metadata)
                backup_file.SetContentFile(zip_world)
                backup_file.Upload()
        else:
            print("No server is running, skipping backup")

    @staticmethod
    def discover_world_folders():
        """
        Returns all the minecraft versions with a "world" folder.
        """
        versions_folder = BASE_DIR / "versions"
        paths = [p.resolve() for p in versions_folder.iterdir() if p.is_dir()]
        world_folders = []
        for p in paths:
            world_folder = p / "world"
            if world_folder.exists():
                world_folders.append(world_folder)
        return world_folders
