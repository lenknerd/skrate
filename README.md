<img align="right" src="skrate/static/favicon.ico">

# Skrate

Use data mining to measure your skateboarding progression, and play
[SKATE](https://en.wikipedia.org/wiki/Game_of_Skate) against your past self.

David Lenkner
c. 2019

### Shout-outs

Skrate uses a PostgreSQL persistence layer via [docker container](https://hub.docker.com/_/postgres)
with a mounted directory for data for portability.

Skrate uses [Flask](https://www.palletsprojects.com/p/flask/) Python web service, and
[Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/en/2.x/) for model management.

## Instructions

### Running the Server

Install [docker](https://docs.docker.com/install/linux/docker-ce/ubuntu/), and build and run the
postgres database server by running `./run.sh` in the `persistence` folder. This will start a
background process.

Install python modules in `requirements.txt` via `pip install -r requirements.txt` (preferably in a
[virtual environment](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/)).

You can run tests via

	pytest ./tests/test_skrate.py

If you are running the server for the first time, also create necessary tables by running

	./run_skrate.py database-setup

This not only creates the model tables but also populates the `trick` table with some common
skateboarding tricks. New ones may be added, see "Adding New Tricks" below.

Optional - if you are inclined to look via SQL behind the "alchemy" part of SQLAlchemy, you can connect
and check out tables created, using [psql](http://www.postgresqltutorial.com/install-postgresql/) inside
the docker container. If so you can open that program via

	docker exec -it skrate-persistence psql postgresql://postgres:postgres_password@localhost:5432/postgres

You can also run this at any time later to manually explore data.

To actually start the service on your LAN, run

	./run_skrate.py serve -h 0.0.0.0

This will start the server on your local network. It is not a background task, so may want to use
for example [screen](https://linuxize.com/post/how-to-use-linux-screen/) and detach after run. To only
start service between docker and your local machine, leave off the 0.0.0.0.

Verbose output may be seen by adding the `--debug` argument after `skrate.py` for any command. Log 
messages go to stdout and `/tmp/skrate_service.log`. For more help you can run

	./run_skrate.py --help

for a list of general command, and for help on a specific command,

	./run_skrate.py [COMMAND] --help

### Skating

Pick any username, and browse to `http://<your-ip>:5000/<anyusername>` to log in (security is not a
thing in Skrate yet).

You don't have to start a game of SKATE - any time you miss or land trick, click "Miss" or "Land" by
the appropriate trick in the list to record the attempt and update your stats.

If you want to play SKATE against your past self, click "Start Game" near top of page. From there
simply follow instructions near the top of the page under "Current Game".

#### Skate Opponent Logic - SKATE Against Yourself

[SKATE](https://en.wikipedia.org/wiki/Game_of_Skate) is a common game in skateboarding, with rules
analogous to HORSE in basketball. For context see [BATB](https://theberrics.com/battle-at-the-berrics),
a widely-followed tournament with many top pro skateboarders playing SKATE against eachother.

In this app, your opponent in a game of SKATE is your past self, to measure whether you've progressed
(whether you land more tricks more reliably than you used to). Your opponents' likelihood of landing
any trick is determined by your own history of tries on that trick. The app algorithm takes a fixed
window of most recent tries of the trick, so as you progress your opponent also "gets better". The history
window length is defined in `_RECENT_ATTEMPTS_WINDOW_OLDEST` in [game\_logic.py](skrate/game_logic.py) -
roughly, increasing that means including "older versions" of oneself in a progression measure (have I
gotten better since last year, vs. better since last week).

If your opponent is challenging (choosing a trick to try), they will pick the trick with the best
probability of landing, with a randomization factor to sometimes take less reliable tricks and "mix up"
the game a bit, to get a different game every time. That randomization factor is controlled by
`_TRICK_RANDOM_SKIP` in [game\_logic.py](skrate/game_logic.py).
 
### Adding New Tricks

Trick definitions are in `tricks.py`. Each base trick is also labeled with whether it should be
duplicated in nollie/switch/fakie form. Most things should be but not everything. For instance,
we should have "Kickflip" as well as "Nollie Kickflip", "Switch Kickflip", and "Fakie Kickflip"
but we don't want to have both "Ollie" and "Nollie Ollie".

After adding to `tricks.py`, you can simply rerun

	./skrate.py database-setup

in order to load the changes. It will respect existing data and only add the new tricks.

### Migrating Data

The PostgreSQL docker container is run using a mounted docker volume called skrate-vol for postgres
data. Thus, the database is persisted between docker runs in a host directory, and can be easily
copied or migrated.

You can view the actual disk location of this data by running

	docker inspect skrate-vol

and noting the `Mountpoint` entry. You can then explore this directory (root permissions needed
since docker owns this location).
