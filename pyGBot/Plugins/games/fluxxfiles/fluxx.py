
from pyGBot.Plugins.games.fluxxfiles.game import Card

class FluxxCard(Card):
    def __init__(self, title, short_title, description):
        Card.__init__(self, title, short_title)
        self.description = description.strip()

    def play(self, player):
        pass
    
    def __str__(self):
        return "%s (%s)" % (self.title, self.short_title)

    @property
    def card_info(self):
        return """
%s (%s)
--------------------------------------
Card Type: %s
Information: %s
%s
        """.strip() % \
        (self.title, self.short_title, self.type,
         self.information, "Description: %s" % self.description \
         if self.description != "" else "")
    
