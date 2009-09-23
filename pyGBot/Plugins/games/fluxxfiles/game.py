
import random

def pretty_print_list(list, use_both=False):
    list = [t for t in list if t is not None]
    if len(list) == 0:
        return ""
    elif len(list) == 1 and list[0] is not None:
        return str(list[0])
    elif use_both and len(list) == 2:
        return "both %s and %s" % tuple(list)
    return "%sand %s" % ((('%s, ' * (len(list)-1)) % tuple(list[:-1])), list[-1])

def plural(list):
    return "" if len(list) == 1 else "s"

class Deck(object):

    is_removable = False
    
    def __init__(self):
        self._cards = set()
        self.short_title_map = {}
    
    @property
    def cards(self):
        return self._cards
        
    @cards.setter
    def cards(self, value):
        for c in value:
            c.owner = self
        self._cards = set(value)
        
        self.short_title_map = {}
        for card in value:
            self.short_title_map[card.short_title] = card
    
    def find_card(self, short_title):
        return self.short_title_map[short_title]

    @property
    def undealt_cards(self):
        # Owner is set to the deck when undealt.
        return [c for c in self._cards if c.owner is self]
    
    def __contains__(self, card):
        return card in self._cards or card in self.short_title_map
    
    def __len__(self):
        return len(self._cards)
    
class Card(object):
    
    def __init__(self, title, short_title):
        self.title = title
        # short_title must be unique!
        self.short_title = short_title
        self.owner = None
        
    def __repr(self):
        return "Card(%r)" % self.title
    def __str__(self):
        return self.title
    def __iter__(self):
        return iter([self])
    def __getitem__(self, i):
        if i == 0:
            return self
    
class CardPile(object):

    is_removable = True
    
    def __init__(self):
        self.cards = []
        self.short_title_map = {}
    
    def shuffle(self):
        random.shuffle(self.cards)

    def receive(self, cards):
        L = []
        print cards
        for card in cards:
            if card.owner and card.owner.is_removable and card in card.owner.cards:
                card.owner.cards.remove(card)
                
            ret = self.receive_card(card)
            if ret is True:
                self.cards.append(card)
                self.short_title_map[card.short_title] = card
                L.append(card)
                card.owner = self
            elif ret is not False:
                self.cards.append(ret)
                L.append(ret)
                ret.owner = self
        return L

    def receive_card(self, card):
        """
        Return True to add a card to this pile, otherwise return False or
        another card to add instead of the argument provided.
        """
        
        return True
    
    def deal(self, piles, num_cards):
        for c in xrange(num_cards):
            for pile in piles:
                pile.receive(self.draw(1))
    
    def draw(self, num_cards):
        """
        Return num_cards cards from the top of the pile.
        """
        return self.cards[:num_cards]
    
    def __contains__(self, card):
        return card in self.cards or card in self.short_title_map
    
    def __iter__(self):
        return iter(self.cards)

    def __str__(self):
        return pretty_print_list(self.cards)
    
    def __len__(self):
        return len(self.cards)
    
    def __getitem__(self, i):
        return self.cards[i]
    
    def find_card(self, short_title):
        return self.short_title_map[short_title]

    
class Player(object):
    
    player_count = 1
    
    def __init__(self, name=None):
        if name == None:
            name = "Player %d" % Player.player_count
        Player.player_count += 1
        self.name = name
        self._hand = None
    
    @property
    def hand(self):
        return self._hand
    
    @hand.setter
    def hand(self, hand):
        hand.player = self
        self._hand = hand

    def __getattr__(self, i):
        if self._hand is not None:
            return getattr(self._hand, i)
        return None