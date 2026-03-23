from main_classes import Card
from classes import Particle
from random import randint

AI_CONFIG = {
    # these are the googoo babies that need taunt to not instantly die
    # musketeer ignores taunt so shes a little different but she's still squishy :3
    "fragile_classes": ("Pump", "Medic", "Musketeer", "Sponge", "Snowball", "Retriever"),
    # how many attackers the ai wants at each game phase
    # (turn_threshold, target_count)
    "attacker_targets": {
        "early": (0, 3),   # turns 0-3: just 2 attackers, focus economy
        "mid": (4, 4),   # turns 4-8: ramp up pressure
        "late": (9, 5)    # turn 9+: go full aggro
    },
    # hard = never exceed, soft = start worrying about diminishing returns
    "limits": {
        "Pump": {"soft": 2, "hard": 3},   # 4 pumps = +4 mana/turn, more than enough
        "Taunt": {"soft": 2, "hard": 3},   # 3 taunts covers most boards
        "Medic": {"soft": 1, "hard": 2},   # 2 medics = 4hp/turn which is strong
    }
}

def get_enemy(player):
    """
    Description:
    Returns the other player. Used everywhere so ai_value() methods don't
    have to repeat the same one-liner every time they want to know what
    they're trying to kill.

    Parameters:
        player (Player): the player whose enemy we want

    Returns:
        Player: whoever is not this player
    """
    return next(p for p in player.game.players if p != player)

def is_protected(player):
    """
    Description:
    Checks whether this player has at least one taunt card on the board.
    Every fragile card (Pump, Medic, Sponge, Snowball, Retriever, Musketeer)
    runs this check before deciding whether playing them is a valid strategic
    decision or just feeding a body to the enemy for free.

    Parameters:
        player (Player): the player whose board to inspect

    Returns:
        bool: True if at least one active card has taunt > 0
    """
    return any(c.taunt > 0 for c in player.active)

def get_attacker_target(turn):
    """
    Description:
    How many attackers does the AI want right now? Lookup from AI_CONFIG based
    on current turn. Early game: build economy and stop spamming bodies. Mid game:
    start applying pressure. Late game: everything is a weapon, stop thinking,
    start winning.

    Parameters:
        turn (int): the current turn number from game.turn

    Returns:
        int: how many attacker cards the AI wants active at this point in the game
    """
    # returns how many attackers the ai wants right now
    if turn >= AI_CONFIG["attacker_targets"]["late"][0]:
        return AI_CONFIG["attacker_targets"]["late"][1]
    elif turn >= AI_CONFIG["attacker_targets"]["mid"][0]:
        return AI_CONFIG["attacker_targets"]["mid"][1]
    return AI_CONFIG["attacker_targets"]["early"][1]

def count_active_by_name(player, class_name):
    """
    Description:
    Counts how many cards of a specific class are currently on the player's board.
    Used to enforce the soft/hard limits in AI_CONFIG which stops the AI from playing
    a fourth Pump.

    Parameters:
        player (Player): the player whose board to check
        class_name (str): class name string to match (e.g. "Pump", "Medic")

    Returns:
        int: number of active cards matching that class name
    """
    return len([c for c in player.active if c.__class__.__name__ == class_name])

def stat_value(card):
    """
    Description:
    Flat rough score for a card based purely on its numbers. Does NOT call
    ai_value() because several ai_value() methods call this. 
    Used by Net to pick the juiciest free play, and by FatMan
    to weigh up whether nuking both boards hurts the AI more than the opponent.

    Parameters:
        card (Card): the card to estimate

    Returns:
        int: a rough value
    """
    # had to add this to avoid recursion
    return card.cost * 10 + card.atk * 3 + card.hp * 2


class Skeleton(Card):
    """
    Description:
    A 1/1 for 1. Its entire purpose is to fill the
    board when you have a spare mana and nothing worth doing with it.
    Gets a surprising amount better with Miku (heals to 3hp, now survives 
    retaliation) or Sonic (attacks immediately for 1 damage).

    Attributes:
        hp (int): 1
        atk (int): 1
        cost (int): 1
        retreat_cost (int): 0
    """
    def setup(self):
        """
        Description:
        Sets Skeleton's stats and loads its image.

        Returns:
            self: for chaining
        """
        self.name = "Skeleton"
        self.desc = "A humble 1/1 for 1."
        self.hp = 1
        self.atk = 1
        self.cost = 1
        self.retreat_cost = 0
        self.set_image("skeleton")
        return self

    def ai_value(self):
        """
        Description:
        early_bonus decays so hard that by turn 6 the AI correctly recognises
        Skeleton as bad and stops playing them. kill_bonus exists because
        sometimes the only thing worth playing is a 1/1 that can snipe another 1/1.
        miku_bonus is high because 3hp Skeleton surviving  is kinda funny.

        Returns:
            int: play priority score, sliding toward the floor with each passing turn
        """
        enemy = get_enemy(self.owner)
        game = self.owner.game

        # skeleton is cheap filler, great early terrible late
        early_bonus = max(0, 18 - game.turn * 3)

        # good if there are 1hp things we can trade into
        one_shot_targets = len([c for c in enemy.active if c.hp <= 1 and c.taunt == 0])
        kill_bonus = one_shot_targets * 12

        # filling an empty board is always good
        board_deficit = len(enemy.active) - len(self.owner.active)
        presence_bonus = board_deficit * 5

        # miku heals it to 3hp on play which makes it not completely pathetic
        miku_bonus = 25 if self.owner.commander.name == "Miku" else 0

        # sonic gives it haste which is basically a free 1 damage on the turn
        sonic_bonus = 12 if self.owner.commander.name == "Sonic" else 0

        # too many attackers already
        own_attackers = len([c for c in self.owner.active if c.atk > 0])
        attacker_target = get_attacker_target(game.turn)
        saturation_penalty = max(0, (own_attackers - attacker_target) * 10)

        base = 12 + early_bonus + kill_bonus + presence_bonus + miku_bonus + sonic_bonus - saturation_penalty
        return max(4, base)


class Amogus(Card):
    """
    Description:
    A 2/2 for 2, trades evenly with most things.

    Attributes:
        hp (int): 2
        atk (int): 2
        cost (int): 2
        retreat_cost (int): 0
    """
    def setup(self):
        """
        Description:
        Sets Amogus's stats and loads its image.

        Returns:
            self: for chaining
        """
        self.name = "amogus"
        self.desc = "from the hit game among us"
        self.hp = 2
        self.atk = 2
        self.cost = 2
        self.retreat_cost = 0
        self.set_image("amogus")
        return self

    def ai_value(self):
        """
        Description:
        Stays relevant all game but decays gently so the AI knows late-game there's
        probably a better play. board_deficit bonus means the AI will still fill an
        empty board with Amogus at turn 12 rather than sit there doing nothing.

        Returns:
            int: play priority score for the AI
        """
        enemy = get_enemy(self.owner)
        game = self.owner.game

        # amogus is the bread and butter
        # good early, still playable late as body filler
        early_bonus = max(0, 18 - game.turn * 2)

        # can trade into 1hp or 2hp things
        trade_targets = len([c for c in enemy.active if c.hp <= 2 and c.taunt == 0])
        trade_bonus = trade_targets * 8

        # filling the board
        board_deficit = len(enemy.active) - len(self.owner.active)
        presence_bonus = board_deficit * 7

        # sonic makes it immediately useful
        sonic_bonus = 14 if self.owner.commander.name == "Sonic" else 0

        # shadow loves anything that can kill stuff for mana
        shadow_bonus = 8 if self.owner.commander.name == "Shadow" else 0

        # check if we already have too many of this type
        own_attackers = len([c for c in self.owner.active if c.atk > 0])
        attacker_target = get_attacker_target(game.turn)
        saturation_penalty = max(0, (own_attackers - attacker_target) * 10)

        base = 24 + early_bonus + trade_bonus + presence_bonus + sonic_bonus + shadow_bonus - saturation_penalty
        return max(5, base)


class Pump(Card):
    """
    Description:
    The economy engine, now with a generous cap condition. Generates +1 mana at
    the start of your turn if your mana is at or below the cap (turn_mana * 2).
    Since the condition fires AT the cap, one Pump can push you one above it.

    Attributes:
        hp (int): 5
        atk (int): 0
        cost (int): 1
        retreat_cost (int): 5
    """
    def setup(self):
        """
        Description:
        Sets Pump's stats and loads its image.

        Returns:
            self: for chaining
        """
        self.name = "Pump"
        self.desc = "Generates 1 energy per turn. Allows one over the cap."
        self.hp = 5
        self.atk = 0
        self.cost = 1
        self.retreat_cost = 5
        self.set_image("pump")
        return self

    def ai_value(self):
        """
        Description:
        Value depends almost entirely on whether it'll survive long enough to
        generate anything. Hard returns 0 when the enemy has 4+ ATK and there's
        no taunt as it will die before producing a single mana and that's just
        a waste. Biden bonus is large because each Pump is instant
        tempo on top of future mana.

        Returns:
            int: play priority score, 0 if it would die before doing anything useful
        """
        pumps_active = count_active_by_name(self.owner, "Pump")
        if pumps_active >= AI_CONFIG["limits"]["Pump"]["hard"]:
            return 0  # 4 pumps is insane we do not need more

        game = self.owner.game
        enemy = get_enemy(self.owner)

        # mana value scales down the later it is
        estimated_turns_remaining = max(2, 18 - game.turn)
        mana_value = min(estimated_turns_remaining, 12) * 3

        # each additional pump is worth less than the last (mana cap exists)
        pump_decay = pumps_active * 18
        base = mana_value - pump_decay

        # biden makes every pump immediately profitable (+1 mana on play)
        if self.owner.commander.name == "Biden":
            base += 30

        # already at mana cap means pump is less useful right now
        mana_cap = game.turn_mana * 2
        if self.owner.mana >= mana_cap - 1:
            base = int(base * 0.4)

        # pump dies instantly without taunt
        # retreat cost is 5 so you basically can never retreat it
        enemy_total_atk = sum(c.atk for c in enemy.active)
        has_taunt = is_protected(self.owner)

        if not has_taunt:
            if enemy_total_atk >= 4:
                return 0  # it will die before generating a single mana
            elif enemy_total_atk >= 2:
                base = int(base * 0.2)  # very risky
            elif enemy_total_atk >= 1:
                base = int(base * 0.5)  # risky but might survive
        else:
            # even with taunt, thin taunt coverage is still risky
            taunt_hp = sum(c.hp for c in self.owner.active if c.taunt > 0)
            if taunt_hp < enemy_total_atk:
                base = int(base * 0.6)  # taunt might die this turn

        return max(0, int(base))

    def on_turn_start(self):
        """
        Description:
        Fires at the start of the owning player's turn. Adds +1 mana if currently
        at or below the cap (turn_mana * 2). Since the check is <= rather than <,
        a Pump will fire even when at the cap, exactly as the description promises.

        Returns:
            list: one mana particle near the mana display, slightly randomised
        """
        if self.owner.mana <= self.owner.game.turn_mana * 2:
            self.owner.mana += 1
        return [Particle(self.owner.mana_position[0]+randint(-32,32), self.owner.mana_position[1]+randint(-32,32), 1, self.particle_font, self.hp_color_font, self.atk_color_font)]


class Hong(Card):
    """
    Description:
    The big threat. A 4/4 for 5, which is expensive but kills almost everything in one hit
    and survives most counterattacks. With Sonic he swings for 4 the turn he enters.
    With Shadow, killing something with a 4/4 guarantees +1 mana almost every swing.

    Attributes:
        hp (int): 4
        atk (int): 4
        cost (int): 5
        retreat_cost (int): 2
    """
    def setup(self):
        """
        Description:
        Sets Hong's stats and loads his image.

        Returns:
            self: for chaining
        """
        self.name = "Hong"
        self.desc = "Taiping Heavenly King"
        self.hp = 4
        self.atk = 4
        self.cost = 5
        self.retreat_cost = 2
        self.set_image("hong")
        return self

    def ai_value(self):
        """
        Description:
        Large bonus when there are 4hp-or-less things he can oneshot.
        need_bonus fires if the AI has literally no attackers at all.

        Returns:
            int: play priority score for the AI
        """
        enemy = get_enemy(self.owner)
        game = self.owner.game

        # hong is a late-game
        killable_next_turn = [c for c in enemy.active if c.hp <= 4]
        kill_bonus = len(killable_next_turn) * 15

        # hong survives most things
        safe_from = [c for c in enemy.active if c.atk < 4]
        survive_bonus = len(safe_from) * 5

        # good for closing out games
        if enemy.commander.hp <= 15:
            commander_pressure = (15 - enemy.commander.hp) * 4
        else:
            commander_pressure = 0

        # if we have no attackers we desperately need hong
        own_attackers = len([c for c in self.owner.active if c.atk > 0])
        attacker_target = get_attacker_target(game.turn)
        need_bonus = 22 if own_attackers < attacker_target else 0

        # shadow gains +1 mana per kill
        shadow_bonus = 20 if self.owner.commander.name == "Shadow" else 0

        # sonic gives haste which is VILE on a 4/4
        sonic_bonus = 25 if self.owner.commander.name == "Sonic" else 0

        base = 35 + kill_bonus + survive_bonus + commander_pressure + need_bonus + shadow_bonus + sonic_bonus
        return base


class IceCube(Card):
    """
    Description:
    The cheap taunt. 1 mana, 2hp (4hp with Miku, which is part of why Miku
    stages feel oppressive), taunt=1. Just a wall.

    Attributes:
        hp (int): 2
        atk (int): 0
        cost (int): 1
        retreat_cost (int): 1
        taunt (int): 1
    """
    def setup(self):
        """
        Description:
        Sets IceCube's minimal stats and loads its image.

        Returns:
            self: for chaining
        """
        self.name = "Ice Cube"
        self.desc = "Taunt: 1"
        self.taunt = 1
        self.hp = 2
        self.atk = 0
        self.cost = 1
        self.retreat_cost = 1
        self.set_image("icecube")
        return self

    def ai_value(self):
        """
        Description:
        Scales with how much it's currently protecting. More fragile stuff behind
        it = more value. Sponge and Snowball both get their own bonus because they
        are completely dead the moment they're exposed. Miku bonus is very high
        because 4hp taunt for 1 mana is kind of insane.

        Returns:
            int: play priority score, or 2 if the board is already taunted up
        """
        taunts_active = len([c for c in self.owner.active if c.taunt > 0])
        if taunts_active >= AI_CONFIG["limits"]["Taunt"]["hard"]:
            return 2  # already have 3 taunts, not needed

        enemy = get_enemy(self.owner)
        enemy_total_atk = sum(c.atk for c in enemy.active)

        # protecting fragile cards is the whole point
        protected_value = 0
        for c in self.owner.active:
            if c.__class__.__name__ in AI_CONFIG["fragile_classes"]:
                protected_value += stat_value(c) // 3

        # emergency taunt if we have nothing
        no_taunt_urgency = 40 if taunts_active == 0 else 8

        # musketeer ignores taunt so its partially countered
        musketeer_threat = any(c.__class__.__name__ == "Musketeer" for c in enemy.active)
        ignore_penalty = 25 if musketeer_threat else 0

        # miku heals it to 4hp on play
        miku_bonus = 22 if self.owner.commander.name == "Miku" else 0

        # sponge needs taunt to grow so we want ice cube when we have a sponge
        sponge_on_board = any(c.__class__.__name__ == "Sponge" for c in self.owner.active)
        sponge_bonus = 18 if sponge_on_board else 0

        # snowball also needs protection desperately
        snowball_on_board = any(c.__class__.__name__ == "Snowball" for c in self.owner.active)
        snowball_bonus = 20 if snowball_on_board else 0

        base = (enemy_total_atk * 5) + protected_value + no_taunt_urgency + miku_bonus + sponge_bonus + snowball_bonus - ignore_penalty
        return max(5, base)


class Thorn(Card):
    """
    Description:
    The punishing taunt. 2 mana, 3hp, taunt=1, 1 atk, and deals 2 damage back
    to anything that hits it. 2hp cards that attack Thorn just die.
    The 1 atk means Thorn can also chip the commander.

    Attributes:
        hp (int): 2
        atk (int): 1
        cost (int): 2
        taunt (int): 1
    """
    def setup(self):
        """
        Description:
        Sets Thorn's stats and loads its image.

        Returns:
            self: for chaining
        """
        self.name = "Thorn"
        self.desc = "Taunt: 1. Deals 2 damage back to anyone who attacks it."
        self.taunt = 1
        self.hp = 3
        self.atk = 1
        self.cost = 2
        self.set_image("thorn")
        return self

    def ai_value(self):
        """
        Description:
        Scales with how many things it will kill via retaliation.
        Cards with 2hp or less die when they swing into it.
        Without attackers since Thorn is still useful as
        protection even when nobody's currently attacking.

        Returns:
            int: play priority score, or 2 if already at the taunt hard cap
        """
        taunts_active = len([c for c in self.owner.active if c.taunt > 0])
        limits = AI_CONFIG["limits"]["Taunt"]
        if taunts_active >= limits["hard"]:
            return 2  # board is protected enough

        enemy = get_enemy(self.owner)

        # thorn actively punishes attackers
        kills_via_retaliation = [c for c in enemy.active if c.hp <= 2]
        crippled_by_retaliation = [c for c in enemy.active if 2 < c.hp <= 4]
        kill_bonus = len(kills_via_retaliation) * 25
        cripple_bonus = len(crippled_by_retaliation) * 10

        # the higher their atk, the more they want to attack through taunt
        strong_attackers = len([c for c in enemy.active if c.atk >= 3])
        strong_punish = strong_attackers * 12

        # protecting fragile units
        fragile_units = len([c for c in self.owner.active if c.__class__.__name__ in AI_CONFIG["fragile_classes"]])
        protect_bonus = fragile_units * 10

        # first taunt is always urgent
        no_taunt_bonus = 25 if taunts_active == 0 else 8

        # thorn has 1 atk itself which is a nice bonus
        own_attack_value = len([c for c in enemy.active if c.hp <= 1]) * 6

        enemy_has_attackers = any(c.atk > 0 for c in enemy.active)
        if not enemy_has_attackers:
            return max(5, no_taunt_bonus + protect_bonus)  # less urgent with no attackers

        base = no_taunt_bonus + kill_bonus + cripple_bonus + strong_punish + own_attack_value + protect_bonus
        return max(5, base)

    def attacked(self, target):
        """
        Description:
        Overrides Card.attacked() to insert retaliation. The dead check prevents
        on_attacked from firing if Thorn was already killed earlier in the same
        damage chain, which would be potentially crash.

        Parameters:
            target (Card):

        Returns:
            list: particles from on_attacked (retaliation + whatever death it causes)
        """
        particles = []
        if self.dead == False:
            particles.extend(self.on_attacked(target))
        return particles

    def on_attacked(self, attacker):
        """
        Description:
        Called when Thorn is hit. Dies first if already at 0hp so that Shadow's
        on_enemy_death fires before the retaliation. Then deals 2 damage back via
        attacker.attacked(self), triggering attacker's own defensive on action.

        Parameters:
            attacker (Card):

        Returns:
            list: the -2 retaliation particle and anything the damage chain kicks off
        """
        particles = []
        if self.hp <= 0:
            self.die()
            particles.extend(attacker.owner.commander.on_enemy_death(self))
        attacker.hp -= 2
        particles.append(Particle(attacker.x + attacker.w/2, attacker.y + attacker.h/2, -2, self.particle_font, self.hp_color_font, self.atk_color_font))
        attacker.attacked(self)
        return particles


class Medic(Card):
    """
    Description:
    Passive healer. Heals the commander for 2hp at the start of every turn.

    Attributes:
        hp (int): 4
        atk (int): 0
        cost (int): 2
    """
    def setup(self):
        """
        Description:
        Sets Medic's stats and loads its image.

        Returns:
            self: for chaining
        """
        self.name = "Medic"
        self.desc = "Heals your commander for 2 HP at the start of your turn."
        self.hp = 4
        self.atk = 0
        self.cost = 2
        self.set_image("medic")
        return self

    def ai_value(self):
        """
        Description:
        Scales with how much HP the commander is missing and how many turns are
        left to actually use the healing. Returns 0 at the hard cap.
        Returns nearly nothing without taunt because it dies before healing once.
        urgency_multiplier spikes at 8hp or below.

        Returns:
            int: play priority score, 0 if there are already two Medics on the board
        """
        medics_active = count_active_by_name(self.owner, "Medic")
        if medics_active >= AI_CONFIG["limits"]["Medic"]["hard"]:
            return 0  # 2 medics already, thats plenty

        enemy = get_enemy(self.owner)
        game = self.owner.game
        hp_deficit = 25 - self.owner.commander.hp

        # at full hp, medic is bad (will just overflow)
        if hp_deficit <= 0:
            return 3

        # estimate how many turns we can get out of it
        turns_estimate = max(2, 16 - game.turn // 2)
        total_heal = min(hp_deficit, turns_estimate * 2)
        heal_value = total_heal * 4  # slightly more valuable now

        # medic dies instantly without taunt
        has_taunt = is_protected(self.owner)
        enemy_total_atk = sum(c.atk for c in enemy.active)

        if not has_taunt:
            if enemy_total_atk >= 3:
                return max(2, int(heal_value * 0.1))  # will die before healing anything
            else:
                heal_value = int(heal_value * 0.5)

        # jesus heals a random ally too
        jesus_overlap = 8 if self.owner.commander.name == "Jesus" else 0

        # near death? medic becomes priority
        urgency_multiplier = 1.0
        if self.owner.commander.hp <= 8:
            urgency_multiplier = 2.2  # we are literally dying
        elif self.owner.commander.hp <= 14:
            urgency_multiplier = 1.5

        base = int((heal_value - jesus_overlap) * urgency_multiplier)
        return max(3, base)

    def on_turn_start(self):
        """
        Description:
        Heals the commander for 2hp every single turn. No cap.

        Returns:
            list: one +2 heal particle near the commander position
        """
        self.owner.commander.hp += 2
        return [Particle(self.owner.commander_position[0]+self.owner.commander.w//2+randint(-32,32), self.owner.commander_position[1]+self.owner.commander.h//2+randint(-32,32), 2, self.particle_font, self.hp_color_font, self.atk_color_font)]


class Sponge(Card):
    """
    Description:
    Gets +1 ATK every time it's hit and survives.

    Attributes:
        hp (int): 4
        atk (int): 1
        cost (int): 2
    """
    def setup(self):
        """
        Description:
        Sets Sponge's starting stats and loads its image.

        Returns:
            self: for chaining
        """
        self.name = "Sponge"
        self.desc = "Gains +1 ATK every time it is attacked and survives."
        self.hp = 4
        self.atk = 1
        self.cost = 2
        self.set_image("sponge")
        return self

    def ai_value(self):
        """
        Description:
        Playing it unprotected is just handing the opponent a free kill. 
        With taunt, scales with current stats, how many enemy cards would proc 
        the growth without killing it, and a coverage_factor representing how 
        long the taunt wall will realistically survive.

        Returns:
            int: play priority score for the AI
        """
        enemy = get_enemy(self.owner)
        game = self.owner.game
        has_taunt = is_protected(self.owner)

        # bad play
        if not has_taunt:
            return max(3, self.atk * 2)

        # current combat value
        current_value = self.atk * 10 + self.hp * 2

        # how many enemy cards would hit it and proc the buff instead of killing it
        growth_triggers = len([c for c in enemy.active if 0 < c.atk < self.hp])
        growth_value = growth_triggers * 16

        longevity = min(game.turn * 2, 30)

        # how long until sponge can kill the commander
        turns_to_lethal = max(1, enemy.commander.hp - self.atk)
        urgency = max(0, 35 - turns_to_lethal * 4)

        # how long will the taunt wall actually last
        taunt_stability = sum(c.hp for c in self.owner.active if c.taunt > 0)
        enemy_pressure = sum(c.atk for c in enemy.active)
        coverage_factor = min(1.0, taunt_stability / max(enemy_pressure, 1))

        # sonic + sponge = swing immediately, then grows every time its attacked
        sonic_bonus = 30 if self.owner.commander.name == "Sonic" else 0

        # shadow + sponge = killing enemies generates mana to play more stuff
        shadow_bonus = 15 if self.owner.commander.name == "Shadow" and self.atk >= 3 else 0

        # jesus randomly heals sponge sometimes which is nice
        jesus_bonus = 8 if self.owner.commander.name == "Jesus" else 0

        base = int((current_value + growth_value + longevity + urgency) * coverage_factor)
        return base + sonic_bonus + shadow_bonus + jesus_bonus

    def on_attacked(self, attacker):
        """
        Description:
        Called when Sponge takes a hit. Gains +1 ATK if still alive (hp > 0).
        The hp check stops Sponge from gaining ATK posthumously.

        Parameters:
            attacker (Card): the card that just attacked

        Returns:
            list: empty
        """
        particles = []
        if self.hp > 0:
            self.atk += 1
        return particles


class Kamikaze(Card):
    """
    Description:
    Direct commander damage spell. atk=8 is what the card shows and what the AI
    uses for all its lethal calculations. This card has been rebalanced at least
    three times. 
    Whatever the actual damage ends up being, it bypasses the entire board and closes
    games that would otherwise drag on indefinitely.

    Attributes:
        hp (int): 0
        atk (int): 7
        cost (int): 6
        spell (bool): True
    """
    def setup(self):
        """
        Description:
        Sets Kamikaze's stats and loads its image.

        Returns:
            self: for chaining
        """
        self.name = "Kamikaze"
        self.desc = "Deals 7 damage to the enemy commander and dies immediately."
        self.hp = 0
        self.atk = 7
        self.cost = 6
        self.spell = True
        self.set_image("kamikaze")
        return self

    def ai_value(self):
        """
        Description:
        Lethal detection via self.atk (currently 5). Commander at or below self.atk hp
        = 2000, always play. self.atk + available board ATK >= commander HP = 1500,
        win this turn. Otherwise scales with damage percentage, how blocked the board
        is (more useful when normal attacks can't get through), and a wall bypass
        bonus. alchemist_bonus is gone since Kamikaze costs 6 and Alchemist only
        draws off spells costing 1 or less.

        Returns:
            int: play priority score, 2000 or 1500 for lethal windows
        """
        enemy = get_enemy(self.owner)
        game = self.owner.game

        # if we can kill the commander this is the highest priority
        if enemy.commander.hp <= self.atk:
            return 2000  # always play, no exceptions

        # kombination kill check
        total_own_atk = sum(c.atk for c in self.owner.active if c.actions > 0)
        if self.atk + total_own_atk >= enemy.commander.hp:
            return 1500  # we can win this turn

        # % of commanders health we're nuking
        damage_pct = self.atk / max(enemy.commander.hp, 1)
        pct_bonus = int(damage_pct * 90)

        # kamikaze bypasses taunt entirely which is its main use case
        losing_margin = len(enemy.active) - len(self.owner.active)
        bypass_bonus = max(0, losing_margin * 18)  # more valuable when behind on board

        # blows through thorn/icecube walls to hit commander directly
        enemy_taunt_wall = sum(c.taunt for c in enemy.active)
        wall_bypass = enemy_taunt_wall * 12

        # slight penalty for wasting mana (could have played another card with spare)
        spare_mana = max(0, self.owner.mana - self.cost)
        wasted_mana_penalty = spare_mana * 4

        base = 20 + pct_bonus + bypass_bonus + wall_bypass - wasted_mana_penalty
        return max(5, base)

    def on_play(self):
        """
        Description:
        Fires on play. Deals 6 damage (hp -= self.atk) to the enemy commander.

        Returns:
            list: damage particles and anything commander.attacked() kicks off
        """
        particles = []
        for player in self.owner.game.players:
            if player != self.owner:
                player.commander.hp -= self.atk
                particles.extend(player.commander.attacked(self))
                particles.append(Particle(player.commander.x+player.commander.w/2, player.commander.y+player.commander.h/2, -self.atk, self.particle_font, self.hp_color_font, self.atk_color_font))
        self.hp = 0
        self.die()
        return particles
class Bin(Card):
    """
    Description:
    Haste draw engine. Plays to the board, immediately draws a card for free, and
    stays there. The haste means you get the draw AND a board presence on the same turn, 
    which is better than Retriever who makes you wait a turn to use it.
    2hp means it dies to anything.

    Attributes:
        hp (int): 2
        atk (int): 0
        cost (int): 2
        haste (bool): True
        selection_type (str): ""
    """
    def setup(self):
        """
        Description:
        Sets Bin's stats and loads its image.

        Returns:
            self: for chaining
        """
        self.name = "Bin"
        self.desc = "Draw 1 card. Haste."
        self.action_image = "card_images/star.png"
        self.hp = 2
        self.atk = 0
        self.cost = 2
        self.haste = True
        self.selection_type = ""
        self.set_image("bin")
        return self

    def on_action(self):
        """
        Description:
        Draws one card for free. selection_type="" means no target is needed.
        both the player and the AI's empty-string branch just call this and get
        a card without needing to click anything.

        Returns:
            list: empty
        """
        self.owner.draw(1, cost=0)
        self.actions -= 1
        return []

    def ai_value(self):
        """
        Description:
        Most valuable when the hand is running dry or the opponent has significantly
        more cards. The haste_premium reflects that Bin draws AND gives board presence
        the same turn as opposed to Retriever which requires spare mana the following
        turn before it does anything useful.

        Returns:
            int: play priority score for the AI
        """
        enemy = get_enemy(self.owner)
        game = self.owner.game
        hand_size = len(self.owner.hand)
        deck_size = len(self.owner.deck)

        # core value: low hand means bin is very good
        hand_scarcity = (4 - hand_size) * 10  # sharper scaling

        # if they have more cards than us thats very bad
        card_adv = (len(enemy.hand) - hand_size) * 2


        base = hand_scarcity + card_adv
        return int(base)


class Retriever(Card):
    """
    Description:
    Persistent draw engine. max_actions=2 means it can draw twice per turn for
    1 mana each. Worse than Bin on arrival (Bin draws free on the same turn,
    Retriever needs spare mana before it does anything), but every subsequent
    turn it sits there trading 1 mana for 1 card which is a good deal. 2hp means
    it dies to anything, so draw quickly.

    Attributes:
        hp (int): 2
        atk (int): 0
        cost (int): 2
        max_actions (int): 2
        selection_type (str): ""
    """
    def setup(self):
        """
        Description:
        Sets Retriever's stats and loads its image.

        Returns:
            self: for chaining
        """
        self.name = "Retriever"
        self.desc = "Draw 1 card for 1 mana."
        self.action_image = "card_images/star.png"
        self.hp = 2
        self.atk = 0
        self.cost = 2
        self.max_actions = 2
        self.selection_type = ""
        self.set_image("retriever")
        return self

    def ai_value(self):
        """
        Description:
        Simplified scoring: scales with how low the hand is and how much card
        advantage the enemy has. The usability_now and deck_penalty logic were
        removed in this version.

        Returns:
            int: play priority score for the AI
        """
        enemy = get_enemy(self.owner)
        hand_size = len(self.owner.hand)
        deck_size = len(self.owner.deck)

        # retriever costs mana to use (1 per draw) unlike bin which is free
        hand_scarcity = (3 - hand_size) * 10


        card_adv = max(0, len(enemy.hand) - hand_size) * 7


        base = hand_scarcity + card_adv
        return max(2, int(base))

    def on_action(self):
        """
        Description:
        Draws one card for 1 mana. If somehow out of mana, still consumes the
        action but skips the draw. This is technically a bug but also arguably
        the player's fault for clicking it when broke. I tried fixing it but
        ran into a problem with the AI infinitely clicking it.

        Returns:
            list: empty
        """
        if self.owner.mana > 0:
            self.actions -= 1
            self.owner.draw(1, cost=1)
        else:
            self.actions -= 1
        return []
class Musketeer(Card):
    """
    Description:
    ignore_taunt=True means she can attack anything on the
    enemy board regardless of what taunts are protecting it, including Pumps
    and Medics sitting cosily behind a Thorn wall. 3/1 means she kills almost
    anything in one hit but dies to any counterattack, so she needs her own 
    taunt to survive past one swing. 

    Attributes:
        hp (int): 1
        atk (int): 3
        cost (int): 3
        ignore_taunt (bool): True
    """
    def setup(self):
        """
        Description:
        Sets Musketeer's stats and loads her image.

        Returns:
            self: for chaining
        """
        self.name = "Musketeer"
        self.desc = "Ignores Taunt."
        self.ignore_taunt = True
        self.hp = 1
        self.atk = 3
        self.cost = 3
        self.set_image("musketeer")
        return self

    def ai_value(self):
        """
        Description:
        Massive value when the enemy has taunt because she bypasses it entirely.
        engine_bonus is very high for killing Pumps and Medics which would
        otherwise be untouchable. Without enemy taunt she's just a fragile 3/1
        which isn't good. Half value without own taunt since
        she dies to any counterattack and won't get to swing again.

        Returns:
            int: play priority score for the AI
        """
        enemy = get_enemy(self.owner)

        enemy_taunt_cards = [c for c in enemy.active if c.taunt > 0]
        enemy_has_taunt = len(enemy_taunt_cards) > 0

        if enemy_has_taunt:
            # kill valuable things sitting behind taunt
            non_taunt_targets = [c for c in enemy.active if c.taunt == 0]
            if non_taunt_targets:
                # go for highest value soft target
                best_target_value = max(stat_value(c) for c in non_taunt_targets)
                commander_snipe = max(0, 22 - enemy.commander.hp) * 2
            else:
                # only the commander is a valid target
                best_target_value = 20
                commander_snipe = max(5, 32 - enemy.commander.hp)

            # pumps and medics are especially valuable kills
            engine_targets = len([c for c in non_taunt_targets if c.name in ("Pump", "Medic")])
            engine_bonus = engine_targets * 22

            base = 48 + best_target_value // 2 + commander_snipe + engine_bonus
        else:
            # without enemy taunt musketeer is just a 3/1 which is not great
            one_shot_targets = len([c for c in enemy.active if c.hp <= 3])
            base = 14 + one_shot_targets * 8

        # musketeer dies to any counterattack (1hp) so she needs to be behind taunt
        has_taunt = is_protected(self.owner)
        if not has_taunt:
            base = int(base * 0.45)  # dies instantly to retaliation

        # sonic lets her attack immediately on the turn its played
        if self.owner.commander.name == "Sonic":
            base += 35

        # shadow gains mana from kills
        if self.owner.commander.name == "Shadow" and enemy_has_taunt:
            base += 15

        return max(5, base)


class Net(Card):
    """
    Description:
    Plays a card from your hand for free. selection_type="hand" means its action
    targets your own hand rather than attacking. No haste (it was nerfed), 
    so the free play happens next turn, UNLESS Sonic gives
    Net +1 action on play, making it immediate. hp is now 1, down from 2.
    Net is clearly considered dangerous enough to justify a 1hp tax.
    Net+Kamikaze was insane back in the day as Rayhan will tell you.

    Attributes:
        hp (int): 1
        atk (int): 0
        cost (int): 3
        selection_type (str): "hand"
    """
    def setup(self):
        """
        Description:
        Sets Net's stats and loads its image.

        Returns:
            self: for chaining
        """
        self.name = "Net"
        self.desc = "Play one card for free."
        self.selection_type = "hand"
        self.action_image = "card_images/star.png"
        self.hp = 1
        self.atk = 0
        self.cost = 3
        # self.haste = True
        self.set_image("net")
        return self

    def ai_value(self):
        """
        Description:
        Uses stat_value() to find the juiciest free play target. Special-cases
        Kamikaze (checks if the combo is actually lethal before committing) and
        anything with a very high ai_value (if it scores >= 500 on its own,
        definitely play it free immediately).

        Returns:
            int: play priority score, up to 1500 for lethal combo setups
        """
        playable_via_net = [c for c in self.owner.hand if c.name != "Net"]
        if not playable_via_net:
            return 0  # empty hand

        # use stat_value to find the juiciest free target
        best_card = max(playable_via_net, key=lambda c: stat_value(c))
        best_val = stat_value(best_card)
        best_cost = best_card.cost

        # special case: free kamikaze = 3 mana for 10 commander damage
        if best_card.name == "Kamikaze":
            # evaluate if the kamikaze is itself worth playing
            kaz_score = best_card.ai_value()
            if kaz_score >= 500:
                return 1500  # always combo net + kamikaze when kamikaze is lethal
            return max(50, 30 + kaz_score // 4)  # still usually good

        if best_val >= 500:
            return 1500  # whatever this is, play it free

        # more valuable if the best card costs more than we can afford otherwise
        currently_unaffordable = best_cost > self.owner.mana - self.cost
        unaffordable_bonus = (best_cost - 3) * 8 if currently_unaffordable else (best_cost - 3) * 4

        base = best_val * max(0, unaffordable_bonus)
        return max(0, int(base))

    def on_action(self, target):
        """
        Description:
        Plays the target card for free (spend_mana=False), then consumes Net's
        action and kills Net. Single-use.

        Parameters:
            target (Card): the hand card that gets free entry onto the board

        Returns:
            list: empty
        """
        target.play(False)
        self.actions -= 1
        self.hp = 0
        self.die()
        return []


class BagOfGold(Card):
    """
    Description:
    Zero-cost spell that gives +1 mana. Useful for reaching expensive cards on
    the same turn (FatMan costs 7, normal cap is 6, BagOfGold bridges it) or
    chaining into multiple plays in one turn. With Alchemist it also draws a
    card because cost 0 qualifies for the cost 1 or less trigger.
    cap_penalty of 250 stops the AI from burning bags when already at max mana.

    Attributes:
        hp (int): 0
        atk (int): 0
        cost (int): 0
        spell (bool): True
    """
    def setup(self):
        """
        Description:
        Sets BagOfGold's stats and loads its image.

        Returns:
            self: for chaining
        """
        self.name = "Gold Bag"
        self.desc = "Gives 1 mana."
        self.spell = True
        self.hp = 0
        self.atk = 0 
        self.cost = 0
        self.set_image("bagofgold")
        return self

    def ai_value(self):
        """
        Description:
        Checks whether +1 mana enables a more expensive card this turn (the main
        use case), then scores that card's stat_value as the primary value. Also
        checks what else could be played after that enabled card (chain_bonus for
        multi-play turns). Alchemist bonus is huge because BagOfGold is effectively
        a free draw + mana with him. Near-worthless at mana cap (cap_penalty = 250).

        Returns:
            int: play priority score for the AI
        """
        current_mana = self.owner.mana
        game = self.owner.game

        # alchemist draws a card every time a spell is played
        alchemist_bonus = 45 if self.owner.commander.name == "Alchemist" else 0

        # is this the mana that unlocks a more expensive card this turn
        best_enabled_val = 0
        best_enabled_card = None
        for card in self.owner.hand:
            if card is self:
                continue
            if card.cost == current_mana + 1:
                val = stat_value(card)
                if val > best_enabled_val:
                    best_enabled_val = val
                    best_enabled_card = card

        # chain bonus: what else can we play after the enabled card
        chain_bonus = 0
        if best_enabled_card is not None:
            remaining_after = current_mana + 1 - best_enabled_card.cost
            follow_up = [c for c in self.owner.hand
                         if c is not self and c is not best_enabled_card
                         and c.cost <= remaining_after]
            if follow_up:
                chain_bonus = max(stat_value(c) for c in follow_up) // 3

        # at mana cap the extra mana is literally wasted
        mana_cap = game.turn_mana * 2
        cap_penalty = 250 if current_mana >= mana_cap else 0

        # minimum intrinsic value (its always at least 1 mana of value)
        base_intrinsic = 4

        base = alchemist_bonus + best_enabled_val + chain_bonus + base_intrinsic - cap_penalty
        return max(1, base)

    def on_play(self):
        """
        Description:
        Gives +1 mana and immediately dies.
        Spawns a mana particle so you can see the +1 land.

        Returns:
            list: one mana particle at the mana display position
        """
        self.owner.mana += 1
        self.hp = 0
        self.die()
        return [Particle(self.owner.mana_position[0], self.owner.mana_position[1], 1, self.particle_font, self.hp_color_font, self.atk_color_font)]


class Snowball(Card):
    """
    Description:
    Gets +1/+1 every turn. Starts as a 0/1 for 4 mana
    Retreat_cost=10 means once you've committed, you've committed.
    Needs taunt or it dies to absolutely anything the turn it enters.

    Attributes:
        hp (int): 1
        atk (int): 0
        cost (int): 4
        retreat_cost (int): 10
    """
    def setup(self):
        """
        Description:
        Sets Snowball's starting stats and loads its image.

        Returns:
            self: for chaining
        """
        self.name = "Snowball"
        self.desc = "Gets +1/+1 per turn"
        self.hp = 1
        self.atk = 0
        self.cost = 4
        self.retreat_cost = 10
        self.set_image("snowball")
        return self

    def ai_value(self):
        """
        Description:
        Returns 1 without taunt. It's a 0/1 and it will die. With taunt,
        projects total ATK output over remaining turns, then
        multiplies by coverage_factor representing how long the taunt wall will
        realistically hold. Sonic and Jesus both make this significantly more viable.

        Returns:
            int: play priority score, 1 if unprotected and will die immediately
        """
        has_taunt = is_protected(self.owner)
        game = self.owner.game
        enemy = get_enemy(self.owner)

        # snowball without taunt dies immediately
        if not has_taunt:
            return 1

        current_value = self.atk * 8 + self.hp * 2

        # project total damage output if snowball survives
        turns_remaining = max(2, 20 - game.turn)
        # it gains +1/+1 each turn so atk growth is triangular
        projected_damage = self.atk * turns_remaining + (turns_remaining * (turns_remaining + 1)) // 2
        growth_value = min(projected_damage * 2, 120)

        # the closer commander is to dying the more urgent snowball becomes
        turns_to_lethal = max(1, enemy.commander.hp - self.atk)
        urgency_bonus = max(0, 45 - turns_to_lethal * 5)

        # will the taunt actually survive long enough for snowball to matter
        taunt_total_hp = sum(c.hp for c in self.owner.active if c.taunt > 0)
        enemy_total_atk = sum(c.atk for c in enemy.active)
        cover_turns = taunt_total_hp / max(enemy_total_atk, 1)
        cover_factor = min(1.0, cover_turns / max(turns_to_lethal, 1))

        # jesus randomly heals allies
        jesus_bonus = 10 if self.owner.commander.name == "Jesus" else 0

        base = int((current_value + growth_value + urgency_bonus) * cover_factor)
        return max(1, base + jesus_bonus)

    def on_turn_start(self):
        """
        Description:
        Gains +1 ATK and +1 HP at the start of every turn. The growth is
        permanent.

        Returns:
            list: empty
        """
        self.atk += 1
        self.hp += 1
        return []


class B52(Card):
    """
    Description:
    AoE spell. Deals 1 damage to every enemy active card. Cheap at 2 mana and
    excellent for clearing boards full of 1hp things (Skeletons, Musketeers). 
    Uses float("inf") hp so Thorn's 2-damage retaliation can't kill it mid-sweep.
    Then hp=0 and die() are called manually at the end to clean up properly.
    spell=True means no board slot and no on_card_played.

    Attributes:
        hp (float): inf
        atk (int): 0
        cost (int): 2
        spell (bool): True
    """
    def setup(self):
        """
        Description:
        Sets B52's stats, including the hp=float("inf"), and loads its image.

        Returns:
            self: for chaining
        """
        self.name = "B52"
        self.desc = "Deals 1 damage to every enemy card."
        self.spell = True
        self.hp = float("inf")
        self.atk = 0 
        self.cost = 2
        self.set_image("b52")
        return self

    def ai_value(self):
        """
        Description:
        Returns 2 if nothing would be killed or even weakened.
        Otherwise scales with total kill value and an exponential
        board_clear_bonus. Fragile high-value
        targets like Pumps and Medics get a large extra bonus.

        Returns:
            int: play priority score, or 2 if the sweep would achieve nothing
        """
        enemy = get_enemy(self.owner)

        # what can we kill (1hp cards die immediately)
        kills = [c for c in enemy.active if c.hp <= 1]
        # what do we weaken to 1hp (making them vulnerable to anything)
        weakened = [c for c in enemy.active if 1 < c.hp <= 2]

        kill_value = sum(stat_value(c) for c in kills)
        weaken_value = sum(int(stat_value(c) * 0.4) for c in weakened)

        # killing multiple cards at once is exponentially good (clears threats AND draws from glados)
        board_clear_bonus = len(kills) * (len(kills) - 1) * 14

        # even better when commander is low
        if len(kills) >= 2 and enemy.commander.hp <= 15:
            lane_clear_bonus = (15 - enemy.commander.hp) * 4
        else:
            lane_clear_bonus = 0

        # especially good at nuking pumps and medics (1hp fragile value targets)
        fragile_kills = [c for c in kills if c.__class__.__name__ in AI_CONFIG["fragile_classes"]]
        fragile_bonus = len(fragile_kills) * 18

        # alchemist draws a card off b52 which is a bonus
        alchemist_bonus = 20 if self.owner.commander.name == "Alchemist" else 0


        # nothing happens :(
        if not kills and not weakened:
            return 2

        base = kill_value + weaken_value + board_clear_bonus + lane_clear_bonus + fragile_bonus + alchemist_bonus
        return max(2, int(base))

    def on_play(self):
        """
        Description:
        Deals 1 damage to every card in every non-owning player's active zone.
        Calls attacked() on each so defensive hooks fire (Thorn retaliates, Sponge
        may gain ATK, etc). Now uses five passes like FatMan due to the same list mutation
        issue applies here since die() modifies player.active mid-iteration and a
        single pass would skip cards that shift index. The infinite hp still prevents
        Thorn retaliation from killing B52 mid-sweep.

        Returns:
            list: -1 damage particles at each affected card's position
        """
        particles = []
        cards_hit = []
        for i in range(5):
            for player in self.owner.game.players:
                if player != self.owner:
                    for card in player.active:
                        if card not in cards_hit:
                            cards_hit.append(card)
                            card.hp -= 1
                            card.attacked(self)
                            particles.append(Particle(card.x+card.w//2, card.y+card.h//2, -1, self.particle_font, self.hp_color_font, self.atk_color_font))
        self.hp = 0
        self.die()
        return particles
    

class FatMan(Card):
    """
    Description:
    Kills every active card on both boards simultaneously.
    spell=True bypasses the board limit. hp=float("inf") survives its own sweep.
    Cost 7 means you need BagOfGold or a mana bonus to reach it,
    this should require setup and ideally some kind of ramp to justify itself.

    Attributes:
        hp (float): inf
        atk (int): 0
        cost (int): 7
        spell (bool): True
    """
    def setup(self):
        """
        Description:
        Sets FatMan's stats, including hp=float("inf") for reasons that should and loads its image.

        Returns:
            self: for chaining
        """
        self.name = "Fat Man"
        self.desc = "Kills every card."
        self.spell = True
        self.hp = float("inf")
        self.atk = 0
        self.cost = 7
        self.set_image("fat_man")
        return self

    def ai_value(self):
        """
        Description:
        Computes net board impact: enemy board value minus own board value minus
        a penalty for losing engine cards (Pumps and Medics are expensive to rebuild
        and hurt to lose). Adds bonuses for huge grown threats that can't otherwise
        be dealt with, and for taunt walls that can't be punched through normally.
        Returns 2 if winning (don't nuke a winning position) or if both boards are
        empty (pointless and expensive).

        Returns:
            int: play priority score, 2 if it would be actively bad to play this
        """
        enemy = get_enemy(self.owner)
        own = self.owner

        # what do we gain from wiping the enemy board
        enemy_wipe_value = sum(stat_value(c) for c in enemy.active)

        # what do we lose from wiping our own board
        # pumps and medics hurt a lot to lose
        own_wipe_cost = sum(stat_value(c) for c in own.active)
        engine_loss = len([c for c in own.active if c.name in ("Pump", "Medic")]) * 25

        # wipe benefits us
        net = enemy_wipe_value - own_wipe_cost - engine_loss

        # specifically great against massive grown threats we cant kill normally
        scary_threats = [c for c in enemy.active if c.atk >= 5 or c.__class__.__name__ in ("Snowball", "Sponge")]
        threat_bonus = sum(c.atk * 8 for c in scary_threats)

        # taunt walls
        taunt_wall_hp = sum(c.hp for c in enemy.active if c.taunt > 0)
        wall_bonus = taunt_wall_hp * 4

        # dont do it
        if own_wipe_cost > enemy_wipe_value + 15:
            return 2  # we are winning, nuking ourselves is bad

        # alchemist draws a card off this spell which slightly softens the loss
        alchemist_bonus = 5 if own.commander.name == "Alchemist" else 0

        # nothing on either board = waste of 8 mana
        if not enemy.active and not own.active:
            return 2

        base = 12 + net + threat_bonus + wall_bonus + alchemist_bonus
        return max(2, base)

    def on_play(self):
        """
        Description:
        Deals 99 damage to every active card on both boards five times over,
        calling attacked() on each so death hooks and Shadow triggers fire.
        The five passes attempt to compensate for a list mutation issue: die()
        modifies player.active mid-iteration, which causes cards to be skipped
        on a single pass. Multiple passes catch what the first pass missed.
        Then hp=0, die().

        Returns:
            list: -99 damage particles at every card's position on both sides
        """
        particles = []
        cards_hit = []
        for i in range(5):
            for player in self.owner.game.players:
                for card in player.active:
                    if card not in cards_hit:
                        cards_hit.append(card)
                        card.hp -= 99
                        card.attacked(self)
                        particles.append(Particle(card.x+card.w//2, card.y+card.h//2, -99, self.particle_font, self.hp_color_font, self.atk_color_font))
        self.hp = 0
        self.die()
        return particles
