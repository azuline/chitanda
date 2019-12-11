Development
###########

Modules
-------

Modules can be added by creating a module inside ``chitanda/modules``. All
modules inside of ``chitanda/modules`` will be dynamically imported upon bot
startup. The name of the module identifies the module in configuration
options. For example, ``chitanda/modules/catpics.py``, the identifier will be
``catpics``.

Modules can contain setup functions, bot hooks, commands, and database
migrations.

If a module contains multiple commands, it can be turned into a package. The
package must have an ``__init__.py`` to be dynamically imported. All python
modules inside the package will be imported, and the name of the package
identifies all python modules inside the package in the configuration file.

Setup
-----

If an module imported dynamically by the bot has a ``setup`` function, it will
be called on first import. This occurs after the bot's ``__init__`` finishes
running. The only argument passed to ``setup`` is ``bot``. This function should
be synchronous.

During setup, functions can be added to the bot's ``message_handler`` and
``response_handler`` hooks and routes can be added to the bot's
``web_application`` (for webhook support).

Commands
--------

To add a command to the bot, decorate a function with the ``register``
decorator, which takes, as an argument, the command trigger (without the
configurable trigger character). Command functions must be asynchonous, and
should have a ``message`` parameter.

Commands can either be coroutines or async generators; both are supported. The
coroutines can return a generator as well.

The return value of a command or the values returned when iterating over it can
be in two formats: a ``str`` or a ``dict``. If returned as a ``str``, the
return value will be sent to ``message.target``. If returned as a ``dict``, the
dict will be directly passed to the ``listener.message`` coroutine. The
``dict`` must have the keys ``target`` and ``message``, with other key support
depending on the listener it is passed to.

For example, a simple command to parrot text would be:

.. code-block:: python

   @register('parrot')
   async def parrot(message):
      return message.contents

.. parsed-literal::

   <user> .parrot squawk
   <chitanda> squawk

When a command is called, it is passed a ``Message`` object as its only
argument. A ``Message`` object has the following attributes:

.. parsed-literal::

   class Message:
       bot  # The main bot class.
       listener  # The listener the message originated from.
       target  # The channel the message was sent to (same as author in PM).
       author  # The nickname (IRC) or ID of the message sender.
       contents  # The contents of the message with the trigger stripped out.
       private  # If the message was sent via PM or in a channel.

There are several decorators in the ``chitanda.decorators`` package which can
be used to decorate commands. Some of these decorators add new instance
variables to the ``message`` object.

Decorators
~~~~~~~~~~

args
^^^^

``chitanda.decorators.args``

A decorator factory that takes ``re.Pattern`` objects and/or ``str`` regexes as
arguments. When a command is called, ``message.contents`` will be matched with
the regexes in the order that they were passed into ``args``. If there is a
match, the return value of ``re.Match.groups()`` will be assigned to
``message.args``. If there isn't a match, a ``BotError`` will be raised.

Example:

.. code-block:: python

   import re
   from chitanda.decorators import args, register

   REUSED_REGEX = re.compile(r'a regex')

   @register('generic_command')
   @args(r'([^ ]+)', REUSED_REGEX)
   async def call(message):
       print(message.args)

admin_only
^^^^^^^^^^

``chitanda.decorators.admin_only``

Compares the sender of the command against the admin list. If the sender is an
admin, the command will be called. Otherwise, a ``BotError`` will be raised.

auth_only
^^^^^^^^^

``chitanda.decorators.auth_only``

Check's a user's authorization before calling the command. This is primarily
geared towards IRC, where it mandates NickServ identification. In services that
require accounts to use, the command will always be called. If the user is
found to be authorized, their account name/username will be assigned to
``message.username``. If they are not authorized, a ``BotError`` will be raised.

channel_only
^^^^^^^^^^^^

``chitanda.decorators.channel_only``

Requires that the message be sent in a channel, otherwise a ``BotError`` will
be raised.

private_message_only
^^^^^^^^^^^^^^^^^^^^

``chitanda.decorators.private_message_only``

Requires that the command be sent via PM, otherwise a ``BotError`` will be
raised.

allowed_listeners
^^^^^^^^^^^^^^^^^

``chitanda.decorators.allowed_listeners``

A decorator factory that restricts the command to certain listeners. Each
allowed listener type should be passed in as a separate argument. If the
command is called on a disallowed listener, a ``BotError`` will be raised.
Commands that are not allowed on a listener will not be shown in that
listener's ``help`` command.

Example:

.. code-block:: python

   from chitanda.decorators import register, allowed_listeners
   from chitanda.listeners import IRCListener

   @register('quit')
   @allowed_listeners(IRCListener)
   async def call(message):
       await listener.raw('QUIT\r\n')

Decorating Async Generators
~~~~~~~~~~~~~~~~~~~~~~~~~~~

When decorating an async generator, the ``admin_only`` and ``auth_only``
decorators must visually come last, i.e. decorate the function first. this is
because they have different behaviors for async generators vs regular
coroutines and detection of a decorated async generator isn't accurate

.. code-block:: python

   from chitanda.decorators import args, auth_only, register

   # Good

   @register('pics cats')
   @args(r'$')
   @auth_only
   async def call(message):
       for cat in _get_cat_pics():
           yield cat

   # Bad

   @register('pics cats')
   @auth_only
   @args(r'$')
   async def call(message):
       for cat in _get_cat_pics():
           yield cat

Hooks
-----

Hooks enable modules to process messages before the command is
called and responses before they are sent to the recipient.

Pre-command hooks must be coroutines or async generators and take a ``message``
parameter, which is the ``Message`` object. If a value is returned from the
hook, it will be handled the same way a return value from a command call would
be handled. To add a pre-command hook, append the hook function to the
``bot.message_handlers`` list.

Pre-response hooks must be coroutines and take four parameters:
``bot, listener, target, response``. Their return value is discarded.
The ``response`` argument will always be a dictionary with ``target`` and
``message`` keys.

Database Migrations
-------------------

Modules with database migrations must be python packages. Inside the package,
the existence of a directory named ``migrations`` indicates that the module has
database migrations to run. Migrations should be numerically named ``.sql``
files in the format ``0001.sql``, ``0002.sql``. They will be ran in the order
of their ascending numerical identifiers.

The migrations that have been ran will be recorded in the database as to not
re-run them.
