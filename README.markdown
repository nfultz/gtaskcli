gtaskcli
=======

`gtaskcli` is a command-line todo list manager for people that want to *finish* tasks,
not organize them.

It provides a stable, sane CLI for Google Tasks based on [sjl/t](/sjl/t).

Why fork t?
------

  * It Does the Simplest Thing That Could Possibly Work
  * It's Flexible


Installing gtaskcli
------------

```
pip install git+https://github.com/nfultz/gtaskcli

```


Using gtaskcli
-------

`gtaskcli` is quick and easy to use.

### Add a Task

To add a task, use `gtaskcli [task description]`:

    $ gtaskcli Clean the apartment.
    $ gtaskcli Write chapter 10 of the novel.
    $ gtaskcli Buy more beer.
    $

### List Your Tasks

Listing your tasks is even easier -- just use `gtaskcli`:

    $ gtaskcli
    9  - Buy more beer.
    30 - Clean the apartment.
    31 - Write chapter 10 of the novel.
    $

`t` will list all of your unfinished tasks and their IDs.

### Finish a Task

After you're done with something, use `t -f ID` to finish it:

    $ gtaskcli -f 31
    $ gtaskcli
    9  - Buy more beer.
    30 - Clean the apartment.
    $

### Edit a Task

Sometimes you might want to change the wording of a task.  You can use
`t -e ID [new description]` to do that:

    $ gtaskcli -e 30 Clean the entire apartment.
    $ gtaskcli
    9  - Buy more beer.
    30 - Clean the entire apartment.
    $

Yes, nerds, you can use sed-style substitution strings:

    $ gtaskcli -e 9 /more/a lot more/
    $ gtaskcli
    9  - Buy a lot more beer.
    30 - Clean the entire apartment.
    $

Tips and Tricks
---------------

`t` might be simple, but it can do a lot of interesting things.

### Count Your Tasks

Counting your tasks is simple using the `wc` program:

    $ t | wc -l
          2
    $

### Multiple Lists

`gtaskcli`, like `t` before it, uses the CWD for the default task list
if none are specified explicitly. You can set up shell aliases to override
this behavior if you like.

Problems, Contributions, Etc
----------------------------

`gtaskcli` was hacked together in a couple of nights to fit my needs.  If you use it
and find a bug, please let me know.

If you want to request a feature feel free, but remember that `t` is meant to
be simple.  If you need anything beyond the basics you might want to look at
[todo.txt][] or [TaskWarrior][] instead.  They're great tools with lots of
bells and whistles.

If you want to contribute code to `t`, that's great!
