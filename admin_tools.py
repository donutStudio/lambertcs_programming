"""Run host-only administration from the project directory.

  .venv\\Scripts\\python.exe admin_tools.py list
  .venv\\Scripts\\python.exe admin_tools.py show ATTEMPT_ID
  .venv\\Scripts\\python.exe admin_tools.py export --output submissions/export.csv
  .venv\\Scripts\\python.exe admin_tools.py reset-device DEVICE_ID --confirm

Find DEVICE_ID in `list` output. Reset deletes that device's attempts and its
network/browser quota matches, so cookie deletion does not leave a stale quota.
Use it only for an intentional administrator reset; there is no student endpoint.
Back up submissions/attempts.sqlite3 first if you need to retain those attempts.
The signing key/cookies stay intact; resetting takes effect on the next request.
"""
import argparse
from club import create_app
from club.store import database


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('list')
    show = sub.add_parser('show'); show.add_argument('attempt_id')
    export = sub.add_parser('export'); export.add_argument('--output', default='submissions/export.csv')
    reset = sub.add_parser('reset-device'); reset.add_argument('device_id'); reset.add_argument('--confirm', action='store_true')
    args = parser.parse_args()
    app = create_app()
    if args.command == 'reset-device':
        if not args.confirm: parser.error('Reset requires --confirm. This deletes attempts for the matching quota group.')
        with app.app_context(), database() as db:
            device = db.execute('SELECT fingerprint FROM devices WHERE id=?', (args.device_id,)).fetchone()
            if not device: parser.error('Device not found')
            count = db.execute('DELETE FROM attempts WHERE owner IN (SELECT id FROM devices WHERE fingerprint=?)', (device['fingerprint'],)).rowcount
        print(f'Reset {count} attempts. Device cookies are still usable.')
        return
    command = ['list-submissions'] if args.command == 'list' else ['show-submission', args.attempt_id] if args.command == 'show' else ['export-submissions', '--output', args.output]
    result = app.test_cli_runner().invoke(args=command)
    print(result.output, end='')
    if result.exception: raise result.exception


if __name__ == '__main__':
    main()
