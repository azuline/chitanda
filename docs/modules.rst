Modules
#######

Note: All module-specific configuration sections should be added to the
top-level dictionary of the JSON, on the same level as ``trigger_character``.

Aliases (\ ``aliases``\ )
-------------------------

This module allows users to trigger a PM containing the list of aliases
specified in the bot's configuration.

Commands:

.. parsed-literal::

   aliases  // sends the list of aliases to the user via PM

Choose (\ ``choose``\ )
-----------------------

The bot can make a choice for you!

Commands:

.. parsed-literal::

   choose <#>-<#>  // bot will respond with a number in the given range
   choose word1 word2 word3  // bot will respond with one of the words
   choose phrase1, phrase2, phrase3  // bot will respond with one of the phrases

GitHub Relay (\ ``github_relay``\ )
-----------------------------------

This module allows the bot to receive GitHub webhooks and report push, issue,
and pull request events to a specified channel. If this module is enabled, a
key/value pair similar to the following should be added to the configuration
file. The webserver should also be enabled. This module creates an endpoint for
GitHub's webhooks at the ``/github`` URL location; thus, the webhook in GitHub
should be configured to target that URL location.


* ``secret`` - A secret key used to verify signed payloads from GitHub.
* ``relays`` - A dictionary mapping repository IDs to lists of channels to relay
  webhook events to.
* ``relays[][[listener]]`` - The identifier of the listener that the destinaton
  channel belongs to. See the Configuration section for identifier formatting.
* ``relays[][[channel]]`` - The channel to relay to. ``#channel`` for IRC and the
  channel ID for Discord.
* ``relays[][[branches]]`` - If empty, commits to all branches will be reported.
  Otherwise, only commits to the listed branches will be reported.

.. code-block:: json

   {
     "github_relay": {
       "secret": null,
       "relays": {
         "1": [
           {
             "listener": "DiscordListener",
             "channel": "12345",
             "branches": [
               "master"
             ]
           }
         ]
       }
     }
   }

No commands

Help (\ ``help``\ )
-------------------

Send a private message with all bot commands to any user who types !help.

Commands:

.. parsed-literal::

   help  // triggers the private message

IRC Channels (\ ``irc_channels``\ )
-----------------------------------

An IRC only module that handles channel joins and parts. It keeps track of
which channels the bot was in prior to quitting, handling channel rejoins after
the bot reconnects. Admin only.

Commands:

.. parsed-literal::

   join #channel
   part  // parts current channel
   part #channel

Last.FM (\ ``lastfm``\ )
------------------------

Fetches a user's now playing track from Last.FM.

Requires the following addition to the config:

.. code-block:: json

   {
     "lastfm": {
       "api_key": "your api key"
     }
   }

Commands:

.. parsed-literal::

   lastfm  // fetches and relays your now playing track
   lastfm set <lastfm username>  // sets the lastfm account to fetch from
   lastfm unset  // unsets your lastfm username

Quotes (\ ``quotes``\ )
-----------------------

Allows users to store and fetch quotes of messages to and from the bot's
database. Quotes are stored separately for each channel. Deletion of quotes is
admin only.

Commands:

.. parsed-literal::

   quote  // fetches a random quote
   quote <quote id> <quote id> <quote id>  // fetches quotes by ID (max: 3)
   quote add <quote>  // adds a quote
   quote del <quote id>  // delets a quote
   quote find <string>  // searches for a quote from its contents

Relay (\ ``relay``\ )
---------------------

Relays messages between two channels. Handles differences in formatting
between listeners.

The configuration is a list of sublists. The sublists contain dictionaries
detailling the linked channels. Each group of linked channels are their
own sublist. More than two channels can be linked at once.

.. code-block:: json

   {
     "relays": [
       [
         {
           "listener": "IRCListener@irc.freenode.fake",
           "channel": "#channel"
         },
         {
           "listener": "DiscordListener",
           "channel": "12345",
           "webhook": "something"
         }
       ]
     ]
   }

No commands.

Reload (\ ``reload``\ )
-----------------------

Hot reloads the bot's config and modules. Will handle changes in the bot's
configuration of enabled modules. Admin only.

Commands:

.. parsed-literal::

   reload  // triggers the reload

Say (\ ``say``\ )
-----------------

The bot parrots your message back to you.

Commands:

.. parsed-literal::

   say <message>  // bot says the message

Sed (\ ``sed``\ )
-----------------

Sed a previous message from the channel. Up to 1024 messages are saved in the
history per-channel. Supports case-insensitive ``i`` and global ``g`` flags.

Commands:

.. parsed-literal::

   s/find/replace  // replace 'find' with 'replace'
   .sed s/find/replace  // same thing but with a trigger

Tell (\ ``tell``\ )
-------------------

Allow for messages to be stored and relayed to users who are not currently
online.

Commands:

.. parsed-literal::

   tell <user> <message>  // store a message to be relayed to user

Titles (\ ``titles``\ )
-----------------------

The bot will print the ``<title>`` tag of URLs messaged to the
channel. This module listens only on IRC.

No commands.

UrbanDictionary (\ ``urbandictionary``\ )
-----------------------------------------

Allows queries to the UrbanDictionary API and relaying of definitions.

Commands:

.. parsed-literal::

   urbandictionary <string>  // fetches top definition for string
   urbandictionary <number> <string>  // fetches <number> ranked definition

WolframAlpha (\ ``wolframalpha``\ )
-----------------------------------

Allows basic queries and answer fetching to the WolframAlpha API. Useful for
math and weather, among other things.

To enable this command, a configuration section must be added to the config,
per the following:

.. code-block:: json

   {
     "wolframalpha": {
       "appid": "your api key goes here"
     }
   }

Commands:

.. parsed-literal::

   wolframalpha <query>  // fetches wolframalpha's response to the query
