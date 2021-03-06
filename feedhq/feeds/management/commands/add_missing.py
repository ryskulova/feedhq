from django.conf import settings

from . import SentryCommand
from ...models import enqueue_favicon, Feed, UniqueFeed


class Command(SentryCommand):
    """Updates the users' feeds"""

    def handle_sentry(self, *args, **kwargs):
        missing = Feed.objects.raw(
            """
            select f.id, f.url
            from
                feeds_feed f
                left join auth_user u on f.user_id = u.id
            where
                not exists (
                    select 1 from feeds_uniquefeed u where f.url = u.url
                ) and
                u.is_suspended = false
            """)
        urls = set([f.url for f in missing])
        UniqueFeed.objects.bulk_create([
            UniqueFeed(url=url) for url in urls
        ])

        if not settings.TESTS:
            missing_favicons = UniqueFeed.objects.raw(
                """
                select id, url from feeds_uniquefeed u
                where
                    u.url != '' and
                    not exists (
                        select 1 from feeds_favicon f
                        where f.url = u.url
                    )
                """)
            for feed in missing_favicons:
                enqueue_favicon(feed.url)
