import sys

from twisted.internet import defer, endpoints, protocol, reactor, task
from twisted.python import log
from twisted.words.protocols import irc


class EchoBotProtocol(irc.IRCClient):
    nickname = 'EchoBot'

    def __init__(self):
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
        self.msg(channel, message)


class EchoBotFactory(protocol.ReconnectingClientFactory):
    protocol = EchoBotProtocol
    channels = ['#pysprings']


def main(reactor, description):
    endpoint = endpoints.clientFromString(reactor, description)
    factory = EchoBotFactory()
    d = endpoint.connect(factory)
    d.addCallback(lambda protocol: protocol.deferred)
    return d


if __name__ == '__main__':
    log.startLogging(sys.stderr)
    task.react(main, ['tcp:127.0.0.1:6667'])
