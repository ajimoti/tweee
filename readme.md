python manage.py run_twitter_bot


Running the Bot in the Background
Use screen or tmux to run the bot script in the background without interfering with your Django app.

Install screen (if not already installed)
```
sudo apt-get install screen
```

Start a New Screen Session
```
screen -S twitter-bot
```
Run the Bot Script
```
python manage.py run_twitter_bot
```

To detach from the screen session and keep the bot running, press Ctrl+A followed by D.

To reattach to the screen session later
screen -r twitter-bot# tweee
