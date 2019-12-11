Configuration
#############

The listeners supported by default are for IRC and Discord. In the
configuration file, these listeners are sometimes referred to using an
identifier. The syntax of a listener's identifier varies depending on which
service it belongs to.

IRCListener identifiers will be in the format ``IRCListener@{hostname}``, where
``hostname`` is the hostname of the IRC server the listener is connecting to.

Discord listener identifiers will simply be ``DiscordListener``, as a single
listener is spawned for the entire service.

The fields in the config file are as follows:

* ``trigger_character`` - The character that precedes all commands.
* ``user_agent`` - User Agent to use when making HTTP requests.
* ``irc_servers`` - A dictionary of IRC servers to connect to, mapping the
  hostname to another dictionary containing information about the server. The
  specific keys available can be found in the example configuration below. The
  ``perform`` key defines commands that are run upon an established connection
  to the IRC server. If left empty, no IRC listeners will be spawned.
* ``discord_token`` - The token of a discord bot. This can be generated in the
  discord developer portal. If left blank, the Discord listener will not
  start.
* ``webserver`` - Configuration of whether or not to spawn a webserver and on
  which port to spawn it. Enable if a module/listener uses the bot's webserver;
  disable if no modules or listeners use it.
* ``modules`` - A dictionary whose keys are listener identifiers and values are
  lists of the names of modules to enable. The names of default modules are
  found in parentheses on the Modules documentation page. The ``global`` key
  represents modules enabled for all listeners.
* ``aliases`` - A dictionary whose keys are listener identifiers and values are
  dictionaries of trigger aliases mapping custom triggers to the triggers
  supported by the bot. Do not include the trigger character in the triggers.
  The ``global`` key represents aliases effective for all listeners.
* ``admins`` - A list of bot admins. The admins have access to commands that
  others don't have access to. It is configured as a dictionary mapping an
  identifier of the service to a list of administrator names. For Discord, the
  unique account identifier is used, which can be copied after enabling
  Developer mode in the Discord client. For IRC, the NickServ account name is
  used.

chitanda can run with only a subset of its listeners enabled. Leave the
configuration blank for a listener to disable it.

Example configuration:

.. code-block:: json

   {
     "trigger_character": ".",
     "user_agent": "chitanda bot",
     "irc_servers": {
       "irc.freenode.net": {
         "port": "6697",
         "tls": true,
         "tls_verify": false,
         "nickname": "chitanda",
         "perform": ["NICKSERV IDENTIFY chitanda_nickserv_password"]
       }
     },
     "discord_token": "sample",
     "webserver": {
       "enable": true,
       "port": 38248
     },
     "modules": {
       "global": [
         "aliases",
         "choose",
         "help",
         "irc_channels",
         "lastfm",
         "reload",
         "say",
         "sed",
         "tell",
         "titles",
       ],
       "IRCListener@irc.freenode.net": [
         "quotes",
         "wolframalpha"
       ],
       "DiscordListener": [
         "urbandictionary"
       ]
     },
     "aliases": {
       "global": {
         "j": "join"
       },
       "IRCListener@irc.freenode.net": {
         "im": "say I'm free!"
       },
       "DiscordListener": {
         "s": "sed"
       }
     },
     "admins": {
       "DiscordListener": ["111111111111111111"],
       "IRCListener@irc.freenode.net": ["azul"]
     }
   }
