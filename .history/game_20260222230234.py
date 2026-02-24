# solar_game.py
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import (
    AmbientLight, DirectionalLight, Vec3, Vec4,
    TextNode, WindowProperties
)
from direct.gui.OnscreenText import OnscreenText
import math


class SolarGame(ShowBase):
    def __init__(self):
        super().__init__()

        # Window title
        props = WindowProperties()
        props.setTitle("3D Solar System (Panda3D) - Simple Game Demo")
        self.win.requestProperties(props)

        # Mouse + camera setup
        self.disableMouse()  # we will control the camera ourselves
        self.camera.setPos(0, -80, 20)
        self.camera.lookAt(0, 0, 0)

        # Simple instructions
        self.ui = OnscreenText(
            text="W/S: forward/back | A/D: strafe | Q/E: up/down | Arrow keys: look | Esc: quit",
            pos=(-1.32, 0.93),
            align=TextNode.ALeft,
            scale=0.05,
            fg=(1, 1, 1, 1),
            shadow=(0, 0, 0, 1),
        )

        # Lighting
        ambient = AmbientLight("ambient")
        ambient.setColor(Vec4(0.20, 0.20, 0.25, 1))
        self.render.setLight(self.render.attachNewNode(ambient))

        sun_light = DirectionalLight("sun_light")
        sun_light.setColor(Vec4(1, 1, 0.95, 1))
        sun_light_np = self.render.attachNewNode(sun_light)
        sun_light_np.setHpr(20, -30, 0)
        self.render.setLight(sun_light_np)

        # Background
        self.setBackgroundColor(0.02, 0.02, 0.05, 1)

        # Key controls
        self.keys = {
            "w": False, "s": False, "a": False, "d": False,
            "q": False, "e": False,
            "left": False, "right": False, "up": False, "down": False
        }
        for k in ["w","s","a","d","q","e","arrow_left","arrow_right","arrow_up","arrow_down"]:
            self.accept(k, self._set_key, [k, True])
            self.accept(f"{k}-up", self._set_key, [k, False])
        self.accept("escape", self.userExit)

        # Map arrow names to dict keys
        self.key_map = {
            "arrow_left": "left",
            "arrow_right": "right",
            "arrow_up": "up",
            "arrow_down": "down"
        }

        # Models (use Panda3D built-in sphere)
        self.loader.loadModel("models/environment").removeNode()  # warm up loader

        # Create Sun
        self.sun = self._make_sphere(scale=4.5, color=(1.0, 0.85, 0.2, 1))
        self.sun.reparentTo(self.render)
        self.sun.setPos(0, 0, 0)

        # A pivot Node for each planet to orbit around the sun
        self.planets = []
        self._add_planet(name="Mercury", radius=10, size=0.8, orbit_speed=1.6, color=(0.6, 0.6, 0.62, 1))
        self._add_planet(name="Venus",   radius=15, size=1.2, orbit_speed=1.2, color=(0.9, 0.8, 0.55, 1))
        self._add_planet(name="Earth",   radius=20, size=1.3, orbit_speed=1.0, color=(0.2, 0.5, 1.0, 1))
        self._add_planet(name="Mars",    radius=26, size=1.1, orbit_speed=0.8, color=(0.9, 0.35, 0.2, 1))
        self._add_planet(name="Jupiter", radius=36, size=2.5, orbit_speed=0.45, color=(0.9, 0.7, 0.55, 1))
        self._add_planet(name="Saturn",  radius=48, size=2.2, orbit_speed=0.32, color=(0.85, 0.8, 0.5, 1))

        # Camera motion settings
        self.move_speed = 35.0   # units per second
        self.look_speed = 75.0   # degrees per second
        self.cam_h = 0.0
        self.cam_p = -10.0

        # Task loop
        self.taskMgr.add(self.update, "update")

    def _set_key(self, key, value):
        mapped = self.key_map.get(key, key)
        self.keys[mapped] = value

    def _make_sphere(self, scale=1.0, color=(1, 1, 1, 1)):
        # Use a built-in sphere model. Panda ships with "models/misc/sphere".
        m = self.loader.loadModel("models/misc/sphere")
        m.setScale(scale)
        m.setColor(*color)
        m.setTwoSided(True)
        return m

    def _add_planet(self, name, radius, size, orbit_speed, color):
        pivot = self.render.attachNewNode(f"{name}_pivot")
        planet = self._make_sphere(scale=size, color=color)
        planet.reparentTo(pivot)
        planet.setPos(radius, 0, 0)

        self.planets.append({
            "name": name,
            "pivot": pivot,
            "planet": planet,
            "radius": radius,
            "size": size,
            "orbit_speed": orbit_speed,
            "angle": 0.0
        })

    def update(self, task):
        dt = globalClock.getDt()

        # Orbit planets
        for p in self.planets:
            p["angle"] += p["orbit_speed"] * dt * 60.0  # scale speed for visibility
            p["pivot"].setH(p["angle"])

            # planet self-rotation
            p["planet"].setH(p["planet"].getH() + (40.0 * dt))

        # Sun slow rotation
        self.sun.setH(self.sun.getH() + 10.0 * dt)

        # Camera look (arrow keys)
        if self.keys["left"]:
            self.cam_h += self.look_speed * dt
        if self.keys["right"]:
            self.cam_h -= self.look_speed * dt
        if self.keys["up"]:
            self.cam_p += self.look_speed * dt
        if self.keys["down"]:
            self.cam_p -= self.look_speed * dt

        # Clamp pitch
        self.cam_p = max(-89.0, min(89.0, self.cam_p))
        self.camera.setHpr(self.cam_h, self.cam_p, 0)

        # Camera movement (WASDQE)
        forward = 0.0
        strafe = 0.0
        updown = 0.0

        if self.keys["w"]:
            forward += 1.0
        if self.keys["s"]:
            forward -= 1.0
        if self.keys["d"]:
            strafe += 1.0
        if self.keys["a"]:
            strafe -= 1.0
        if self.keys["e"]:
            updown += 1.0
        if self.keys["q"]:
            updown -= 1.0

        if forward != 0 or strafe != 0 or updown != 0:
            # Move relative to camera orientation
            dir_forward = self.camera.getQuat(self.render).getForward()
            dir_right = self.camera.getQuat(self.render).getRight()
            dir_up = Vec3(0, 0, 1)

            move = (dir_forward * forward) + (dir_right * strafe) + (dir_up * updown)
            move.normalize()
            self.camera.setPos(self.camera.getPos() + move * self.move_speed * dt)

        return Task.cont


if __name__ == "__main__":
    app = SolarGame()
    app.run()