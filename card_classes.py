from main_classes import Card
from classes import Particle
from random import randint

AI_CONFIG = {
    "fragile_classes": ("Pump", "Medic", "Musketeer", "Sponge", "Snowball"),
    "attacker_targets": {
        "early": (0, 3),
        "mid": (2, 4),
        "late": (5, 4)
    },
    "limits": {
        "Pump": {"soft": 3, "hard": 4},
        "Taunt": {"soft": 2, "hard": 3},
        "Medic": {"soft": 1, "hard": 2}
    }
}

def get_enemy(player):
    return next(p for p in player.game.players if p != player)

def is_protected(player):
    return any(c.taunt > 0 for c in player.active)

def get_attacker_target(turn):
    target = AI_CONFIG["attacker_targets"]["early"][1]
    if turn >= AI_CONFIG["attacker_targets"]["late"][0]:
        target = AI_CONFIG["attacker_targets"]["late"][1]
    elif turn >= AI_CONFIG["attacker_targets"]["mid"][0]:
        target = AI_CONFIG["attacker_targets"]["mid"][1]
    return target

def count_active_by_name(player, class_name):
    return len([c for c in player.active if c.__class__.__name__ == class_name])

def stat_value(card):
    """Flat estimate of a card's worth from raw stats alone — never recurses."""
    return card.cost * 10 + card.atk * 3 + card.hp * 2

# cards
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
 
        # cheap filler
        one_shot_targets = len([c for c in enemy.active if c.hp <= 1 and c.taunt == 0])
        kill_bonus = one_shot_targets * 10
 
        early_bonus = max(0, 15 - game.turn * 2)
 
        board_deficit = len(enemy.active) - len(self.owner.active)
        presence_bonus = board_deficit * 6
 
        # miku loves cheap stuff
        miku_bonus = 20 if self.owner.commander.name == "Miku" else 0
 
        # sonic loves anything it can swing with immediately
        sonic_bonus = 10 if self.owner.commander.name == "Sonic" else 0
 
        own_attackers = len([c for c in self.owner.active if c.atk > 0])
        attacker_target = get_attacker_target(game.turn)
        saturation_penalty = max(0, (own_attackers - attacker_target) * 8)
 
        base = 14 + early_bonus + kill_bonus + presence_bonus + miku_bonus + sonic_bonus - saturation_penalty
        return max(5, base)
    
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

        # throw more bodies
        board_deficit = len(enemy.active) - len(self.owner.active)
        presence_bonus = board_deficit * 8

        # w early game card
        early_bonus = max(0, 20 - game.turn * 2)

        trade_targets = len([c for c in enemy.active if c.hp <= 2 and c.taunt == 0])
        trade_bonus = trade_targets * 7

        # miku!!!!!
        miku_bonus = 15 if self.owner.commander.name == "Miku" else 0

        # sonic!!!!!!!
        sonic_bonus = 12 if self.owner.commander.name == "Sonic" else 0

        # amogus is worse than others
        own_attackers = len([c for c in self.owner.active if c.atk > 0])
        attacker_target = get_attacker_target(game.turn)
        saturation_penalty = max(0, (own_attackers - attacker_target) * 10)

        base = 22 + early_bonus + presence_bonus + trade_bonus + miku_bonus + sonic_bonus - saturation_penalty
        return max(5, base)

class Pump(Card):
    def setup(self):
        self.name = "Pump"
        self.desc = "Generates 1 energy per turn"
        self.hp = 5
        self.atk = 0
        self.cost = 1
        self.retreat_cost = 5
        self.set_image("pump")
        return self
    
    def ai_value(self):
        pumps_active = count_active_by_name(self.owner, "Pump")
        if pumps_active >= AI_CONFIG["limits"]["Pump"]["hard"]:
            return 0

        game = self.owner.game
        enemy = get_enemy(self.owner)

        # early pump better i think
        estimated_turns_remaining = max(2, 18 - game.turn)
        mana_value = min(estimated_turns_remaining, 12) * 3

        # diminishing returns
        pump_decay = pumps_active * 15
        base = mana_value - pump_decay

        # biden economics
        if self.owner.commander.name == "Biden":
            base += 25

        # mana cap check
        mana_cap = game.turn_mana * 2
        if self.owner.mana >= mana_cap - 1:
            base = int(base * 0.5)

        # will it live
        enemy_total_atk = sum(c.atk for c in enemy.active)
        has_taunt = is_protected(self.owner)

        if not has_taunt:
            if enemy_total_atk >= 5:
                return 0
            elif enemy_total_atk >= 3:
                base = int(base * 0.25)
            elif enemy_total_atk >= 1:
                base = int(base * 0.55)
        else:
            # taunt sucks
            taunt_hp = sum(c.hp for c in self.owner.active if c.taunt > 0)
            if taunt_hp < enemy_total_atk:
                base = int(base * 0.7)

        return max(0, int(base))

    def on_turn_start(self):
        self.owner.mana += 1
        return [Particle(self.owner.mana_position[0]+randint(-32,32), self.owner.mana_position[1]+randint(-32,32), 1, self.font, self.hp_color_font, self.atk_color_font)]

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

        # imagine a hong with haste...
        killable_next_turn = [c for c in enemy.active if c.hp <= 5]
        kill_bonus = len(killable_next_turn) * 12

        # will live?
        safe_from = [c for c in enemy.active if c.atk < 4]
        survive_bonus = len(safe_from) * 4

        if enemy.commander.hp <= 15:
            commander_pressure = (15 - enemy.commander.hp) * 3
        else:
            commander_pressure = 0

        # need to throw bodies at the problem
        own_attackers = len([c for c in self.owner.active if c.atk > 0])
        attacker_target = get_attacker_target(game.turn)
        need_bonus = 20 if own_attackers < attacker_target else 0

        # shadow!!!
        shadow_bonus = 15 if self.owner.commander.name == "Shadow" else 0

        # sonic!!!
        sonic_bonus = 20 if self.owner.commander.name == "Sonic" else 0

        base = 32 + kill_bonus + survive_bonus + commander_pressure + need_bonus + shadow_bonus + sonic_bonus
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
            return 2

        enemy = get_enemy(self.owner)

        enemy_total_atk = sum(c.atk for c in enemy.active)

        protected_value = 0
        for c in self.owner.active:
            if c.__class__.__name__ in AI_CONFIG["fragile_classes"]:
                protected_value += stat_value(c) // 3

        # fragile units will die to everything
        no_taunt_urgency = 35 if taunts_active == 0 else 8

        # taunt is partially countered
        musketeer_threat = any(c.__class__.__name__ == "Musketeer" for c in enemy.active)
        ignore_penalty = 20 if musketeer_threat else 0

        # miku!!!!!
        miku_bonus = 18 if self.owner.commander.name == "Miku" else 0

        # IceCube keeps sponge alive to grow
        sponge_on_board = any(c.__class__.__name__ == "Sponge" for c in self.owner.active)
        sponge_bonus = 15 if sponge_on_board else 0

        base = (enemy_total_atk * 4) + protected_value + no_taunt_urgency + miku_bonus + sponge_bonus - ignore_penalty
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
            return 2

        enemy = get_enemy(self.owner)

        # potential kils
        kills_via_retaliation = [c for c in enemy.active if c.hp <= 2]
        crippled_by_retaliation = [c for c in enemy.active if 2 < c.hp <= 4]
        kill_bonus = len(kills_via_retaliation) * 22
        cripple_bonus = len(crippled_by_retaliation) * 8

        # distraction for big evil cards
        strong_attackers = len([c for c in enemy.active if c.atk >= 3])
        strong_punish = strong_attackers * 10

        own_attack_value = len([c for c in enemy.active if c.hp <= 1]) * 5

        fragile_units = len([c for c in self.owner.active if c.__class__.__name__ in AI_CONFIG["fragile_classes"]])
        protect_bonus = fragile_units * 8

        no_taunt_bonus = 22 if taunts_active == 0 else 6

        enemy_has_attackers = any(c.atk > 0 for c in enemy.active)
        if not enemy_has_attackers:
            return max(5, no_taunt_bonus + protect_bonus)

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
        particles.append(Particle(attacker.x + attacker.w/2, attacker.y + attacker.h/2, -2, self.font, self.hp_color_font, self.atk_color_font))
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
            return 0

        enemy = get_enemy(self.owner)
        game = self.owner.game
        hp_deficit = 25 - self.owner.commander.hp

        # want to get to 25
        if hp_deficit <= 0:
            return 3

        turns_estimate = max(2, 16 - game.turn // 2)
        total_heal = min(hp_deficit, turns_estimate * 2)
        heal_value = total_heal * 3

        # weak weak
        has_taunt = is_protected(self.owner)
        enemy_total_atk = sum(c.atk for c in enemy.active)
        
        if not has_taunt:
            if enemy_total_atk >= 3:
                return max(2, int(heal_value * 0.1))
            else:
                heal_value = int(heal_value * 0.5)

        # jesus heals
        jesus_overlap = 10 if self.owner.commander.name == "Jesus" else 0

        # is commander about to die?
        urgency_multiplier = 1.0
        if self.owner.commander.hp <= 10:
            urgency_multiplier = 1.8
        elif self.owner.commander.hp <= 15:
            urgency_multiplier = 1.3

        base = int((heal_value - jesus_overlap) * urgency_multiplier)
        return max(3, base)

    def on_turn_start(self):
        self.owner.commander.hp += 2
        return [Particle(self.owner.commander_position[0]+self.owner.commander.w//2+randint(-32,32), self.owner.commander_position[1]+self.owner.commander.h//2+randint(-32,32), 2, self.font, self.hp_color_font, self.atk_color_font)]

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

        # has to be protected
        if not has_taunt:
            return max(3, self.atk * 2)

        current_value = self.atk * 9 + self.hp * 2

        growth_triggers = len([c for c in enemy.active if 0 < c.atk < self.hp])
        growth_value = growth_triggers * 14

        longevity = min(game.turn * 2, 25)

        turns_to_lethal = max(1, enemy.commander.hp - self.atk)
        urgency = max(0, 30 - turns_to_lethal * 4)

        # how good is coverage
        taunt_stability = sum(c.hp for c in self.owner.active if c.taunt > 0)
        enemy_pressure = sum(c.atk for c in enemy.active)
        coverage_factor = min(1.0, taunt_stability / max(enemy_pressure, 1))

        # sonic is kinda broken
        sonic_bonus = 25 if self.owner.commander.name == "Sonic" else 0

        # shadow!!!
        shadow_bonus = 12 if self.owner.commander.name == "Shadow" and self.atk >= 3 else 0

        base = int((current_value + growth_value + longevity + urgency) * coverage_factor)
        return base + sonic_bonus + shadow_bonus

    def on_attacked(self, attacker):
        particles = []
        if self.hp > 0:
            self.atk += 1
        return particles
    
class Kamikaze(Card):
    def setup(self):
        self.name = "Kamikaze"
        self.desc = "Deals 10 damage to the enemy commander and dies immediately."
        self.hp = 0
        self.atk = 10
        self.cost = 6
        self.spell = True
        self.set_image("kamikaze")
        return self
    
    def ai_value(self):
        enemy = get_enemy(self.owner)
        game = self.owner.game

        if enemy.commander.hp <= 10:
            return 2000

        total_own_atk = sum(c.atk for c in self.owner.active if c.actions > 0)
        if 10 + total_own_atk >= enemy.commander.hp:
            return 1500  # Kamikaze + board = lethal this turn

        damage_pct = 10 / max(enemy.commander.hp, 1)
        pct_bonus = int(damage_pct * 80)  # up to 80 pts if fully fresh


        losing_margin = len(enemy.active) - len(self.owner.active)
        bypass_bonus = max(0, losing_margin * 15)

        # Also valuable if enemy has Thorn/taunt wall 
        enemy_taunt_wall = sum(c.taunt for c in enemy.active)
        wall_bypass = enemy_taunt_wall * 10

        # cards would be a better use of mana
        spare_mana = max(0, self.owner.mana - self.cost)
        wasted_mana_penalty = spare_mana * 3  # small penalty for leftover mana

        base = 18 + pct_bonus + bypass_bonus + wall_bypass - wasted_mana_penalty
        return max(5, base)

    def on_play(self):
        particles = []
        for player in self.owner.game.players:
            if player != self.owner:
                player.commander.hp -= 10
                particles.extend(player.commander.attacked(self))
                particles.append(Particle(player.commander.x+player.commander.w/2, player.commander.y+player.commander.h/2, -10, self.font, self.hp_color_font, self.atk_color_font))
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

        # fewer cards in hand
        hand_scarcity = (hand_size - 4) * 7

        # lots of mana but nothing to spend it on
        playable_cards = len([c for c in self.owner.hand if c.cost <= self.owner.mana and c.name != "Bin"])
        mana_hunger = max(0, self.owner.mana - max(playable_cards, 1) * 2) * 4

        card_adv = max(0, len(enemy.hand) - hand_size) * 8

        deck_penalty = max(0, 6 - deck_size) * 4

        haste_premium = 8

        board_presence = 5

        base = 12 + hand_scarcity + mana_hunger + card_adv + haste_premium + board_presence - deck_penalty
        return max(0, int(base))
    
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
    
    def on_action(self):
        if self.owner.mana > 0:
            self.actions -= 1
            self.owner.draw(1, cost=1)
        return []
    
    def ai_value(self):
        enemy = get_enemy(self.owner)
        hand_size = len(self.owner.hand)
        deck_size = len(self.owner.deck)

        # retriever is less efficient than bin
        hand_scarcity = max(0, 6 - hand_size) * 5

        spare_mana_after_play = self.owner.mana - self.cost
        usability_now = min(spare_mana_after_play * 8, 20) if spare_mana_after_play > 0 else 0

        card_adv = max(0, len(enemy.hand) - hand_size) * 6

        deck_penalty = max(0, 4 - deck_size) * 6

        persistence_bonus = 8

        base = 8 + hand_scarcity + usability_now + card_adv + persistence_bonus - deck_penalty
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
            non_taunt_targets = [c for c in enemy.active if c.taunt == 0]
            if non_taunt_targets:
                best_target_value = max(stat_value(c) for c in non_taunt_targets)
                commander_snipe = max(0, 20 - enemy.commander.hp) * 2
            else:
                best_target_value = 20
                commander_snipe = max(5, 30 - enemy.commander.hp)

            engine_targets = len([c for c in non_taunt_targets if c.name in ("Pump", "Medic")])
            engine_bonus = engine_targets * 18

            base = 45 + best_target_value // 2 + commander_snipe + engine_bonus
        else:
            one_shot_targets = len([c for c in enemy.active if c.hp <= 3])
            base = 12 + one_shot_targets * 8

        has_taunt = is_protected(self.owner)
        if not has_taunt:
            base = int(base * 0.5)

        if self.owner.commander.name == "Sonic":
            base += 30

        if self.owner.commander.name == "Shadow" and enemy_has_taunt:
            base += 12

        return max(5, base)
    
class Net(Card):
    def setup(self):
        self.name = "Net"
        self.desc = "Play one card for free. Haste."
        self.selection_type = "hand"
        self.hp = 1
        self.atk = 0
        self.cost = 3
        self.haste = True
        self.set_image("net")
        return self
    
    def ai_value(self):
        playable_via_net = [c for c in self.owner.hand if c.name != "Net"]
        if not playable_via_net:
            return 0

        best_card = max(playable_via_net, key=lambda c: stat_value(c))
        best_val = stat_value(best_card)
        best_cost = best_card.cost

        if best_val >= 500:
            return 1500

        currently_unaffordable = best_cost > self.owner.mana - self.cost
        unaffordable_bonus = (best_cost - 3) * 6 if currently_unaffordable else (best_cost - 3) * 3

        combo_bonus = 0
        if best_card.name == "BagOfGold":
            affordable_after = len([c for c in self.owner.hand
                                     if c.name not in ("Net", "BagOfGold")
                                     and c.cost <= self.owner.mana - self.cost + 1])
            combo_bonus = affordable_after * 10

        base = best_val + max(0, unaffordable_bonus) + combo_bonus
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

        # w alchemist
        alchemist_bonus = 40 if self.owner.commander.name == "Alchemist" else 0

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

        chain_bonus = 0
        if best_enabled_card is not None:
            remaining_after = current_mana + 1 - best_enabled_card.cost
            follow_up = [c for c in self.owner.hand
                         if c is not self and c is not best_enabled_card
                         and c.cost <= remaining_after]
            if follow_up:
                chain_bonus = max(stat_value(c) for c in follow_up) // 3

        #ccap bad
        mana_cap = game.turn_mana * 2
        cap_penalty = 20 if current_mana >= mana_cap else 0

        base_intrinsic = 3

        base = alchemist_bonus + best_enabled_val + chain_bonus + base_intrinsic - cap_penalty
        return max(1, base)

    def on_play(self):
        self.owner.mana += 1
        self.hp = 0
        self.die()
        return [Particle(self.owner.mana_position[0], self.owner.mana_position[1], 1, self.font, self.hp_color_font, self.atk_color_font)]

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

        # taunt protection
        if not has_taunt:
            return 1

        current_value = self.atk * 7 + self.hp * 2

        # gdp growth graph ts
        turns_remaining = max(2, 20 - game.turn)
        # projected total damage output
        projected_damage = self.atk * turns_remaining + (turns_remaining * (turns_remaining + 1)) // 2
        growth_value = min(projected_damage * 2, 100)

        # KILL COMANNDER!!!!!!
        turns_to_lethal = max(1, enemy.commander.hp - self.atk)
        urgency_bonus = max(0, 40 - turns_to_lethal * 5)

        # is taunt real????
        taunt_total_hp = sum(c.hp for c in self.owner.active if c.taunt > 0)
        enemy_total_atk = sum(c.atk for c in enemy.active)

        cover_turns = taunt_total_hp / max(enemy_total_atk, 1)
        cover_factor = min(1.0, cover_turns / max(turns_to_lethal, 1))

        # i love sonic i love sonic i love sonic
        sonic_bonus = 20 if self.owner.commander.name == "Sonic" else 0

        base = int((current_value + growth_value + urgency_bonus) * cover_factor)
        return max(1, base + sonic_bonus)

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
        own = self.owner

        # kd ratio?
        kills = [c for c in enemy.active if c.hp <= 1]
        weakened = [c for c in enemy.active if 1 < c.hp <= 2]

        # value of kills
        kill_value = sum(stat_value(c) for c in kills)

        weaken_value = sum(int(stat_value(c) * 0.35) for c in weakened)

        # board wipe?????????
        board_clear_bonus = len(kills) * (len(kills) - 1) * 12

        # more valuable when their commander is already low on HP
        if len(kills) >= 2 and enemy.commander.hp <= 15:
            lane_clear_bonus = (15 - enemy.commander.hp) * 3
        else:
            lane_clear_bonus = 0

        # B52 is especially good at killing fragile high-value targets
        fragile_kills = [c for c in kills if c.__class__.__name__ in AI_CONFIG["fragile_classes"]]
        fragile_bonus = len(fragile_kills) * 15

        # nothing ever happens...
        if not kills and not weakened:
            return 2

        base = kill_value + weaken_value + board_clear_bonus + lane_clear_bonus + fragile_bonus
        return max(2, int(base))

    def on_play(self):
        particles = []
        
        for player in self.owner.game.players:
            if player != self.owner:
                for card in player.active:
                    card.hp -= 1
                    card.attacked(self)
                    particles.append(Particle(card.x+card.w//2, card.y+card.h//2, -1, self.font, self.hp_color_font, self.atk_color_font))
        self.hp = 0
        self.die()
        return particles