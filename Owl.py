from manim import *
import numpy.linalg as LA
import numpy as np

draw_color = WHITE


class Owl:

    def __init__(self):
        self.skull_height = 1
        self.skull_width = 1.2

        self.skull_rotation = ValueTracker(0)

        self.eye_radius = 0.7
        self.pupile_fraction = 0.4
        self.pupil_radius = self.eye_radius * self.pupile_fraction

        self.pupil_pos_x = ValueTracker(0)
        self.pupil_pos_y = ValueTracker(0)

        self.ear_size = 0.65
        self.left_ear_rotation = ValueTracker(0.4)
        self.right_ear_rotation = ValueTracker(0.5)

        self.body_height = 4
        self.body_width = 3
        self.body_displacement = 1.25

        self.wing_displacement_x = 1.
        self.wing_displacement_y = 2
        self.wing_width = 1.1
        self.wing_height = 3

        self.gap_scale = 1.1

        self.default_arm_angle = 0.2

        self.right_wing_rotation = ValueTracker(self.default_arm_angle)
        self.left_wing_rotation = ValueTracker(-self.default_arm_angle)

    def draw(self):

        head = self.create_head()

        body = self.create_body()
        wings = VGroup(*self.create_wings())

        self.all = VGroup(head, body, wings)
        return self.all

    def move_eyes(self, x, y):
        return self.pupil_pos_x.animate.set_value(x), self.pupil_pos_y.animate.set_value(y)

    def update_pupil(self, pupil, eye):
        pupil.set_fill(draw_color, opacity=0.8)
        pupil.set_stroke(draw_color, opacity=0.)
        dist = (self.eye_radius - self.pupil_radius) * 0.5
        pupil.set_y(dist * self.pupil_pos_y.get_value() + eye.get_y())
        pupil.set_x(dist * self.pupil_pos_x.get_value() + eye.get_x())

    def create_eye(self):
        eye = Circle(radius=self.eye_radius)
        eye.set_stroke(draw_color, opacity=0.8)

        pupil = Circle(radius=self.pupil_radius)
        pupil.set_fill(draw_color, opacity=0.8)
        pupil.set_stroke(draw_color, opacity=0.)

        dist = (self.eye_radius - self.pupil_radius) * 0.99
        pupil.set_y(dist * self.pupil_pos_y.get_value() + eye.get_y())
        pupil.set_x(dist * self.pupil_pos_x.get_value() + eye.get_x())
        return VGroup(eye, pupil)

    def create_eyes(self):
        left_eye = self.create_eye().shift(LEFT * self.skull_width / 1.65)
        right_eye = self.create_eye().shift(RIGHT * self.skull_width / 1.65)
        return VGroup(left_eye, right_eye)

    def create_ear(self, ear_size):
        ear_c = Circle(radius=ear_size)
        ear_r = Square(ear_size * 2).shift(RIGHT * ear_size)
        return Difference(ear_c, ear_r)

    def create_skull_half(self, ear_rotation):
        circle = Circle(radius=self.skull_height)  # create a circle
        ear = self.create_ear(self.ear_size) \
            .shift(UP * self.skull_height) \
            .shift(LEFT * self.skull_height * 0.3)
        ear.rotate(ear_rotation.get_value(), about_point=ear.get_right())

        # ear.add_updater(lambda ear: ear.rotate(ear_rotation.get_value()))
        skull_half = Union(circle, ear)
        return skull_half

    def create_skull(self):
        skull_left_half = self.create_skull_half(self.left_ear_rotation).shift(LEFT * self.skull_width / 2.)
        skull_right_half = self.create_skull_half(self.right_ear_rotation).flip(Y_AXIS).reverse_direction().shift(
            RIGHT * self.skull_width / 2.)

        return Union(skull_right_half, skull_left_half)

    def create_head(self):
        skull = self.create_skull()
        eyes = self.create_eyes()
        return VGroup(skull, eyes).rotate(self.skull_rotation.get_value(), about_point=LEFT*0.5)

    def create_body(self):
        skull = self.create_head().split()[0]
        body = Ellipse(width=self.body_width, height=self.body_height)
        body.shift(DOWN * self.body_displacement)

        wings = self.create_wings()
        for wing in wings:
            body = Difference(body, wing.scale(self.gap_scale + 0.1))

        body = Difference(body, skull.stretch(self.gap_scale, 1))
        return body

    def create_wings(self):
        left_wing = self.create_wing() \
            .shift(LEFT * self.wing_displacement_x) \
            .shift(DOWN * self.wing_displacement_y) \
            .rotate(self.left_wing_rotation.get_value(),
                    about_point=ORIGIN + [-self.wing_displacement_x, -self.wing_displacement_y + self.wing_height / 2.,
                                          0])
        right_wing = self.create_wing() \
            .shift(RIGHT * self.wing_displacement_x) \
            .shift(DOWN * self.wing_displacement_y) \
            .rotate(self.right_wing_rotation.get_value(),
                    about_point=ORIGIN + [self.wing_displacement_x, -self.wing_displacement_y + self.wing_height / 2.,
                                          0])

        skull = self.create_head().split()[0].stretch(self.gap_scale, 1)
        left_wing = Difference(left_wing, skull)
        right_wing = Difference(right_wing, skull)
        return left_wing, right_wing

    def create_wing(self):
        wing = Ellipse(self.wing_width, self.wing_height)
        return wing

    def point_to(self, point):
        multi = 1
        arm = self.right_wing_rotation
        other = self.left_wing_rotation
        if point[0] < self.all.get_x():
            arm = self.left_wing_rotation
            other = self.right_wing_rotation
            multi = -1
        a = self.all.get_center() - point
        b = Y_AXIS
        inner = np.inner(a, b)
        norms = LA.norm(a) * LA.norm(b)

        cos = inner / norms
        rad = np.arccos(np.clip(cos, -1.0, 1.0))
        return arm.animate.set_value(rad * multi), other.animate.set_value(-multi * 0.2), *self.move_eyes(
            multi * np.sin(rad), -np.cos(rad))

    def reset(self):
        return self.right_wing_rotation.animate.set_value(self.default_arm_angle), \
               self.left_wing_rotation.animate.set_value(-self.default_arm_angle), \
               *self.move_eyes(0, 0), \
               self.skull_rotation.animate.set_value(0)

    def wave(self, scene):
        scene.play(self.right_wing_rotation.animate(run_time=.8, rate_func=rate_functions.smooth).set_value(2.4),
                   self.skull_rotation.animate(run_time=.8, rate_func=rate_functions.smooth).set_value(0.3))
        scene.play(self.right_wing_rotation.animate(run_time=0.4, rate_func=rate_functions.smooth).set_value(3.))
        scene.play(self.right_wing_rotation.animate(run_time=0.4, rate_func=rate_functions.smooth).set_value(2.))
        scene.play(self.right_wing_rotation.animate(run_time=0.4, rate_func=rate_functions.smooth).set_value(3.))
        scene.play(self.right_wing_rotation.animate(run_time=0.4, rate_func=rate_functions.smooth).set_value(2.))

        scene.play(*self.reset())

    def ear_wink(self):
        return self.right_ear_rotation.animate(run_time=0.5, rate_func=rate_functions.there_and_back).set_value(1)

