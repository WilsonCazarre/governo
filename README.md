# Governo
A discord bot to control minecraft servers


## How to contribute

1 - Clone the repo and navigate to it
```
git clone https://github.com/WilsonCazarre/governo.git
cd governo
```

2 - Create and activate a new venv
```
python -m venv venv
venv/Scripts/activate.bat
```

3 - Install the dependencies
```
python -m pip install -r requirements.txt
```

4 - Create a new `.env` file
```env
TOKEN=your discord bot token here
```

5 - Run the bot
```
python bot.py
```


## How to add server versions

In order to serve minecraft versions you need to create a folder in the root of the project called `versions`.
The bot will see each folder inside `versions` as a minecraft server and will try to run the file `server.jar` when that specific server is requested.
