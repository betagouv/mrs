import os


def settings(request):  # pragma: no cover
    return dict(
        settings=dict(
            INSTANCE=os.getenv('INSTANCE'),
        )
    )
