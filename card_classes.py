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
        "mid":   (4, 4),   # turns 4-8: ramp up pressure
        "late":  (9, 5)    # turn 9+: go full aggro
    },
    # hard = never exceed, soft = start worrying about diminishing returns
    "limits": {
        "Pump":   {"soft": 2, "hard": 3},   # 4 pumps = +4 mana/turn, more than enough
        "Taunt":  {"soft": 2, "hard": 3},   # 3 taunts covers most boards
        "Medic":  {"soft": 1, "hard": 2},   # 2 medics = 4hp/turn which is strong
    }
}

def get_enemy(player):
    return next(p for p in player.game.players if p != player)

def is_protected(player):
    return any(c.taunt > 0 for c in player.active)

def get_attacker_target(turn):
    # returns how many attackers the ai wants right now
    if turn >= AI_CONFIG["attacker_targets"]["late"][0]:
        return AI_CONFIG["attacker_targets"]["late"][1]
    elif turn >= AI_CONFIG["attacker_targets"]["mid"][0]:
        return AI_CONFIG["attacker_targets"]["mid"][1]
    return AI_CONFIG["attacker_targets"]["early"][1]

def count_active_by_name(player, class_name):
    return len([c for c in player.active if c.__class__.__name__ == class_name])

def stat_value(card):
    # had to add this to avoid recursion
    return card.cost * 10 + card.atk * 3 + card.hp * 2


class Skeleton(Card):
    def setup(self):
        self.name = "Skeleton"
        self.desc = "A humble 1/1 for 1."
        self.hp = 1
        self.atk = 1
        self.cost = 1
        self.retreat_cost = 0
        self.set_image("skeleton")
        return self

    def ai_value(self):
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
    def setup(self):
        self.name = "amogus"
        self.desc = "from the hit game among us"
        self.hp = 2
        self.atk = 2
        self.cost = 2
        self.retreat_cost = 0
        self.set_image("amogus")
        return self

    def ai_value(self):
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

        # miku heals to 4hp - now it lives through thorn which is huge
        miku_bonus = 18 if self.owner.commander.name == "Miku" else 0

        # sonic makes it immediately useful
        sonic_bonus = 14 if self.owner.commander.name == "Sonic" else 0

        # shadow loves anything that can kill stuff for mana
        shadow_bonus = 8 if self.owner.commander.name == "Shadow" else 0

        # check if we already have too many of this type
        own_attackers = len([c for c in self.owner.active if c.atk > 0])
        attacker_target = get_attacker_target(game.turn)
        saturation_penalty = max(0, (own_attackers - attacker_target) * 10)

        base = 24 + early_bonus + trade_bonus + presence_bonus + miku_bonus + sonic_bonus + shadow_bonus - saturation_penalty
        return max(5, base)


class Pump(Card):
    def setup(self):
        self.name = "Pump"
        self.desc = "Generates 1 energy per turn. Allows one over the cap."
        self.hp = 5
        self.atk = 0
        self.cost = 1
        self.retreat_cost = 5
        self.set_image("pump")
        return self

    def ai_value(self):
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
        if self.owner.mana <= self.owner.game.turn_mana:
            self.owner.mana += 1
        return [Particle(self.owner.mana_position[0]+randint(-32,32), self.owner.mana_position[1]+randint(-32,32), 1, self.particle_font, self.hp_color_font, self.atk_color_font)]


class Hong(Card):
    def setup(self):
        self.name = "Hong"
        self.desc = "Taiping Heavenly King"
        self.hp = 4
        self.atk = 4
        self.cost = 5
        self.retreat_cost = 2
        self.set_image("hong")
        return self

    def ai_value(self):
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
    def setup(self):
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

        # miku heals it to 4hp on play - makes it actually tanky
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
    def setup(self):
        self.name = "Thorn"
        self.desc = "Taunt: 1. Deals 2 damage back to anyone who attacks it."
        self.taunt = 1
        self.hp = 3
        self.atk = 1
        self.cost = 2
        self.set_image("thorn")
        return self

    def ai_value(self):
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
        particles = []
        if self.dead == False:
            particles.extend(self.on_attacked(target))
        return particles

    def on_attacked(self, attacker):
        particles = []
        if self.hp <= 0:
            self.die()
            particles.extend(attacker.owner.commander.on_enemy_death(self))
        attacker.hp -= 2
        particles.append(Particle(attacker.x + attacker.w/2, attacker.y + attacker.h/2, -2, self.particle_font, self.hp_color_font, self.atk_color_font))
        attacker.attacked(self)
        return particles


class Medic(Card):
    def setup(self):
        self.name = "Medic"
        self.desc = "Heals your commander for 2 HP at the start of your turn."
        self.hp = 4
        self.atk = 0
        self.cost = 2
        self.set_image("medic")
        return self

    def ai_value(self):
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

        # jesus heals a random ally too - medic might get topped by jesus
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
        self.owner.commander.hp += 2
        return [Particle(self.owner.commander_position[0]+self.owner.commander.w//2+randint(-32,32), self.owner.commander_position[1]+self.owner.commander.h//2+randint(-32,32), 2, self.particle_font, self.hp_color_font, self.atk_color_font)]


class Sponge(Card):
    def setup(self):
        self.name = "Sponge"
        self.desc = "Gains +1 ATK every time it is attacked and survives."
        self.hp = 4
        self.atk = 1
        self.cost = 2
        self.set_image("sponge")
        return self

    def ai_value(self):
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
        particles = []
        if self.hp > 0:
            self.atk += 1
        return particles


class Kamikaze(Card):
    def setup(self):
        self.name = "Kamikaze"
        self.desc = "Deals 5 damage to the enemy commander and dies immediately."
        self.hp = 0
        self.atk = 5
        self.cost = 6
        self.spell = True
        self.set_image("kamikaze")
        return self

    def ai_value(self):
        enemy = get_enemy(self.owner)
        game = self.owner.game

        # if we can kill the commander this is the highest priority
        if enemy.commander.hp <= self.atk:
            return 2000  # always play, no exceptions

        # kombination kill check - kamikaze + board damage = lethal
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
        particles = []
        for player in self.owner.game.players:
            if player != self.owner:
                player.commander.hp -= 8
                particles.extend(player.commander.attacked(self))
                particles.append(Particle(player.commander.x+player.commander.w/2, player.commander.y+player.commander.h/2, -10, self.particle_font, self.hp_color_font, self.atk_color_font))
        self.hp = 0
        self.die()
        return particles


class Bin(Card):
    def setup(self):
        self.name = "Bin"
        self.desc = "Draw 1 card. Haste."
        self.hp = 2
        self.atk = 0
        self.cost = 2
        self.haste = True
        self.selection_type = ""
        self.set_image("bin")
        return self

    def on_action(self):
        self.owner.draw(1, cost=0)
        self.actions -= 1
        return []

    def ai_value(self):
        enemy = get_enemy(self.owner)
        game = self.owner.game
        hand_size = len(self.owner.hand)
        deck_size = len(self.owner.deck)

        # core value: low hand means bin is very good
        hand_scarcity = max(0, (5 - hand_size)) * 10  # sharper scaling

        # if they have more cards than us thats very bad
        card_adv = (len(enemy.hand) - hand_size) * 10


        # haste means we draw AND still have board presence this turn
        haste_premium = 12

        base = 14 + hand_scarcity + card_adv + haste_premium
        return int(base)


class Retriever(Card):
    def setup(self):
        self.name = "Retriever"
        self.desc = "Draw 1 card for 1 mana."
        self.hp = 2
        self.atk = 0
        self.cost = 2
        self.max_actions = 2
        self.selection_type = ""
        self.set_image("retriever")
        return self

    def ai_value(self):
        enemy = get_enemy(self.owner)
        hand_size = len(self.owner.hand)
        deck_size = len(self.owner.deck)

        # retriever costs mana to use (1 per draw) unlike bin which is free
        hand_scarcity = (3 - hand_size) * 10


        card_adv = max(0, len(enemy.hand) - hand_size) * 7


        base = hand_scarcity + card_adv
        return max(2, int(base))

    def on_action(self):
        if self.owner.mana > 0:
            self.actions -= 1
            self.owner.draw(1, cost=1)
        else:
            self.actions -= 1
        return []


class Musketeer(Card):
    def setup(self):
        self.name = "Musketeer"
        self.desc = "Ignores Taunt."
        self.ignore_taunt = True
        self.hp = 1
        self.atk = 3
        self.cost = 3
        self.set_image("musketeer")
        return self

    def ai_value(self):
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

        # shadow gains mana from kills - musketeer can kill engine cards for profit
        if self.owner.commander.name == "Shadow" and enemy_has_taunt:
            base += 15

        return max(5, base)


class Net(Card):
    def setup(self):
        self.name = "Net"
        self.desc = "Play one card for free."
        self.selection_type = "hand"
        self.hp = 1
        self.atk = 0
        self.cost = 3
        # self.haste = True
        self.set_image("net")
        return self

    def ai_value(self):
        playable_via_net = [c for c in self.owner.hand if c.name != "Net"]
        if not playable_via_net:
            return 0  # empty hand - net draws nothing

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
        target.play(False)
        self.actions -= 1
        self.hp = 0
        self.die()
        return []


class BagOfGold(Card):
    def setup(self):
        self.name = "Gold Bag"
        self.desc = "Gives 1 mana."
        self.spell = True
        self.hp = 0
        self.atk = 0
        self.cost = 0
        self.set_image("bagofgold")
        return self

    def ai_value(self):
        current_mana = self.owner.mana
        game = self.owner.game

        # alchemist draws a card every time a spell is played - bag is basically a free draw
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
        self.owner.mana += 1
        self.hp = 0
        self.die()
        return [Particle(self.owner.mana_position[0], self.owner.mana_position[1], 1, self.particle_font, self.hp_color_font, self.atk_color_font)]


class Snowball(Card):
    def setup(self):
        self.name = "Snowball"
        self.desc = "Gets +1/+1 per turn"
        self.hp = 1
        self.atk = 0
        self.cost = 4
        self.retreat_cost = 10
        self.set_image("snowball")
        return self

    def ai_value(self):
        has_taunt = is_protected(self.owner)
        game = self.owner.game
        enemy = get_enemy(self.owner)

        # snowball without taunt dies immediately - it starts as a 0/1
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

        # sonic gives haste - snowball can attack immediately and still grow
        sonic_bonus = 25 if self.owner.commander.name == "Sonic" else 0

        # jesus randomly heals allies - snowball might get topped
        jesus_bonus = 10 if self.owner.commander.name == "Jesus" else 0

        base = int((current_value + growth_value + urgency_bonus) * cover_factor)
        return max(1, base + sonic_bonus + jesus_bonus)

    def on_turn_start(self):
        self.atk += 1
        self.hp += 1
        return []


class B52(Card):
    def setup(self):
        self.name = "B52"
        self.desc = "Deals 1 damage to every enemy card."
        self.spell = True
        self.hp = float("inf")
        self.atk = 0
        self.cost = 2
        self.set_image("b52")
        return self

    def ai_value(self):
        enemy = get_enemy(self.owner)

        # what can we kill (1hp cards die immediately)
        kills = [c for c in enemy.active if c.hp <= 1]
        # what do we weaken to 1hp (making them vulnerable to anything)
        weakened = [c for c in enemy.active if 1 < c.hp <= 2]

        kill_value = sum(stat_value(c) for c in kills)
        weaken_value = sum(int(stat_value(c) * 0.4) for c in weakened)

        # killing multiple cards at once is exponentially good (clears threats AND draws from glados)
        board_clear_bonus = len(kills) * (len(kills) - 1) * 14

        # even better when commander is low - cleared board means easier attacks
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
        particles = []
        for i in range(5):
            for player in self.owner.game.players:
                if player != self.owner:
                    for card in player.active:
                        card.hp -= 1
                        card.attacked(self)
                        particles.append(Particle(card.x+card.w//2, card.y+card.h//2, -1, self.particle_font, self.hp_color_font, self.atk_color_font))
        self.hp = 0
        self.die()
        return particles
    
class FatMan(Card):
    def setup(self):
        self.name = "Fat Man"
        self.desc = "Kills every card."
        self.spell = True
        self.hp = float("inf")
        self.atk = 0
        self.cost = 7
        self.set_image("fat_man")
        return self

    def ai_value(self):
        enemy = get_enemy(self.owner)
        own = self.owner

        # what do we gain from wiping the enemy board
        enemy_wipe_value = sum(stat_value(c) for c in enemy.active)

        # what do we lose from wiping our own board
        # pumps and medics hurt a lot to lose
        own_wipe_cost = sum(stat_value(c) for c in own.active)
        engine_loss = len([c for c in own.active if c.name in ("Pump", "Medic")]) * 25

        # net board impact - positive = wipe benefits us
        net = enemy_wipe_value - own_wipe_cost - engine_loss

        # specifically great against massive grown threats we cant kill normally
        scary_threats = [c for c in enemy.active if c.atk >= 5 or c.__class__.__name__ in ("Snowball", "Sponge")]
        threat_bonus = sum(c.atk * 8 for c in scary_threats)

        # taunt walls we cant punch through - fat man bypasses all of that
        taunt_wall_hp = sum(c.hp for c in enemy.active if c.taunt > 0)
        wall_bonus = taunt_wall_hp * 4

        # if we're ahead on board this is self-sabotage - dont do it
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
        particles = []
        for i in range(5):
            for player in self.owner.game.players:
                for card in player.active:
                    card.hp -= 99
                    card.attacked(self)
                    particles.append(Particle(card.x+card.w//2, card.y+card.h//2, -99, self.particle_font, self.hp_color_font, self.atk_color_font))
        self.hp = 0
        self.die()
        return particles