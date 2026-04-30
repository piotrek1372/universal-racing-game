import random
import logging
from pathlib import Path
from direct.showbase.ShowBase import ShowBase
from panda3d.core import CollisionTraverser, CollisionNode, CollisionRay, BitMask32, NodePath, CollisionHandlerQueue, CollisionHandlerEvent, CardMaker, WindowProperties
from direct.gui.OnscreenImage import OnscreenImage
from panda3d.core import TransparencyAttrib
from direct.task import Task
from direct.interval.IntervalGlobal import Sequence, Func, Wait, LerpColorScaleInterval
import sys
import json

class LocalizationManager:
    def __init__(self, lang_path: Path):
        self.lang_path = lang_path
        self.translations = {}
        self.load_translations()

    def load_translations(self):
        lang_files = self.lang_path.glob('*.json')
        for lang_file in lang_files:
            with lang_file.open('r', encoding='utf-8') as file:
                try:
                    data = json.load(file)
                    self.translations.update(data)
                except json.JSONDecodeError as e:
                    logging.error(f"Error decoding {lang_file}: {e}")

    def get_text(self, key: str) -> str:
        return self.translations.get(key, key)


class GameApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Set the game to Fullscreen by default
        window_properties = WindowProperties()
        window_properties.setFullscreen(True)
        self.win.requestProperties(window_properties)
        logging.basicConfig(level=logging.INFO)
        self.load_splash_screen()

    def load_splash_screen(self):
        # Load splash images
        BASE_DIR = Path(__file__).resolve().parent
        assets_dir = BASE_DIR / 'assets' / 'images'
        splash_files = [assets_dir / 'splash1.png', assets_dir / 'splash2.png', assets_dir / 'splash3.png']
        self.splash_index = 0
        self.splash_images = []

        for splash_file in splash_files:
            if splash_file.exists():
                image = OnscreenImage(image=str(splash_file), scale=1, pos=(0, 0, 0))
                image.setTransparency(TransparencyAttrib.MAlpha)
                image.reparentTo(self.aspect2d)
                image.hide()
                self.splash_images.append(image)
            else:
                logging.warning(f'Splash texture {splash_file.name} not found.')

        # Play the splash sequence
        if self.splash_images:
            self.play_splash_sequence()
        else:
            logging.warning('No splash images to display.')
            self.show_main_menu()

    def play_splash_sequence(self):
        # Sequence logic for splash screens
        splash_sequence = Sequence()

        for image in self.splash_images:
            fade_in = LerpColorScaleInterval(image, 1.0, (1, 1, 1, 1), startColorScale=(1, 1, 1, 0))
            fade_out = LerpColorScaleInterval(image, 1.0, (1, 1, 1, 0), startColorScale=(1, 1, 1, 1))

            splash_sequence.append(Func(image.show))
            splash_sequence.append(fade_in)
            splash_sequence.append(Wait(1.5))
            splash_sequence.append(fade_out)
            splash_sequence.append(Func(image.hide))

        splash_sequence.append(Func(self.show_main_menu))
        splash_sequence.start()

    def show_main_menu(self):
        BASE_DIR = Path(__file__).resolve().parent
        assets_dir = BASE_DIR / 'assets' / 'images'
        splash_files = ['splash1.png', 'splash2.png', 'splash3.png']
        selected_file = random.choice(splash_files)
        splash_path = assets_dir / selected_file

        if splash_path.exists():
            self.splash_image = OnscreenImage(image=str(splash_path), scale=1)
            self.splash_image.setTransparency(TransparencyAttrib.MAlpha)
            self.splash_image.reparentTo(self.aspect2d)
            logging.info(f'Splash screen displayed using {selected_file}')
            self.taskMgr.doMethodLater(3.0, self.cleanup_splash, 'remove_splash')
        else:
            logging.warning(f'Splash texture {selected_file} not found. Skipping splash screen.')
            self.initialize_main_scene()

    def cleanup_splash(self, task: Task) -> Task:
        if hasattr(self, 'splash_image'):
            self.splash_image.destroy()
        logging.info('Splash screen removed')
        self.initialize_main_scene()
        return Task.done

    def initialize_main_scene(self):
        # Initialize your main 3D scene here
        # Create main menu buttons as 3D cards
        self.create_main_menu_buttons()

    def create_main_menu_buttons(self):
        # Placeholder logic to set up 3D quads/cards as buttons
        self.button_settings = self.create_button((0, 50, 10), 'Settings', self.on_settings)
        self.button_exit = self.create_button((0, 50, -10), 'Exit', self.on_exit)

    def create_button(self, position, label, action):
        # Create a placeholder card model to act as a button
        card_maker = CardMaker(label)
        card_maker.setFrame(-1, 1, -0.2, 0.2)
        node = self.render.attachNewNode(card_maker.generate())
        node.setPos(*position)
        node.setColorScale(0.5, 0.5, 1, 1)
        node.setTransparency(TransparencyAttrib.MAlpha)
        node.setPythonTag("action", action)
        return node

    def on_settings(self):
        logging.info('Settings button pressed')
        # Placeholder for settings action

    def on_exit(self):
        logging.info('Exit button pressed')
        sys.exit(0)
        logging.info('Main scene initialized')

        # Set up collision detection for mouse raycasting
        self.cTrav = CollisionTraverser()

        self.pickerNode = CollisionNode('mouseRay')
        self.pickerNP = self.camera.attachNewNode(self.pickerNode)

        self.pickerRay = CollisionRay()
        self.pickerNode.addSolid(self.pickerRay)

        self.pickerQueue = CollisionHandlerQueue()
        self.cTrav.addCollider(self.pickerNP, self.pickerQueue)

        self.accept('mouse1', self.check_mouse_click)

    def check_mouse_click(self):
        if self.mouseWatcherNode.hasMouse():
            mpos = self.mouseWatcherNode.getMouse()
            self.pickerRay.setFromLens(self.camNode, mpos.getX(), mpos.getY())
            self.cTrav.traverse(self.render)

            if self.pickerQueue.getNumEntries() > 0:
                self.pickerQueue.sortEntries()
                pickedObj = self.pickerQueue.getEntry(0).getIntoNodePath()

                if pickedObj.hasPythonTag('action'):
                    action = pickedObj.getPythonTag('action')
                    action()  # Call the stored action on click
                else:
                    logging.info('No actionable object was clicked')

if __name__ == "__main__":
    app = GameApp()
    app.run()