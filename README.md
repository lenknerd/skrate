# Skrate

Use data mining to measure your skateboarding progression, and play
[SKATE](https://en.wikipedia.org/wiki/Game_of_Skate) against your past self.

David Lenkner
c. 2019

### Shout-Outs

Skrate uses a PostgreSQL persistence layer via [docker container](https://hub.docker.com/_/postgres)
with a mounted directory for data for portability.

Skrate uses [Flask](https://www.palletsprojects.com/p/flask/) Python web service, and
[Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/en/2.x/) for model management.

## Instructions

### Running the Server

Install [docker](https://docs.docker.com/install/linux/docker-ce/ubuntu/), and build and run the
postgres database server by running `./run.sh` in the `persistence` folder. Install python modules
in `requirements.txt` (preferably in venv).

If you are running it for the first time, also create necessary tables by running

	./skrate.py database-setup

This not only creates the model tables but also populates the `trick` table with some common
skateboarding tricks. New ones may be added, see [Adding New Tricks](### Adding New Tricks) below.

Optional - if you are inclined to look via SQL behind the "alchemy" part of SQLAlchemy, you can connect
and check out tables created, using [psql](http://www.postgresqltutorial.com/install-postgresql/) inside
the docker container. If so run

	docker exec -it skrate-persistence psql postgresql://postgres:postgres_password@localhost:5432/postgres

You can also run this at any time later to manually explore data.

To actually start the service on your LAN, run

	./skrate.py serve -h 0.0.0.0

This will start the server on your local network. It is not a background task, so may want to use
for example [screen](https://linuxize.com/post/how-to-use-linux-screen/) and detach after run. To only
start service between docker and your local machine, leave off the 0.0.0.0.

Verbose output may be seen by adding the `--debug` argument after `skrate.py` for any command. Log 
messages go to stdout and `/tmp/skrate_service.log`. For more help you can run

	./skrate.py --help

for a list of general command, and for help on a specific command,

	./skrate.py [COMMAND] --help

### Skating

Pick any username, and browse to `http://<your-ip>:5000/<anyusername>` to log in (security is not a
thing in Skrate yet).

You don't have to start a game of SKATE - any time you miss or land trick, click "Miss" or "Land" by
the appropriate trick in the list to record the attempt and update your stats.

If you want to play SKATE against your past self, click "Start Game" near top of page. From there
simply follow instructions and read the display below. It may tell you any of the following

* "Your lead" - your turn to try any trick you want and your opponent has to land
* "Your follow-up, try a (whatever)" - your opponent led and landed some trick, you have to try it

When you land or miss a trick, enter Land or Miss in the corresponding trick in the trick list.

Status updates on your opponents tricks also will be shown including

* "Opponent Matched your (whatever)" - you led, landed, opponent landed same trick, back to your lead
* "Opponent Challenged by Landing a (whatever)" - opponent landed a trick when they had lead
* "Opponent Missed a (whatever)" - opponent missed a trick either with or without lead
 
### Adding New Tricks

Trick definitions are in `tricks.py`. Each base trick is also labeled with whether it should be
duplicated in nollie/switch/fakie form. Most things should be but not everything. For instance,
we should have "Kickflip" as well as "Nollie Kickflip", "Switch Kickflip", and "Fakie Kickflip"
but we don't want to have both "Ollie" and "Nollie Ollie".

After adding to `tricks.py`, you can simply rerun `./skrate.py database-setup` in order to write
the changes. It will respect existing data and only add the new tricks.

### Migrating Data

The PostgreSQL docker container is run using a mounted docker volume called skrate-vol for postgres
data. Thus, the database is persisted between docker runs in a host directory, and can be easily
copied or migrated.

You can view the actual disk location of this data by running

	docker inspect skrate-vol

and noting the `Mountpoint` entry. You can then explore this directory (root permissions needed
since docker owns this location).
