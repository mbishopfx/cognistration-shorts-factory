#!/usr/bin/env python3
"""Update batch queue items — mark them done, set output file and Drive ID."""

import argparse, json, os, sys
from datetime import datetime, timezone

STATE_PATH = os.path.join(os.path.dirname(__file__), '..', 'state', 'batch_queue.json')


def update(batch_id: str, status: str, output_file: str = None,
           drive_file_id: str = None):
    if not os.path.exists(STATE_PATH):
        print(f"ERROR: State file not found at {STATE_PATH}")
        sys.exit(1)

    with open(STATE_PATH) as f:
        state = json.load(f)

    found = False
    for batch in state.get('batches', []):
        if batch['id'] == batch_id:
            batch['status'] = status
            if output_file:
                batch['outputFile'] = output_file
            if drive_file_id:
                batch['driveFileId'] = drive_file_id
            batch['updatedAt'] = datetime.now(timezone.utc).isoformat()
            found = True
            break

    if not found:
        print(f"ERROR: Batch ID '{batch_id}' not found in queue")
        sys.exit(1)

    with open(STATE_PATH, 'w') as f:
        json.dump(state, f, indent=2)

    print(f"Updated {batch_id} → status={status}" +
          (f" file={output_file}" if output_file else "") +
          (f" driveId={drive_file_id}" if drive_file_id else ""))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Update batch queue item')
    parser.add_argument('--id', required=True, dest='batch_id',
                        help='Batch ID to update')
    parser.add_argument('--status', required=True,
                        choices=['pending', 'rendering', 'uploading', 'done', 'failed'],
                        help='New status')
    parser.add_argument('--file', dest='output_file',
                        help='Output file path (relative to repo root)')
    parser.add_argument('--drive-id', dest='drive_file_id',
                        help='Google Drive file ID')
    args = parser.parse_args()

    update(args.batch_id, args.status, args.output_file, args.drive_file_id)