from fluxx import FluxxCard
from game import pretty_print_list, plural
from random import choice


class ActionCard(FluxxCard):
    information = """
When you play this card, do whatever it says.
    """.strip()
    type = "Action"
    def __init__(self, title, short_title, description):
        FluxxCard.__init__(self, title, short_title, description)

    def play(self, player):
        self.do_action(player)
        player.game.discard(self)

    def do_action(self, player):
        pass

class RulesReset(ActionCard):
    
    def __init__(self):
        ActionCard.__init__(self, "Rules Reset", "A_RR", """
Reset to the Basic Rules.

Discard all New Rules cards, and leave only the original Basic Rules card in play.
        """)

    def do_action(self, player):
        rules = player.game.rule_pile
        cards = [card for card in rules if card.short_title != "R_BASIC"]
        rules.discard(cards)

rule_regex = "\d+|r_[a-z]+"

class TrashRule(ActionCard):
    
    def __init__(self):
        ActionCard.__init__(self, "Trash a New Rule", "A_TR", """
Select one of the New Rule cards in play and place it in the discard pile.
        """)

    def do_action(self, player):
        self.player = player
        rules_pile = player.game.rule_pile
        self.rules = [card for card in rules_pile if card.short_title != "R_BASIC"]
        player.halt_game = self.title
        if(len(self.rules) == 1): self("1") # Just use that card
        else: self.ask()

    def ask(self):
        rules_str = ["%d: %s" % (i+1, c) for i, c in enumerate(self.rules)]
        self.player.request_input("Which rule do you want to trash? %s" % rules_str,
                                  (self, rule_regex))
        
    def __call__(self, message):
        player = self.player
        rule = message
        if rule.isdigit():
            rule = int(rule)
            num_rules = len(self.rules)
            if rule > num_rules:
                self.player.output("There aren't that many rules in play!")
                return self.ask()
            rule_picked = self.rules[rule-1]
        else:
            rule_picked = player.game.find_card(rule)
            if rule_picked not in self.rules:
                player.output("You can't trash that rule.")
                return self.ask()
        player.game.channel.output("%s trashed %s." % (player.name, rule_picked))
        player.game.draw_discard.discard(rule_picked)
        player.halt_game = None
        return True

class NoLimits(ActionCard):
    
    def __init__(self):
        ActionCard.__init__(self, "No Limits", "A_NL", """
Discard all Hand and Keeper Limit rules currently in play.
        """)

    def do_action(self, player):
        rules = player.game.rule_pile
        rules.discard(card for card in rules if card.short_title[0:3] == "R_L")

class TakeAnotherTurn(ActionCard):
    
    def __init__(self):
        ActionCard.__init__(self, "Take Another Turn", "A_AT", """
Take another turn as soon as you finish this one.
        """)

    def do_action(self, player):
        player.game.another_turn_played = True

class Jackpot(ActionCard):

    def __init__(self):
        ActionCard.__init__(self, "Jackpot!", "A_J", """
Draw 3 extra cards!
        """)

    def do_action(self, player):
        cards = player.draw(3 + player.game.rule_pile.inflation_amount, True)
        handlen = len(player.hand)
        cards_str = ["%d: %s" % (i+handlen+1, c) for i, c in enumerate(cards)]
        player.output("You drew: " + pretty_print_list(cards_str))

class EverybodyGetsOne(ActionCard):
    
    regex = "(give |g )?(\d+|[akrgc]_[a-z]+) (to )?[a-z0-9_\-\[\]`^]+"
    
    def __init__(self):
        ActionCard.__init__(self, "Everybody gets 1", "A_EG1", """
Count the number of players in the game (including yourself).
Draw enough cards to give 1 card each to each player, then do so.
        """)
        self.cards = []

    def do_action(self, player):
        self.draw_amount = (1 + player.game.rule_pile.inflation_amount)
        self.players = player.game.players
        self.num_players = len(self.players)
        self.total_cards = self.draw_amount * self.num_players
        self.cards = player.game.draw_cards(self.total_cards)
        self.cards_str = ["%d: %s" % (i+1, c) for i, c in enumerate(self.cards)]
        self.cards_given = dict((a.name.lower(),0) for a in self.players)
        self.players_dict = dict((a.name.lower(),a) for a in self.players)
        self.ask()
    
    def ask(self):
        self.player.halt_game = self.title
        cards_str = ["%d: %s" % (i+1, c) for i, c in enumerate(self.cards)]
        self.player.request_input("Choose which cards to give to who: %s" % \
                                  pretty_print_list(cards_str), (self, EverybodyGetsOne.regex))
        
    def __call__(self, message):
        params = message.replace("give","") \
                        .replace("to","") \
                        .replace("!", "").split()
        if len(params) != 2:
            return self.player.output("Syntax:    %B[give] %Ucard%U [to] %Uplayer%U%B")
        card_picked, receiver = params
        rec_lower = receiver.lower()
        
        # Check if the player exists.
        if rec_lower not in self.players_dict:
            self.player.output("There is no player with that name.")
            return self.ask()
        
        # Figure out what card to give
        if card_picked.isdigit():
            card_picked = int(card_picked)
            handlen = len(self.cards)
            if card_picked > handlen:
                self.player.output("You only have %d card%s to give." % \
                              (handlen, plural(self.cards)))
                return self.ask()
            card_picked = self.cards[card_picked-1]
        else:
            card_picked = self.player.game.find_card(card_picked.upper())
            if card_picked not in self.cards:
                self.player.output("You didn't draw that card!")
                return self.ask()
        # Check if you've already given that person enough cards
        if self.cards_given[rec_lower] == self.draw_amount:
            self.player.output("You already gave them %d cards." % self.draw_amount)
            return self.ask()
        # Send the card and delete from set that you drew
        hand = self.players_dict[rec_lower].hand
        hand.receive(card_picked)
        self.cards_given[rec_lower] += 1
        self.cards.remove(card_picked)
        
        # Notify player
        if receiver != self.player.name:
            self.players_dict[rec_lower].output("%s gave you %d: %s." \
                              % (self.player.name, len(hand), card_picked))
            self.player.output("You gave %s to %s." % (card_picked, receiver))
        else:
            self.player.output("You gave yourself %d: %s." % (len(hand), card_picked))
        # Check if you're done yet
        if sum(self.cards_given.values()) == self.total_cards:
            self.player.halt_game = None
            return True
        return self.ask()

keeper_regex = "\d+|[kc]_[a-z]+"

class TrashSomething(ActionCard):

    def __init__(self):
        ActionCard.__init__(self, "Trash Something", "A_TK", """
Take your choice of any Keeper or Creeper from in front of
any player and put it on the discard pile.

If no one has any Keepers or Creepers, nothing happens when
you play this card.
        """)
        self.player_keepers = None
        self.player_name = None

    def do_action(self, player):
        self.player = player
        self.players = player.game.players
        self.keeper_list = []
        # For the chosen player
    
    def __call__(self, keeper):
        player, players, keeper_list = self.player, self.players, self.keeper_list
        if keeper.isdigit():
            keeper = int(keeper)
            num_keepers = len(keeper_list)
            if keeper > num_keepers:
                player.output("There aren't that many keepers on the table!")
                return self.ask()
            keeper_picked = self.keeper_list[keeper-1]
        else:
            keeper_picked = player.game.deck.find_card(keeper.upper())
            if keeper_picked not in self.keeper_list:
                player.output("You can't trash that keeper.")
                return self.ask()
        player_name = keeper_picked.owner.player.name
        if player_name != player.name:
            player.game.channel.output("%s trashed %s's %s." % \
                                       (player.name, player_name, keeper_picked))
        else:
            player.game.channel.output("%s trashed their %s." % \
                                       (player.name, keeper_picked))
        player.game.draw_discard.discard(keeper_picked)
        player.halt_game = None
        return True

    def ask(self):
        player, players, keeper_list = self.player, self.players, self.keeper_list
        player.halt_game = self.title
        keeper_no = 1
        s = ""
        for p in players:
            keepers = p.keepers
            if len(keepers) == 0: continue
            s += "\n%s: " % p.name
            keeper_str = []
            for k in keepers:
                keeper_str.append("%d: %s" % (keeper_no, k))
                keeper_no += 1
                self.keeper_list.append(k)
            s += pretty_print_list(keeper_str)
        player.request_input("Which keeper or creeper do you want to trash? %s" % s,
                             (self, keeper_regex))

class StealSomething(ActionCard):

    def __init__(self):
        ActionCard.__init__(self, "Steal Something", "A_SK", """
Take your choice of any Keeper or Creeper from in front of
another player, and put it in front of you.
        """)
        self.keeper_list = []
        self.players = None
        self.player = None

    def do_action(self, player):
        self.player = player
        self.players = player.game.players
        # For the chosen player
        self.ask()
    
    def __call__(self, keeper):
        player, players, keeper_list = self.player, self.players, self.keeper_list
        if keeper.isdigit():
            keeper = int(keeper)
            num_keepers = len(keeper_list)
            if keeper > num_keepers:
                player.output("There aren't that many keepers on the table!")
                return self.ask()
            keeper_picked = keeper_list[keeper-1]
        else:
            keeper_picked = player.game.deck.find_card(keeper.upper())
            if keeper_picked not in self.keeper_list:
                player.output("You can't steal that keeper.")
                return self.ask()
        player_name = keeper_picked.owner.player.name
        if player_name != player.name:
            player.game.channel.output("%s stole %s's %s." % \
                                       (player.name, player_name, keeper_picked))
        else:
            player.output("You can't steal that keeper.")
            return self.ask()
        player.keepers.receive(keeper_picked)
        player.halt_game = None
        return True

    def ask(self):
        player, players, keeper_list = self.player, self.players, self.keeper_list
        player.halt_game = self.title
        keeper_no = 1
        s = ""
        for p in players:
            if p == player: continue
            keepers = p.keepers
            s += "\n%s: " % p.name
            keeper_str = []
            if len(keepers) == 0: continue
            for k in keepers:
                keeper_str.append("%d: %s" % (keeper_no, k))
                keeper_no += 1
                self.keeper_list.append(k)
            s += pretty_print_list(keeper_str)
        player.request_input("Which keeper or creeper do you want to steal? %s" % s,
                             (self, keeper_regex))

class EmptyTrash(ActionCard):
    
    def __init__(self):
        ActionCard.__init__(self, "Empty the Trash", "A_ET", """
Start a new discard pile with this card and shuffle the rest
of the discard pile back into the draw pile.
        """)
    
    def do_action(self, player):
        piles = player.game.draw_discard
        piles.draw_pile.receive(piles.discard_pile)
        piles.draw_pile.shuffle()

class UseWhatYouTake(ActionCard):
    
    def __init__(self):
        ActionCard.__init__(self, "Use What You Take", "A_UT", """
Start a new discard pile with this card and shuffle the rest
of the discard pile back into the draw pile.
        """)
    
    def do_action(self, player):
        self.player = player
        self.players = [p for p in player.game.players if p != player]
        self.players_dict = dict((a.name.lower(),a) for a in self.players)
        player.halt_game = self.title
        if len(self.players) == 1: self("1") # Just use that player
        else: self.ask()
    
    def __call__(self, player_picked):
        player, players, players_dict = self.player, self.players, self.players_dict
        if player_picked.isdigit():
            player_picked = int(player_picked)
            num_players = len(players)
            if player_picked > num_players:
                player.output("There aren't that many players!")
                return self.ask()
            player_picked = players[player_picked-1]
        else:
            if player_picked.lower() not in players_dict:
                player.output("They're not playing.")
                return self.ask()
            player_picked = players_dict[player_picked.lower()]
        card_picked = choice(player_picked.hand)
        player_name = player_picked.name
        player.game.channel.output("%s used %s's %s." % \
                                   (player.name, player_name, card_picked))
        player.hand.receive(card_picked) # So the card belongs to the player now.
        card_picked.play(player)
        player.halt_game = None
        return True
    
    def ask(self):
        player, players, players_dict = self.player, self.players, self.players_dict
        regex = "\d|" + "|".join(p.name for p in players)
        players_str = ["%d: %s" % (i+1, c.name) for i, c in enumerate(players)]
        player.request_input("Whose player's card do you want to play? %s" % \
                             pretty_print_list(players_str), (self, regex))

class DiscardDraw(ActionCard):
    
    def __init__(self):
        ActionCard.__init__(self, "Discard & Draw", "A_DD", """
Discard your entire hand, then draw as many cards as you discarded.

Do not count this card when determining how many replacement cards to draw.
        """)
    
    def do_action(self, player):
        hand = player.hand
        cards_in_hand = len(hand)
        player.game.draw_discard.discard(hand)
        cards = player.draw(cards_in_hand, True)
        handlen = len(player.hand)
        cards_str = ["%d: %s" % (i+handlen+1, c) for i, c in enumerate(cards)]
        player.output("You drew: " + pretty_print_list(cards_str))

card_regex="\d|[kcgar]_[a-z0-9]+"

class DrawXUseY(ActionCard):
    
    draw_total = 0
    play_total = 0
    
    def do_action(self, player):
        self.player = player
        player.halt_game = self.title
        draw_amount = (self.draw_total + player.game.rule_pile.inflation_amount)
        self.cards = player.game.draw_cards(draw_amount)
        self.ask()

    def __call__(self, card):
        player = self.player
        if card.isdigit():
            card = int(card)
            num_cards = len(self.cards)
            if card == 0:
                player.output("You silly!")
                return self.ask()
            if card > num_cards:
                player.output("You didn't get that many cards!")
                return self.ask()
            card_picked = self.cards[card-1]
        else:
            card_picked = player.game.find_card(card.upper())
            if card_picked not in self.cards:
                player.output("You can't play that card.")
                return self.ask()
        player.hand.receive(card_picked)
        card_picked.play(player)
        self.cards.remove(card_picked)
        
        if len(self.cards) == self.draw_total - self.play_total:
            player.game.draw_discard.discard(self.cards)
            player.halt_game = None
            return True
        self.ask()
        
    def ask(self):
        player = self.player
        cards_str = ["%d: %s" % (i+1, c) for i, c in enumerate(self.cards)]
        player.request_input("What do you want to play? %s" % \
                      pretty_print_list(cards_str), (self, card_regex))

class DrawTwoUseThem(DrawXUseY):

    draw_amount = 2
    play_amount = 2
    
    def __init__(self):
        ActionCard.__init__(self, "Draw 2 and Use 'em", "A_D2", """
Set your hand aside.

Draw 2 cards, play them in the order you choose, then pick up your
hand and continue with your turn.

This card, and all cards played because of it, are counted as a single play.
        """)

class DrawThreePlayTwo(DrawXUseY):

    draw_amount = 3
    play_amount = 2
    
    def __init__(self):
        ActionCard.__init__(self, "Draw 3, play 2 of them", "A_D3P2", """
Set your hand aside.

Draw 3 cards and play 2 of them. Discard the last card, then pick up your hand and continue with your turn.

This card, and all cards played because of it, are counted as a single play.
        """)
