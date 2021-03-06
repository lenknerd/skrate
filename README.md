<img align="right" src="skrate/static/favicon.ico">

# Skrate

Use data mining to measure your skateboarding progression, and play
[SKATE](https://en.wikipedia.org/wiki/Game_of_Skate) against your past self.

David Lenkner
c. 2019

## Server Instructions

### Installation

Install [docker](https://docs.docker.com/install/linux/docker-ce/ubuntu/), used for running the
Skrate database service. Install [Python 3.6 or later](https://www.python.org/downloads/).

Install the Skrate Python package and executable via

	python3 -m pip install skrate

### Running Server

Start the local Skrate database service via

	run_skrate database-run

If you are running the server for the first time, also create necessary tables by running

	run_skrate database-setup

This not only creates the model tables but also populates the `trick` table with some common
skateboarding tricks. New ones may be added, see "Adding New Tricks" below.

Finally to start the Skrate web service,

	run_skrate serve [-h 0.0.0.0] [-p <port-number>]

The `-h` option will start the server on your local network as opposed to your machine only.
Default flask port is 5000.

Log messages go to stdout and `/tmp/skrate_service.log`. For further help see

	run_skrate --help

## Skating

Pick any username, and browse to `http://<your-server>:5000/<anyusername>` to log in (security is not a
thing in Skrate yet).

You don't have to start a game of SKATE - any time you miss or land trick, click "Miss" or "Land" by
the appropriate trick in the list to record the attempt and update your stats.

If you want to play SKATE against your past self, click the "New Game" button. After that, updates
and instructions on what to do will appear in the game feed above the "New Game" button.

### Opponent Logic - SKATE Against Yourself

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

If your AI opponent is challenging (choosing a trick to try), they will pick the trick with the best
probability of landing, with a randomization factor to sometimes take less reliable tricks and "mix up"
the game a bit, to get a different game every time. That randomization factor is controlled by
`_TRICK_RANDOM_SKIP` in [game\_logic.py](skrate/game_logic.py).

## Development

Pull the repo, install requirements in `requirements.txt`, and have at it!

Unit tests can be run via

	pytest tests/test_skrate.py
 
### Adding New Tricks

Trick definitions are in `tricks.py`. Each base trick is also labeled with whether it should be
duplicated in nollie/switch/fakie form. Most things should be but not everything. For instance,
we should have "Kickflip" as well as "Nollie Kickflip", "Switch Kickflip", and "Fakie Kickflip"
but we don't want to have both "Ollie" and "Nollie Ollie".

After adding to `tricks.py`, you can simply rerun

	run_skrate database-setup

in order to load the changes. It will respect existing data and only add the new tricks.

### Getting at "Raw Data"

If you are inclined to further analyze Skrate data on tricks, attempts, and games, or
inspect the schema auto-generated by SQLAlchemy, you may be interested in the raw SQL interface
to Skrate data. One way to access that is via 
[psql](http://www.postgresqltutorial.com/install-postgresql/) inside the docker container,

	docker exec -it skrate-persistence psql postgresql://postgres:postgres_password@localhost:5432/postgres

### Migrating Data

The PostgreSQL docker container is run using a mounted docker volume called skrate-vol for postgres
data. Thus, the database is persisted between docker runs in a host directory, and can be easily
copied or migrated (e.g. switching to new host machine w/o losing data).

You can view the actual disk location of this data by running

	docker inspect skrate-vol

and noting the `Mountpoint` entry. You can then explore this directory (root permissions needed
since docker owns this location). The volume name `skrate-vol` is default, any volume name may
be used by setting non-default `--volume` argument to `run_skrate database-run`.

## Acknowledgements

Skrate relies on [Flask](https://www.palletsprojects.com/p/flask/) for web service,
[Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/en/2.x/) for model management,
[Flask-Testing](https://pythonhosted.org/Flask-Testing/) with
[pytest](https://docs.pytest.org/en/latest/) for unit testing.

Also appreciated is the convenient [Postgres Docker image](https://hub.docker.com/_/postgres)
used for the Skrate data persistence layer.
