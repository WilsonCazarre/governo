import atexit
import subprocess
from typing import Optional

import discord
from discord.ext import commands
from discord.ext.commands import errors

from utils.constants import BASE_DIR, SERVER_HOST_NAME, DISCORD_MAX_BODY_LENGTH
from utils.functions import get_env_variable


class MinecraftServer:
    def __init__(self, memory):
        self.memory = memory
        self.java_executable = get_env_variable("JAVA_EXECUTABLE")
        self.process: Optional[subprocess.Popen] = subprocess.Popen(
            ["dir"], shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE
        )
        self.minecraft_executable = "server.jar"
        self.server_name = ""
        self.paths = []
        self.discover_paths()

    def run(self, version_idx):
        if self.process.poll() == 0:
            w_dir = self.paths[version_idx]
            self.server_name = w_dir.name
            command = [
                self.java_executable,
                f"-Xmx{self.memory}",
                f"-Xms{self.memory}",
                "-jar",
                f"{w_dir}/{self.minecraft_executable}",
                "nogui",
            ]
            with open("../server_log.txt", "w") as log_file:
                self.process = subprocess.Popen(
                    command,
                    stdout=log_file,
                    stderr=log_file,
                    stdin=subprocess.PIPE,
                    text=True,
                    universal_newlines=True,
                    cwd=w_dir,
                )
                print(f"Started new process: {self.process}")

    def discover_paths(self):
        versions_folder = BASE_DIR / "versions"
        new_paths = [
            p.resolve() for p in versions_folder.iterdir() if p.is_dir()
        ]
        self.paths = new_paths
        return [p.name for p in self.paths]

    def stop(self):
        if self.process.poll() is None:
            self.process.communicate("/stop\n")
            print(f"Stopping process: {self.process}")

    def execute_command(self, cmd: str):
        if self.process.poll() is None:
            self.process.communicate(f"{cmd}\n")


class MinecraftCog(commands.Cog):
    def __init__(self, bot, allocated_memory="4096M"):
        self.bot = bot
        self.mc_server = MinecraftServer(memory=allocated_memory)

    @commands.group(name="mine", pass_context=True)
    async def minecraft_group(self, ctx: commands.Context):
        """
        Lists all the available servers.
        """
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="Minecraft versions",
                description="This are the available servers to run",
            )
            servers = self.mc_server.discover_paths()
            for s in range(len(servers)):
                embed.add_field(
                    name=servers[s], value=f"ID: {s + 1}", inline=False
                )
            await ctx.send(embed=embed)

    @minecraft_group.command(pass_context=True)
    async def run_server(self, ctx: commands.Context, server_id: int):
        """
        Runs the server with the specified ID.
        A list of the available server can be retrieved with the "list" command.
        This command will always try to stop a running server before starting a new
        one.
        """
        self.mc_server.stop()
        self.mc_server.run(server_id - 1)
        server_name = self.mc_server.paths[server_id - 1].name
        await self.bot.change_presence(
            activity=discord.Game(name=f"Hosting {server_name}")
        )
        await ctx.send(
            embed=discord.Embed(
                title=f"{server_name} is yours",
                description=f"Your server is currently running and can be accessed "
                f"**{SERVER_HOST_NAME}**",
            )
        )

    @run_server.error
    async def on_run_server_error(
        self, ctx: commands.Context, error: errors.CommandError
    ):
        if isinstance(error, errors.MissingRequiredArgument):
            await ctx.send("You need to specify a server ID")
        else:
            raise error

    @minecraft_group.command(name="cmd", pass_context=True)
    async def execute_command(self, ctx: commands.Context, *args):
        """
        Sends the input to the minecraft server as a admin command.

        Writes the args to the STDIN of the running Java process.
        """
        await ctx.send("hey")
        if self.mc_server.process.poll() is None:
            command = " ".join(args)
            await ctx.send(f"Executing [{command}] on the server")
            self.mc_server.execute_command(command)

    @minecraft_group.command(pass_context=True)
    async def stop_server(self, ctx: commands.Context):
        """
        Stops the current running server.
        """
        if self.mc_server.process.poll() is None:
            await ctx.send("Shutting down internal server...")
            self.mc_server.stop()
            await self.bot.change_presence(status=discord.Status.idle)
            await ctx.send("Server was stopped")
        else:
            await ctx.send("There's no server running...")

    @minecraft_group.command(pass_context=True)
    async def log_server(self, ctx: commands.Context):
        """
        Returns the java process log of the running server.
        """
        if self.mc_server.process.poll() is None:
            with open("server_log.txt", "r") as log_file:
                message = ""
                for line in log_file.readlines():
                    if len(message) + len(line) >= DISCORD_MAX_BODY_LENGTH:
                        await ctx.send(f"```{message}```")
                        message = ""
                    message += line

                if len(message) == 0:
                    await ctx.send("Nothing to log yet")
                else:
                    await ctx.send(f"```{message}```")
        else:
            await ctx.send(
                embed=discord.Embed(
                    title="No server running",
                    description=f"You can start one by running {ctx.prefix}run_server <server_id>",
                )
            )

    @atexit.register
    def goodbye(self):
        print("Trying to stop servers...")
        if self.mc_server.process.poll() is None:
            self.mc_server.stop()
