# The MIT License (MIT)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`adafruit_led_animation.timedsequence`
================================================================================

Animation timed sequence helper for CircuitPython helper library for LED animations.


* Author(s): Mark Komus

Implementation Notes
--------------------

**Hardware:**

* `Adafruit NeoPixels <https://www.adafruit.com/category/168>`_
* `Adafruit DotStars <https://www.adafruit.com/category/885>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads

"""

from adafruit_led_animation.sequence import AnimationSequence
MS_PER_SECOND = const(1000)
#from . import MS_PER_SECOND, monotonic_ms


class TimedAnimationSequence(AnimationSequence):
    """
    A sequence of Animations to run in succession, each animation running for an
    individual amount of time.
    :param members: The animation objects or groups followed by how long the animation
                    should run in seconds.
    :param bool auto_clear: Clear the pixels between animations. If ``True``, the current animation
                            will be cleared from the pixels before the next one starts.
                            Defaults to ``False``.
    :param bool random_order: Activate the animations in a random order. Defaults to ``False``.
    :param bool auto_reset: Automatically call reset() on animations when changing animations.
    .. code-block:: python
        import board
        import neopixel
        from adafruit_led_animation.timedsequence import TimedAnimationSequence
        import adafruit_led_animation.animation.comet as comet_animation
        import adafruit_led_animation.animation.sparkle as sparkle_animation
        import adafruit_led_animation.animation.blink as blink_animation
        import adafruit_led_animation.color as color
        strip_pixels = neopixel.NeoPixel(board.A1, 30, brightness=1, auto_write=False)
        blink = blink_animation.Blink(strip_pixels, 0.2, color.RED)
        comet = comet_animation.Comet(strip_pixels, 0.1, color.BLUE)
        sparkle = sparkle_animation.Sparkle(strip_pixels, 0.05, color.GREEN)
        animations = AnimationSequence(blink, 5, comet, 3, sparkle, 7)
        while True:
            animations.animate()
    """

    # pylint: disable=too-many-instance-attributes
    def __init__(
        self, *members, auto_clear=True, random_order=False, auto_reset=False, name=None
    ):
        self._animation_members = []
        self._animation_timings = []
        #for x in range(len(members)):
        for x, item in enumerate(members):
            if not x % 2:
                self._animation_members.append(members[x])
            else:
                self._animation_timings.append(members[x])

        super().__init__(
            *self._animation_members,
            auto_clear=auto_clear,
            random_order=random_order,
            auto_reset=auto_reset,
            advance_on_cycle_complete=False,
            name=name
        )
        self._advance_interval = self._animation_timings[self._current] * MS_PER_SECOND

    def activate(self, index):
        super().activate(index)
        self._advance_interval = self._animation_timings[self._current] * MS_PER_SECOND