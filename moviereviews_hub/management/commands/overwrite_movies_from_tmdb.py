import os
import time
import requests

from django.core.management.base import BaseCommand
from moviereviews_hub.models import Movie

TMDB_BASE = "https://api.themoviedb.org/3"


class Command(BaseCommand):
    help = (
        "Overwrite all Movie fields from TMDB for movies that have TMDB_Api_ID. "
        "Keeps internal DB IDs, slugs, and reviews intact."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Only process N movies (0 = all).",
        )
        parser.add_argument(
            "--sleep",
            type=float,
            default=0.25,
            help="Seconds to sleep between TMDB requests.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print changes without saving.",
        )

    def handle(self, *args, **opts):
        tmdb_key = os.environ.get("TMDB_API_KEY")
        if not tmdb_key:
            self.stderr.write(self.style.ERROR("TMDB_API_KEY is not set."))
            return

        limit = opts["limit"]
        sleep_s = opts["sleep"]
        dry = opts["dry_run"]

        qs = Movie.objects.exclude(TMDB_Api_ID__isnull=True).order_by("id")
        if limit and limit > 0:
            qs = qs[:limit]

        processed = 0
        failed = 0

        for movie in qs:
            tmdb_id = int(movie.TMDB_Api_ID)

            try:
                details_res = requests.get(
                    f"{TMDB_BASE}/movie/{tmdb_id}",
                    params={"api_key": tmdb_key, "language": "en-US"},
                    timeout=20,
                )
                details_res.raise_for_status()
                details = details_res.json()

                credits_res = requests.get(
                    f"{TMDB_BASE}/movie/{tmdb_id}/credits",
                    params={"api_key": tmdb_key, "language": "en-US"},
                    timeout=20,
                )
                credits_res.raise_for_status()
                credits = credits_res.json()
            except Exception as e:
                failed += 1
                self.stderr.write(
                    self.style.WARNING(
                        f"FAILED Movie(id={movie.id}) TMDB={tmdb_id}: {e}"
                    )
                )
                continue

            # --- Parse TMDB fields ---
            title = details.get("title") or details.get("original_title") or movie.title

            directors = []
            for p in (credits.get("crew") or []):
                if p.get("job") == "Director" and p.get("name"):
                    directors.append(p["name"])
            directors = list(dict.fromkeys(directors))  # unique, stable order

            actors = [
                c.get("name")
                for c in (credits.get("cast") or [])[:10]
                if c.get("name")
            ]

            genres = [
                g.get("name")
                for g in (details.get("genres") or [])
                if g.get("name")
            ]

            release_date = details.get("release_date") or ""
            release_yr = (
                int(release_date[:4])
                if len(release_date) >= 4 and release_date[:4].isdigit()
                else None
            )

            runtime = details.get("runtime")

            poster_path = details.get("poster_path") or ""
            poster_url = (
                f"https://image.tmdb.org/t/p/w500{poster_path}"
                if poster_path
                else ""
            )

            updates = {
                "title": title,
                "director": directors,
                "actors": actors,
                "genres": genres,
                "release_yr": release_yr,
                "runtime": runtime,
                "poster_url": poster_url,
                "TMDB_Api_ID": tmdb_id,
            }

            if dry:
                self.stdout.write(
                    f"DRY-RUN Movie(id={movie.id}) updates={updates}"
                )
            else:
                for field, value in updates.items():
                    setattr(movie, field, value)
                movie.save(update_fields=list(updates.keys()))
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Updated Movie(id={movie.id}) '{movie.title}'"
                    )
                )

            processed += 1
            time.sleep(sleep_s)

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Processed={processed}, Failed={failed}"
            )
        )
