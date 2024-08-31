python manage.py run_twitter_bot


run `pipreqs .` to generate requirements.txt
run `black .` to format the code
run `isort .` to sort the imports
run `flake8 .` to check for linting errors
run `mypy .` to check for type errors
run `pytest .` to run the tests

run `python manage.py post_trend_tweet` to run the bot


Run `python manage.py post_trend_tweet` to post a tweet about a trending topic

In two seperate terminals, run the following commands to run the celery worker and beat
run `celery -A twitter_bot_project worker --loglevel=info` to run the celery worker
run `celery -A twitter_bot_project beat --loglevel=info` to run the celery beat
