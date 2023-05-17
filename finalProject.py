import vpython

# Set scene
vpython.scene.background = vpython.color.white
vpython.scene.width = 1000
vpython.scene.height = 650
vpython.scene.range = 1

#constants (don't ask me when k is so low, I will change it later!!!)
K = 9E-9

# store all spawned charges
allCharges = []

# Class Charge
class ChargedObj:
    def __init__(self, mass, charge, spawnPos, spawnVel):
        # variables
        self.charge = charge
        self.mass = mass
        self.pos = spawnPos
        self.vel = spawnVel
        self.acc = vpython.vector(0, 0, 0)
        # spheres for now
        if (charge == -1):
            self.display = vpython.sphere(pos=spawnPos, radius=0.05, color = vpython.color.black)
        if (charge == 1):
            self.display = vpython.sphere(pos=spawnPos, radius=0.05, color = vpython.color.blue)
    
    def update(self):
        # calculate force from  every other charge
        force = vpython.vector(0, 0, 0)
        for charge in allCharges:
            if (charge != self and vpython.mag(self.pos - charge.pos) > 2 * self.display.radius):
                force += calculateForce(self, charge)
        # apply force
        self.acc += force / self.mass
        self.vel += self.acc
        self.pos += self.vel
        self.display.pos = self.pos

# Coulomb's Law
def calculateForce(q1, q2):
    r12 = q2.pos - q1.pos
    return -vpython.norm(r12) * K * q1.charge * q2.charge / (vpython.mag(r12)**2)

# Click make a charge
def makeCharge():
    allCharges.append(ChargedObj(1, spawnCharge, vpython.scene.mouse.project(normal=vpython.vector(0,0, 1)), vpython.vector(0, 0, 0)))

vpython.scene.bind('click', makeCharge)

# choose charge
spawnCharge = -1

def ChangeChargeButton():
    global spawnCharge, wt
    spawnCharge = -1 * spawnCharge
    if spawnCharge == -1:
        wt.text = 'Current Charge: negative'
    else:
        wt.text = 'Current Charge: positve'

wt = vpython.wtext(text='Current Charge: negative')

vpython.button(text="Change Charge", bind=ChangeChargeButton)

while True:
    vpython.rate(200)
    for charge in allCharges:
        charge.update()