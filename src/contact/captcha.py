import random
from django.conf import settings


def noise_arcs(draw, image):  # nosec
    size = image.size

    draw.arc([
        random.randint(15, 25) * -1,
        random.randint(35, 45) * -1,
        random.randint(int(size[0] * .9), int(size[0] * 1.1)),
        random.randint(35, 45)
    ], 0, 185, fill=settings.CAPTCHA_FOREGROUND_COLOR)

    draw.line(
        [
            random.randint(15, 25) * -1,
            random.randint(15, 25),
            size[0] + random.randint(15, 25),
            size[1] - random.randint(15, 25)
        ],
        fill=settings.CAPTCHA_FOREGROUND_COLOR
    )
    draw.arc(
        [
            random.randint(25, 35) * -1,
            size[1] * .45,
            size[0],
            size[1] * (random.randint(50, 60) / 100)
        ], 25, 335,
        fill=settings.CAPTCHA_FOREGROUND_COLOR
    )
    return draw


def noise_dots(draw, image):  # nosec
    size = image.size
    for p in range(int(size[0] * size[1] * 0.2)):
        draw.point(
            (
                random.randint(0, size[0]),
                random.randint(0, size[1])
            ),
            fill=settings.CAPTCHA_FOREGROUND_COLOR
        )
    return draw
