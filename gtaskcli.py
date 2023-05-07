#!/usr/bin/env python
import os, re, sys, hashlib

__API_CLIENT_ID__ = '114962348880-l5k29r3802g1ckni464464f5rkd68rat.apps.googleusercontent.com'
__API_CLIENT_SECRET__ = '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'


"""gtaskcli is for people that want do things, not organize their tasks.
With google tasks."""


from operator import itemgetter
from optparse import OptionParser, OptionGroup


class InvalidTaskfile(Exception):
    """Raised when the path to a task file already exists as a directory."""
    pass

class AmbiguousPrefix(Exception):
    """Raised when trying to use a prefix that could identify multiple tasks."""
    def __init__(self, prefix):
        super(AmbiguousPrefix, self).__init__()
        self.prefix = prefix

class UnknownPrefix(Exception):
    """Raised when trying to use a prefix that does not match any tasks."""
    def __init__(self, prefix):
        super(UnknownPrefix, self).__init__()
        self.prefix = prefix

def _prefixes(tasks):
    """Annotates a list of tasks with a prefix in O(n) time.

    Each prefix will be the shortest possible substring of the ID that
    can uniquely identify it among the given group of IDs.

    If an ID of one task is entirely a substring of another task's ID, the
    entire ID will be the prefix.
    """
    ids = [task["id"].lower() for task in tasks]
    ps = {}
    for id in ids:
        id_len = len(id)
        for i in range(1, id_len+1):
            # identifies an empty prefix slot, or a singular collision
            prefix = id[:i]
            if (not prefix in ps) or (ps[prefix] and prefix != ps[prefix]):
                break
        if prefix in ps:
            # if there is a collision
            other_id = ps[prefix]
            for j in range(i, id_len+1):
                if other_id[:j] == id[:j]:
                    ps[id[:j]] = ''
                else:
                    ps[other_id[:j]] = other_id
                    ps[id[:j]] = id
                    break
            else:
                ps[other_id[:id_len+1]] = other_id
                ps[id] = id
        else:
            # no collision, can safely add
            ps[prefix] = id
    ps = dict(zip(ps.values(), ps.keys()))

    # save back on to task objects
    for task in tasks:
        task["prefix"] = ps[task["id"].lower()]

def build_service():
    import httplib2

    from apiclient.discovery import build
    from apiclient.errors import HttpError

    from oauth2client import client
    from oauth2client.file import Storage
    from oauth2client import tools

    client_secrets = "/home/nfultz/downloads/client_secret_114962348880-l5k29r3802g1ckni464464f5rkd68rat.apps.googleusercontent.com.json"

    scope= "https://www.googleapis.com/auth/tasks"

    flow = client.flow_from_clientsecrets(
        client_secrets, scope=scope, message=client_secrets
    )

    storage = Storage(os.path.expanduser('~/.gtcli_oauth'))

    credentials = storage.get()
    if credentials is None or credentials.invalid:
        credentials = tools.run_flow(flow, storage)

    auth_http = credentials.authorize(httplib2.Http())

    task_service = build(serviceName='tasks', version='v1', http=auth_http)
    return task_service

class TaskDict(object):
    """A set of tasks, both finished and unfinished, for a given list.

    The list's files are read from gtasks when the TaskDict is initialized.

    """
    def __init__(self, taskdir=None):
        """Initialize by reading the task files, if they exist."""
        self.service = build_service()

        if os.path.isdir(taskdir):
            taskdir = os.path.abspath(taskdir)
            taskdir = taskdir.replace(os.path.expanduser("~"), "~")

        self.taskdir = taskdir

        self.id = None
        self.tasks = None

        tasklists = self.service.tasklists().list().execute()

        if not taskdir:
            tl = next(iter(tasklists["items"]))
        else:
            for tl in tasklists["items"]:
                if tl["title"] == taskdir:
                    break
            else:
                pass

        self.id = tl["id"]
        self.tasks = self.service.tasks().list(tasklist=self.id).execute()



    def __getitem__(self, prefix):
        """Return the unfinished task with the given prefix.

        If more than one task matches the prefix an AmbiguousPrefix exception
        will be raised, unless the prefix is the entire ID of one task.

        If no tasks match the prefix an UnknownPrefix exception will be raised.

        """
        matched = {task["id"].lower(): task for task in self.tasks["items"] if task["id"].lower().startswith(prefix)}
        if len(matched) == 1:
            return matched.popitem()[1]
        elif len(matched) == 0:
            raise UnknownPrefix(prefix)
        elif prefix in matched:
            return matched[prefix]
        else:
            raise AmbiguousPrefix(prefix)

    def add_task(self, text, verbose, quiet):
        """Add a new, unfinished task with the given summary text."""

        if self.id is None:
            tasklist = self.service.tasklists().insert(body={"title":self.taskdir}).execute()
            self.id = tasklist["id"]
            self.tasks = {"items":[]}


        request = self.service.tasks().insert(tasklist=self.id, body={"title": text})
        task = request.execute()

        if not quiet:
            if verbose:
                print(task["id"])
            else:
                self.tasks["items"].append(task)
                _prefixes(self.tasks["items"])
                print(task["prefix"])

    def edit_task(self, prefix, text):
        """Edit the task with the given prefix.

        If more than one task matches the prefix an AmbiguousPrefix exception
        will be raised, unless the prefix is the entire ID of one task.

        If no tasks match the prefix an UnknownPrefix exception will be raised.

        """
        task = self[prefix]
        if text.startswith('s/') or text.startswith('/'):
            text = re.sub('^s?/', '', text).rstrip('/')
            find, _, repl = text.partition('/')
            text = re.sub(find, repl, task['text'])
        request = self.service.tasks().patch(tasklist=self.id, task=task["id"], body={"title": text})
        request.execute()

    def finish_task(self, prefix):
        """Mark the task with the given prefix as finished.

        If more than one task matches the prefix an AmbiguousPrefix exception
        will be raised, if no tasks match it an UnknownPrefix exception will
        be raised.

        """
        task = self[prefix]
        request = self.service.tasks().patch(tasklist=self.id, task=task["id"], body={"status": "completed"})
        request.execute()

    def remove_task(self, prefix):
        """Remove the task from tasks list.

        If more than one task matches the prefix an AmbiguousPrefix exception
        will be raised, if no tasks match it an UnknownPrefix exception will
        be raised.

        """
        task = self[prefix]
        request = self.service.tasks().delete(tasklist=self.id, task=task["id"])
        request.execute()


    def print_list(self, kind='needsAction', verbose=False, quiet=False, grep=''):
        """Print out a nicely formatted list of unfinished tasks."""
        if not self.id: return
        tasks = self.tasks["items"]
        label = 'id'
        sep = '' if quiet else ' - '

        if not verbose:
            label = "prefix"
            _prefixes(tasks)

        plen = max(map(lambda t: len(t[label]), tasks)) if tasks else 0

        tasks.sort(key=itemgetter(label))

        p = ''
        for task in tasks:
            if kind != task["status"]:
                continue
            if not grep.lower() in task['title'].lower():
                continue
            if not quiet:
                p = task[label].ljust(plen)
            print(p, task['title'], sep=sep)


def _die(message):
    sys.stderr.write('error: %s\n' % message)
    sys.exit(1)

def _build_parser():
    """Return a parser for the command-line interface."""
    usage = "Usage: %prog [-t DIR] [-l LIST] [options] [TEXT]"
    parser = OptionParser(usage=usage)

    actions = OptionGroup(parser, "Actions",
        "If no actions are specified the TEXT will be added as a new task.")
    actions.add_option("-e", "--edit", dest="edit", default="",
                       help="edit TASK to contain TEXT", metavar="TASK")
    actions.add_option("-f", "--finish", dest="finish",
                       help="mark TASK as finished", metavar="TASK")
    actions.add_option("-r", "--remove", dest="remove",
                       help="Remove TASK from list", metavar="TASK")
    parser.add_option_group(actions)

    config = OptionGroup(parser, "Configuration Options")
    config.add_option("-t", "--task-list", dest="taskdir", default="",
                      help="work on the lists named LIST", metavar="LIST")
    config.add_option("-d", "--delete-if-empty",
                      action="store_true", dest="delete", default=False,
                      help="delete the task file if it becomes empty")
    parser.add_option_group(config)

    output = OptionGroup(parser, "Output Options")
    output.add_option("-g", "--grep", dest="grep", default='',
                      help="print only tasks that contain WORD", metavar="WORD")
    output.add_option("-v", "--verbose",
                      action="store_true", dest="verbose", default=False,
                      help="print more detailed output (full task ids, etc)")
    output.add_option("-q", "--quiet",
                      action="store_true", dest="quiet", default=False,
                      help="print less detailed output (no task ids, etc)")
    output.add_option("--done",
                      action="store_true", dest="done", default=False,
                      help="list done tasks instead of unfinished ones")
    parser.add_option_group(output)

    return parser

def _main():
    """Run the command-line interface."""
    (options, args) = _build_parser().parse_args()

    td = TaskDict(taskdir=options.taskdir)
    text = ' '.join(args).strip()
#
#    if '\n' in text:
#        _die('task text cannot contain newlines')
#
    try:
        if options.finish:
            td.finish_task(options.finish)
        elif options.remove:
            td.remove_task(options.remove)
        elif options.edit:
            td.edit_task(options.edit, text)
        elif text:
            td.add_task(text, verbose=options.verbose, quiet=options.quiet)
        else:
            kind = 'needsAction' if not options.done else 'completed'
            td.print_list(kind=kind, verbose=options.verbose, quiet=options.quiet,
                          grep=options.grep)
    except AmbiguousPrefix:
        e = sys.exc_info()[1]
        _die('the ID "%s" matches more than one task' % e.prefix)
    except UnknownPrefix:
        e = sys.exc_info()[1]
        _die('the ID "%s" does not match any task' % e.prefix)
#    except BadFile as e:
#        _die('%s - %s' % (e.problem, e.path))


if __name__ == '__main__':
    _main()
