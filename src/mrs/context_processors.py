import os


def settings(request):
    return dict(
        settings=dict(
            INSTANCE=os.getenv('INSTANCE'),
        )
    )
