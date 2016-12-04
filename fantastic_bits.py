# Submission of justhalf for CodinGame contest "Fantastic Bits"
# Reduced to remove the logic, showing only the classes
import sys
import math

# Grab Snaffles and try to throw them through the opponent's goal!
# Move towards a Snaffle and use your team id to determine where you need to throw it.

def debug(msg, end='\n'):
    print(msg, file=sys.stderr, end=end)

my_team_id = int(input())  # if 0 you need to score on the right of the map, if 1 you need to score on the left
X_LIMIT = 16000
Y_LIMIT = 7500

def dist(point1, point2):
    return point1.sub(point2).norm()

def ccw(A,B,C):
    return (C.y-A.y) * (B.x-A.x) > (B.y-A.y) * (C.x-A.x)

# Return true if line segments AB and CD intersect
def intersect(A,B,C,D):
    try:
        return ccw(A,C,D) != ccw(B,C,D) and ccw(A,B,C) != ccw(A,B,D)
    except:
        return False

class Point(object):
    def __init__(self, x, y):
        self.x = (x)
        self.y = (y)
    
    def norm(self):
        return math.sqrt(self.x**2 + self.y**2)
    
    def add(self, point):
        return Point(self.x+point.x, self.y+point.y)
    
    def sub(self, point):
        return Point(self.x-point.x, self.y-point.y)
    
    def dot(self, point):
        return self.x*point.x + self.y*point.y
    
    def mul(self, val):
        return Point(self.x*val, self.y*val)
    
    def mulx(self, val):
        return Point(self.x*val, self.y)
    
    def muly(self, val):
        return Point(self.x, self.y*val)
    
    def round(self):
        return Point(round(self.x), round(self.y))
    
    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):
        return '{:.2f} {:.2f}'.format(self.x, self.y)
        
GOAL_TL = Point(0, 1750)
GOAL_BL = Point(0, 5750)
GOAL_CL = Point(0, 3750)

GOAL_TR = Point(16000, 1750)
GOAL_TR_IN = Point(16000, 2300)
GOAL_BR = Point(16000, 5750)
GOAL_BR_IN = Point(16000, 5200)
GOAL_CR = Point(16000, 3750)

class Entity(object):
    def __init__(self, _id, posx, posy, vx, vy):
        self._id = _id
        if my_team_id == 1:
            posx = X_LIMIT - posx
        self._pos = [Point(posx, posy)]
        self._v = [Point(vx, vy)]
    
    @property
    def pos(self):
        # By using Python's property, I can keep track of past 4 positions =)
        return self._pos[0]
    
    @pos.setter
    def pos(self, val):
        self._pos[:] = self._pos[:3]
        if my_team_id == 1:
            val = Point(X_LIMIT-val.x, val.y)
        self._pos.insert(0, val)
    
    @property
    def v(self):
        return self._v[0]
    
    @v.setter
    def v(self, val):
        self._v[:] = self._v[:3]
        if my_team_id == 1:
            val = Point(-val.x, val.y)
        self._v.insert(0, val)
    
    def next_pos(self, thrust=None, target=None):
        if thrust is None:
            thrust = self.def_thrust
        if target is None:
            if self.v.norm() == 0:
                dir_vec = Point(0,0)
            else:
                dir_vec = self.v.mul(1/self.v.norm())
        else:
            diff = target.sub(self.pos)
            dir_vec = diff.mul(1/diff.norm())
        thrust_vec = dir_vec.mul(thrust/self.mass)
        new_v = self.v.add(thrust_vec)
        return self.pos.add(new_v)    
        
    def pos_after(self, n):
        v = self.v.round()
        pos = self.pos.round()
        for i in range(n):
            pos = pos.add(v).round()
            v = v.mul(self.deaccel).round()
        return pos
    
    def __repr__(self):
        return '{}:({},{})'.format(self._id, self.pos.x, self.pos.y)

MOVE = 'MOVE'
THROW = 'THROW'
OBLIVIATE = 'OBLIVIATE'
PETRIFICUS = 'PETRIFICUS'
ACCIO = 'ACCIO'
FLIPENDO = 'FLIPENDO'

class Wizard(Entity):
    def __init__(self, _id, posx, posy, vx, vy, state):
        super().__init__(_id, posx, posy, vx, vy)
        self._state = [state]
        self.has_acted = False
        self._action = []
        self.mass = 1
        self.def_thrust = 100
        self.deaccel = 0.75
        self.radius = 400
        self.snaffles_list = None
        self.opp_list = None
        self._snaffle_target = []
        self.other_wizard = None
    
    @property
    def action(self):
        if len(self._action) == 0:
            return None
        return self._action[0]
    
    @action.setter
    def action(self, val):
        self._action[:] = self._action[:3]
        self._action.insert(0, val)
        
    @property
    def snaffle_target(self):
        if len(self._snaffle_target) == 0:
            return None
        return self._snaffle_target[0]
    
    @snaffle_target.setter
    def snaffle_target(self, val):
        self._snaffle_target[:] = self._snaffle_target[:3]
        self._snaffle_target.insert(0, val)
        
    @property
    def state(self):
        return self._state[0]
    
    @state.setter
    def state(self, val):
        self._state[:] = self._state[:3]
        self._state.insert(0, val)
    
    def sort_snaffles(self, snaffles):
        self.snaffles_list = sorted(snaffles[:], key=lambda x: x.pos.sub(self.pos).norm())
        if self.snaffles_list[0].pos_after(3).x >= X_LIMIT:
            self.snaffles_list = self.snaffles_list[1:]+self.snaffles_list[0:1]
        if self._id % 2 == 0 and len(self.snaffles_list) > 1:
            snaffle0, snaffle1 = self.snaffles_list[:2]
            dist0, dist1 = snaffle0.pos.sub(self.pos).norm(), snaffle1.pos.sub(self.pos).norm()
            if abs(dist0-dist1) < 1000 and snaffle0.pos.x - snaffle1.pos.x > 500:
                self.snaffles_list[:2] = [snaffle1, snaffle0]
    
    def sort_opp(self, opp_wizards):
        self.opp_list = sorted(opp_wizards[:], key=lambda x: x.pos.sub(self.pos).norm())
    
    def set_action_str(self, action_str):
        self.action_str = action_str
    
    def execute(self):
        print(self.action_str)
    
    def move(self, target, thrust):
        if self.has_acted:
            debug('Wizard {} has acted, cannot move to {}'.format(self._id, target))
            return False
        self.has_acted = True
        self.action = MOVE
        x = target.x if my_team_id == 0 else X_LIMIT-target.x
        self.set_action_str('{} {:.0f} {:.0f} {:.0f}'.format(MOVE, x, target.y, thrust))
        return True
        
    def throw(self, target, power):
        if self.has_acted:
            debug('Wizard {} has acted, cannot throw to {}'.format(self._id, target))
            return False
        self.has_acted = True
        self.action = THROW
        x = target.x if my_team_id == 0 else X_LIMIT-target.x
        self.set_action_str('{} {:.0f} {:.0f} {:.0f}'.format(THROW, x, target.y, power))
        return True
    
    def flipendo(self, target):
        if self.has_acted:
            debug('Wizard {} has acted, cannot flipendo {}'.format(self._id, target))
            return False
        self.has_acted = True
        self.action = FLIPENDO
        self.set_action_str('{} {}'.format(FLIPENDO, target._id))
        return True
    
    def obliviate(self, target):
        if self.has_acted:
            debug('Wizard {} has acted, cannot obliviate {}'.format(self._id, target))
            return False
        self.has_acted = True
        self.action = OBLIVIATE
        self.set_action_str('{} {}'.format(OBLIVIATE, target._id))
        return True
    
    def accio(self, target):
        if self.has_acted:
            debug('Wizard {} has acted, cannot accio {}'.format(self._id, target))
            return False
        self.has_acted = True
        self.action = ACCIO
        self.set_action_str('{} {}'.format(ACCIO, target._id))
        return True
    
    def petrificus(self, target):
        if self.has_acted:
            debug('Wizard {} has acted, cannot petrificus {}'.format(self._id, target))
            return False
        self.has_acted = True
        self.action = PETRIFICUS
        self.set_action_str('{} {}'.format(PETRIFICUS, target._id))
        return True
            

class Snaffle(Entity):
    def __init__(self, _id, posx, posy, vx, vy):
        super().__init__(_id, posx, posy, vx, vy)
        self.targetted = False
        self.mass = 0.5
        self.def_thrust = 0
        self.deaccel = 0.75
        self.radius = 150
        self.wizards_list = None
        self.last_turn = 0
        self.danger = False
        self._grabbed = []
        self._enemy_grabbed = []
        self._petrified = []
    
    @property
    def grabbed(self):
        if len(self._grabbed) == 0:
            return None
        return self._grabbed[0]
    
    @grabbed.setter
    def grabbed(self, val):
        self._grabbed[:] = self._grabbed[:3]
        self._grabbed.insert(0, val)
        
    @property
    def enemy_grabbed(self):
        if len(self._enemy_grabbed) == 0:
            return None
        return self._enemy_grabbed[0]
    
    @enemy_grabbed.setter
    def enemy_grabbed(self, val):
        self._enemy_grabbed[:] = self._enemy_grabbed[:3]
        self._enemy_grabbed.insert(0, val)
        
    @property
    def petrified(self):
        if len(self._petrified) == 0:
            return None
        return self._petrified[0]
    
    @petrified.setter
    def petrified(self, val):
        self._petrified[:] = self._petrified[:3]
        self._petrified.insert(0, val)
    
    def sort_wizards(self, wizards):
        self.wizards_list = sorted(wizards[:], key=lambda x: x.pos.sub(self.pos).norm())
        
class Bludger(Entity):
    def __init__(self, _id, posx, posy, vx, vy):
        super().__init__(_id, posx, posy, vx, vy)
        self.mass = 8
        self.def_thrust = 1000
        self.deaccel = 0.9
        self.radius = 200
        self.danger = None

# def copy_entity_list(entities):
#     result = {}
#     for entity in entities:
#         result[entity._id] = entity
#     return result

# game loop
my_wizards = {}
opp_wizards = {}
snaffles = {}
bludgers = {}
mana = 0
turn = 0
can_pester = 0
can_obliviate = 0
my_score = 0
max_score = 100

def sort_wizard(wizard):
    if len(snaffles) == 1:
        the_snaffle = list(snaffles.values())[0]
        return dist(wizard.pos, the_snaffle.pos)
    return wizard._id
    
while True:
    entities = int(input())  # number of entities still in game
    # prev_my_wizards = copy_entity_list(my_wizards)
    # prev_opp_wizards = copy_entity_list(opp_wizards)
    # my_wizards = []
    # opp_wizards = []
    # snaffles = []
    # bludgers = []
    for i in range(entities):
        # entity_id: entity identifier
        # entity_type: "WIZARD", "OPPONENT_WIZARD" or "SNAFFLE" (or "BLUDGER" after first league)
        # x: position
        # y: position
        # vx: velocity
        # vy: velocity
        # state: 1 if the wizard is holding a Snaffle, 0 otherwise
        entity_id, entity_type, x, y, vx, vy, state = input().split()
        entity_id = int(entity_id)
        x = int(x)
        y = int(y)
        vx = int(vx)
        vy = int(vy)
        state = int(state)
        if entity_type == 'WIZARD':
            if turn == 0:
                my_wizard = Wizard(entity_id, x, y, vx, vy, state)
                if len(my_wizards) > 0:
                    my_wizards[entity_id-1].other_wizard = my_wizard
                    my_wizard.other_wizard = my_wizards[entity_id-1]
                my_wizards[entity_id] = my_wizard
            else:
                my_wizards[entity_id].pos = Point(x, y)
                my_wizards[entity_id].v = Point(vx, vy)
                my_wizards[entity_id].state = state
                my_wizards[entity_id].has_acted = False
        elif entity_type == 'OPPONENT_WIZARD':
            if turn == 0:
                opp_wizards[entity_id] = Wizard(entity_id, x, y, vx, vy, state)
            else:
                opp_wizards[entity_id].pos = Point(x, y)
                opp_wizards[entity_id].v = Point(vx, vy)
                opp_wizards[entity_id].state = state
                opp_wizards[entity_id].has_acted = False
        elif entity_type == 'SNAFFLE':
            if turn == 0:
                snaffles[entity_id] = Snaffle(entity_id, x, y, vx, vy)
            else:
                snaffles[entity_id].pos = Point(x, y)
                snaffles[entity_id].v = Point(vx, vy)
                snaffles[entity_id].state = state
                snaffles[entity_id].last_turn = turn
        elif entity_type == 'BLUDGER':
            if turn == 0:
                bludgers[entity_id] = Bludger(entity_id, x, y, vx, vy)
            else:
                bludgers[entity_id].pos = Point(x, y)
                bludgers[entity_id].v = Point(vx, vy)
                bludgers[entity_id].state = state
        else:
            debug('Unknown entity type: {}'.format(entity_type))

    # Keep track of scores
    if turn == 0:
        max_score = (len(snaffles)//2) + 1
    for snaffle_id in list(snaffles.keys()):
        if snaffles[snaffle_id].last_turn != turn:
            if snaffles[snaffle_id].pos.x > 8000:
                my_score += 1
            del snaffles[snaffle_id]
    
    entities = []
    for my_wizard in my_wizards.values():
        entities.append(my_wizard)
    for opp_wizard in opp_wizards.values():
        entities.append(opp_wizard)
    for snaffle in snaffles.values():
        entities.append(snaffle)
    for bludger in bludgers.values():
        entities.append(bludger)

    # LOTS OF IF ELSE HERE
    # with an action called for each wizard once

    # Execute the actions
    for my_wizard in sorted(my_wizards.values(), key=lambda x:x._id):
        my_wizard.execute()

    # Keep track of mana
    mana += 1
    if mana > 100:
        mana = 100
    # Keep track of turn
    turn += 1
    debug('Magic: {}'.format(mana))
    debug('Score: {}'.format(my_score))
            
