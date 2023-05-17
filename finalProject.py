import vpython

vpython.scene.background = vpython.color.white
vpython.scene.width = 1000
vpython.scene.height = 650
vpython.scene.range = 1

K = 0.005

allCharges = []

class Charge:
    def __init__(self, charge, spawnPos, spawnColor):
        self.charge = charge
        self.sphere = vpython.sphere(pos=spawnPos, radius=0.05, color = spawnColor)
    
    def update(self):
        force = vpython.vector(0, 0, 0)
        for charge in allCharges:
            if (charge != self and vpython.mag(self.sphere.pos - charge.sphere.pos) > 2 * self.sphere.radius):
                force += calculateForce(self, charge)
        self.sphere.pos += force

def calculateForce(q1, q2):
    r12 = q2.sphere.pos - q1.sphere.pos
    return -vpython.norm(r12) * K * q1.charge * q2.charge / (vpython.mag(r12)**2)

allCharges.append(Charge(1, vpython.vector(1, 0, 0), vpython.color.black))

def makeSphere():
    print(vpython.scene.mouse.project(normal=vpython.vec(0,0,1)));
    allCharges.append(Charge(spawnCharge, vpython.scene.mouse.project(normal=vpython.vec(0,0, 1)), vpython.color.blue))

vpython.scene.bind('click', makeSphere)


spawnCharge = -1

def Runbutton():
    global spawnCharge, wt
    spawnCharge = -1 * spawnCharge
    if spawnCharge == -1:
        wt.text = 'Current Charge: negative'
    else:
        wt.text = 'Current Charge: positve'

vpython.button(text="Change Charge", bind=Runbutton)

wt = vpython.wtext(text='Current Charge: negative')

while True:
    vpython.rate(200)
    for charge in allCharges:
        charge.update()