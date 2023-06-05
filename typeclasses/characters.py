"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""
from evennia.objects.objects import DefaultCharacter
from .objects import ObjectParent
from evennia.utils import lazy_property
from world.traits import TraitHandler
from world.dice_roller import return_a_roll as roll
from world.dice_roller import return_a_roll_sans_crits as rarsc
from evennia.utils.logger import log_file


class Character(ObjectParent, DefaultCharacter):
    """
    The Character defaults to reimplementing some of base Object's hook methods with the
    following functionality:

    at_basetype_setup - always assigns the DefaultCmdSet to this object type
                    (important!)sets locks so character cannot be picked up
                    and its commands only be called by itself, not anyone else.
                    (to change things, use at_object_creation() instead).
    at_post_move(source_location) - Launches the "look" command after every move.
    at_post_unpuppet(account) -  when Account disconnects from the Character, we
                    store the current location in the pre_logout_location Attribute and
                    move it to a None-location so the "unpuppeted" character
                    object does not need to stay on grid. Echoes "Account has disconnected"
                    to the room.
    at_pre_puppet - Just before Account re-connects, retrieves the character's
                    pre_logout_location Attribute and move it back on the grid.
    at_post_puppet - Echoes "AccountName has entered the game" to the room.

    """

    # pull in handler for traits and trait-like attributes
    @lazy_property
    def traits(self):
        """TraitHandler that manages character traits."""
        return TraitHandler(self)
    
    
    @lazy_property
    def ability_scores(self):
        """TraitHandler that manages character ability scores."""
        return TraitHandler(self, db_attribute='ability_scores')


    # add all necessary traits and other info to new character object at creation
    def at_object_creation(self):
        "Called only at object creation and with update command."
        # clear traits, ability_scores, talents, and mutations
        self.traits.clear()
        self.ability_scores.clear()
        
        # add in ability scores
        self.ability_scores.add(key='Dex', name='Dexterity', type='static', \
                        base=rarsc(100), extra={'learn' : 0})
        self.ability_scores.add(key='Str', name='Strength', type='static', \
                        base=rarsc(100), extra={'learn' : 0})
        self.ability_scores.add(key='Vit', name='Vitality', type='static', \
                        base=rarsc(100), extra={'learn' : 0})
        self.ability_scores.add(key='Per', name='Perception', type='static', \
                        base=rarsc(100), extra={'learn' : 0})
        self.ability_scores.add(key='Cha', name='Charisma', type='static', \
                        base=rarsc(100), extra={'learn' : 0})
        
        # add in traits for essence, mass, encumberance
        # note that essence is a combined health, stamina, and willpower bar
        # all damage and extertion done by the character depletes this commmon pooled resource
        self.traits.add(key="ep", name="Essence Points", type="gauge", \
                        base=(self.ability_scores.Vit.current + \
                        self.ability_scores.Cha.current + \
                        self.ability_scores.Str.current), extra={'learn' : 0})
        self.traits.add(key="mass", name="Mass", type='static', \
                        base=rarsc(180, dist_shape='very flat'), extra={'learn' : 0})
        self.traits.add(key="enc", name="Encumberance", type='counter', \
                        base=0, max=(self.ability_scores.Str.current * .5), extra={'learn' : 0})
        
        # add in initial equipment slots for the character
        self.db.slots = {
            'head': None,
            'face': None,
            'ears': None,
            'neck': None,
            'chest': None,
            'back': None,
            'waist': None,
            'quiver': None,
            'shoulders': None,
            'arms': None,
            'hands': None,
            'ring': None,
            'legs': None,
            'feet': None,
            'main hand': None,
            'off hand': None
        }
        # Add in info db to store other useful tidbits we'll need
        self.db.info = {'Target': None, 'Mercy': True, 'Default Attack': 'unarmed_strike', \
                        'In Combat': False, 'Position': 'standing', 'Sneaking' : False, \
                        'Wimpy': 100, 'Yield': 200, 'Title': None}
        # money
        self.db.wallet = {'GC': 0, 'SC': 0, 'CC': 0}