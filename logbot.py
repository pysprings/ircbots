import datetime
import sys

from twisted.internet import defer, endpoints, protocol, reactor, task
from twisted.python import log
from twisted.words.protocols import irc


class LogBotProtocol(irc.IRCClient):
    nickname = 'LogBot'

    def __init__(self):
        self.deferred = defer.Deferred()
        self.logname = 'pysprings.log'

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
        self.msg(channel, message)
        now = datetime.datetime.now()
        with open(self.logname, 'a') as f:
            f.write('[%s] %s: %s\n' % (now, nick, message))

    def _showError(self, failure):
        return failure.getErrorMessage()


class LogBotFactory(protocol.ReconnectingClientFactory):
    protocol = LogBotProtocol
    channels = ['#pysprings']


def main(reactor, description):
    endpoint = endpoints.clientFromString(reactor, description)
    factory = LogBotFactory()
    d = endpoint.connect(factory)
    d.addCallback(lambda protocol: protocol.deferred)
    return d


if __name__ == '__main__':
    log.startLogging(sys.stderr)
    task.react(main, ['tcp:127.0.0.1:6667'])
