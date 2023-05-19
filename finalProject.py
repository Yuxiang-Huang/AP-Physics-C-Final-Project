import vpython

# Set scene
vpython.scene.background = vpython.color.white
vpython.scene.width = 1000
vpython.scene.height = 650
vpython.scene.range = 1

#constants (don't ask me when k is so low, I will change it later!!!)
K = 9E-7

# store all spawned charges
allChargedObjs = []

# Class Charge
class ChargedObj:
    def __init__(self, mass, charge, spawnPos, spawnVel):
        # variables
        self.charge = charge
        self.mass = mass
        self.pos = spawnPos
        self.vel = spawnVel
        # spheres for now
        if (charge < 0):
            self.display = vpython.sphere(pos=spawnPos, radius=0.05, color = vpython.color.red)
        if (charge > 0):
            self.display = vpython.sphere(pos=spawnPos, radius=0.05, color = vpython.color.blue)
        if (charge == 0):
            self.display = vpython.sphere(pos=spawnPos, radius=0.05, color = vpython.color.black)
    
    def applyForce(self):
        # calculate force from  every other charge
        force = vpython.vector(0, 0, 0)
        for chargedObj in allChargedObjs:
            if (chargedObj != self):
                if (vpython.mag(self.pos - chargedObj.pos) > 2 * self.display.radius):
                    force += calculateForce(self, chargedObj)
        # apply force
        self.vel += force / self.mass

    def applyVel(self):
        self.pos += self.vel
        self.display.pos = self.pos
    
    def checkCollision(self):
        for chargedObj in allChargedObjs:
            if (vpython.mag(self.pos - chargedObj.pos) <= 2 * self.display.radius):
                self.vel = vpython.vector(0, 0, 0)
                chargedObj.vel = vpython.vector(0, 0, 0)

# Coulomb's Law
def calculateForce(q1, q2):
    r12 = q1.pos - q2.pos
    return vpython.norm(r12) * K * q1.charge * q2.charge / (vpython.mag(r12)**2)

# Click make a charge
def makeCharge():
    allChargedObjs.append(ChargedObj(1, spawnCharge, vpython.scene.mouse.project(normal=vpython.vector(0, 0, 1)), vpython.vector(0, 0, 0)))

vpython.scene.bind('click', makeCharge)

# choose charge
spawnCharge = -1

def spawnChargeShift():
    global spawnCharge, spawnChargeText
    spawnCharge = s.value
    spawnChargeText.text = 'Charge:'+'{:1.2f}'.format(s.value)

s = vpython.slider(bind = spawnChargeShift, min = -5, max = 5, value = -1)
spawnChargeText = vpython.wtext(text = 'Charge:'+'{:1.2f}'.format(s.value))

# running
playing = False

def play():
    playing = not playing

def changePlayButton():
    global playing, playButton
    playing = not playing
    if playing:
        playButton.text = 'Stop'
    else:
        playButton.text = 'Play'

vpython.scene.append_to_caption("   ")
playButton = vpython.button(text="Play", bind=changePlayButton)

while True:
    vpython.rate(1000)
    if (playing):
        for chargedObj in allChargedObjs:
            chargedObj.applyForce()
        for chargedObj in allChargedObjs:
            chargedObj.applyVel()
    # for charge in allChargedObjs:
    #     charge.checkCollision()
        
