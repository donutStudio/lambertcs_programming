"""Host-only submission review/export, deliberately unavailable to students."""
import csv
import click
from .store import database, expire


def register_commands(app):
    @app.cli.command("export-submissions")
    @click.option("--output", type=click.Path(), default="submissions/export.csv")
    def export_submissions(output):
        with database() as db:
            expire(db)
            rows = db.execute("SELECT a.*, d.ip, d.user_agent FROM attempts a JOIN devices d ON d.id=a.owner WHERE submitted IS NOT NULL ORDER BY started").fetchall()
        with open(output, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            keys = ("id", "owner", "assessment", "started", "deadline", "submitted", "updated", "reason", "answers", "score", "ip", "user_agent")
            writer.writerow(keys)
            for row in rows:
                # Quoting CSV alone does not prevent spreadsheet formula injection.
                writer.writerow([("'" + row[key]) if isinstance(row[key], str) and row[key].startswith(("=", "+", "-", "@", "\t", "\r", "\n")) else row[key] for key in keys])
        click.echo(f"Exported {len(rows)} submissions to {output}")

    @app.cli.command("list-submissions")
    def list_submissions():
        with database() as db:
            expire(db)
            rows = db.execute("SELECT * FROM attempts ORDER BY started DESC").fetchall()
        for row in rows:
            click.echo(f'{row["id"]}  {row["assessment"]}  {row["reason"] or "in progress"}  device={row["owner"]}')

    @app.cli.command("show-submission")
    @click.argument("attempt_id")
    def show_submission(attempt_id):
        import json
        from .store import unpack
        with database() as db:
            expire(db)
            row = db.execute("SELECT * FROM attempts WHERE id=?", (attempt_id,)).fetchone()
        if row is None:
            raise click.ClickException("Attempt not found")
        click.echo(json.dumps(unpack(row), indent=2))
