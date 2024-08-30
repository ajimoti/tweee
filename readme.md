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


run `pipreqs .` to generate requirements.txt
run `black .` to format the code
run `isort .` to sort the imports
run `flake8 .` to check for linting errors
run `mypy .` to check for type errors
run `pytest .` to run the tests


Run `python manage.py post_trend_tweet` to post a tweet about a trending topic

In two seperate terminals, run the following commands to run the celery worker and beat
run `celery -A twitter_bot_project worker --loglevel=info` to run the celery worker
run `celery -A twitter_bot_project beat --loglevel=info` to run the celery beat
