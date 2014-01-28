import collections
import re
import sys

from twisted.internet import defer, endpoints, protocol, reactor, task
from twisted.python import log
from twisted.words.protocols import irc

regex = re.compile(r'(\w+)(\+\+|--)')


class KarmaBotProtocol(irc.IRCClient):
    nickname = 'KarmaBot'

    def __init__(self):
        self.scores = collections.defaultdict(int)
        self.deferred = defer.Deferred()

    def connectionLost(self, reason):
        self.deferred.errback(reason)

    def signedOn(self):
        # This is called once the server has acknowledged that we sent
        # both NICK and USER.
        for channel in self.factory.channels:
            self.join(channel)

    # Obviously, called when a PRIVMSG is received.
    def privmsg(self, user, channel, message):
        nick, _, host = user.partition('!')
        message = message.strip()
        if not regex.search(message):  # not a trigger command
            return  # so do nothing
        d = defer.maybeDeferred(self.karma, regex.findall(message))
        d.addErrback(self._showError)
        d.addCallback(self._sendMessage, channel, nick)

    def _sendMessage(self, msg, target, nick=None):
        if nick:
            msg = '%s, %s' % (nick, msg)
        self.msg(target, msg)

    def _showError(self, failure):
        return failure.getErrorMessage()

    def karma(self, scores):
        for thing, delta in scores:
            self.scores[thing] += 1 if delta == '++' else -1
        return "%s now has karma of %s" % (thing, self.scores[thing])


class KarmaBotFactory(protocol.ReconnectingClientFactory):
    protocol = KarmaBotProtocol
    channels = ['#pysprings']


def main(reactor, description):
    endpoint = endpoints.clientFromString(reactor, description)
    factory = KarmaBotFactory()
    d = endpoint.connect(factory)
    d.addCallback(lambda protocol: protocol.deferred)
    return d


if __name__ == '__main__':
    log.startLogging(sys.stderr)
    task.react(main, ['tcp:127.0.0.1:6667'])
