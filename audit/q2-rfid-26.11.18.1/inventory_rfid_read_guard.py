"""Q2-only, audited-reader response guard. No transport or persistence replacement.

Reject empty/malformed successful reads; conflicting nonempty payloads quarantine
that scan until the stock deadline. The stock reader still requires its matching
pair, owns the timer and saves accepted results. No synthesized tag responses.
"""
import hashlib
import logging
import re
from itertools import count
from uuid import uuid4
from pathlib import Path

READER_SHA = '6a196c69b79a70fe97eabfaeec84be9fbbd061a6bb7618fe773853f9a890fe78'


class Scan:
    def __init__(self):
        self.candidate = None
        self.conflict = False
        self.empty = 0
        self.malformed = 0
        self.failed = 0
        self.valid = 0

    def filter(self, response):
        if not isinstance(response, dict):
            self.malformed += 1
            return {'status': 0, 'data': bytes(16)}
        if type(response.get('status')) is not int or response['status'] != 1:
            self.failed += 1
            return dict(response, status=0)
        data = response.get('data')
        if (not isinstance(data, (bytes, bytearray, list, tuple)) or len(data) != 16
                or any(type(v) is not int or not 0 <= v <= 255 for v in data)):
            self.malformed += 1
            return dict(response, status=0)
        payload = bytes(data)
        if not any(payload):
            self.empty += 1
            return dict(response, status=0)
        self.valid += 1
        if self.candidate is None:
            self.candidate = payload
        elif payload != self.candidate:
            self.conflict = True
        if self.conflict:
            return dict(response, status=0)
        return response

    def summary(self):
        return {'empty': self.empty, 'malformed': self.malformed,
                'failed': self.failed, 'valid': self.valid, 'conflict': self.conflict}


def install_guard(cls, report):
    if getattr(cls.start_rfid_read, '_inventory_read_guard', False):
        raise RuntimeError('RFID read guard already installed')
    original_start = cls.start_rfid_read
    original_schedule = cls._schedule_rfid_read
    epoch = uuid4().hex
    sequence = count(1)

    def start(reader, *args, **kwargs):
        scan = Scan()
        scan.scan_id = f"{epoch}:{next(sequence)}"
        scan.accepted_id = None
        reader._inventory_read_guard_scan = scan
        return original_start(reader, *args, **kwargs)

    def filter_response(reader, response):
        scan = getattr(reader, '_inventory_read_guard_scan', None)
        if scan is None:
            # Calls outside an active stock scan retain their original behavior.
            return response
        previous_conflict = scan.conflict
        result = scan.filter(response)
        if scan.conflict and not previous_conflict:
            logging.warning('RFID read guard: conflicting payloads slot=%s; scan quarantined until stock deadline',
                            getattr(getattr(reader, 'stepper', None), 'stepper_name', '?'))
        return result

    def schedule(reader, eventtime):
        # Intercept only this poll's instance call. Leaving the class read hook
        # untouched lets the existing adapter disconnect/reload cleanly.
        original_read = reader.read_card_from_slot
        had_instance_read = 'read_card_from_slot' in reader.__dict__
        old_instance_read = reader.__dict__.get('read_card_from_slot')
        reader.read_card_from_slot = lambda: filter_response(reader, original_read())
        scan = getattr(reader, '_inventory_read_guard_scan', None)
        gcode = getattr(reader, 'gcode', None)
        respond = getattr(gcode, 'respond_info', None)
        hooked = scan is not None and respond is not None and hasattr(gcode, '__dict__')
        if hooked:
            had_response = 'respond_info' in vars(gcode)
            old_response = vars(gcode).get('respond_info')

            def observe(message, *args, **kwargs):
                result = respond(message, *args, **kwargs)
                match = re.fullmatch(
                    r"rfid_respond:filament_id=(QF[A-Z][0-9]{2}) version=\d+ color_array=\[.*\] slot=(slot\d+)",
                    message) if isinstance(message, str) else None
                if match and match[2] == getattr(reader.stepper, 'stepper_name', None):
                    scan.accepted_id = match[1]
                return result

            gcode.respond_info = observe
        try:
            result = original_schedule(reader, eventtime)
        finally:
            if hooked:
                if had_response:
                    gcode.respond_info = old_response
                else:
                    del gcode.respond_info
            if had_instance_read:
                reader.read_card_from_slot = old_instance_read
            else:
                del reader.read_card_from_slot
        scan = getattr(reader, '_inventory_read_guard_scan', None)
        if scan is not None and result == reader.printer.get_reactor().NEVER:
            expired = eventtime - reader.rfid_read_start_time > reader.max_read_time
            outcome = ('conflicting-tags' if scan.conflict else
                       'timeout-after-empty' if expired and scan.empty else
                       'timeout-after-malformed' if expired and scan.malformed else
                       'timeout' if expired else 'stock-reader-completed')
            report(getattr(getattr(reader, 'stepper', None), 'stepper_name', '?'), outcome, dict(scan.summary(), scan_id=scan.scan_id, accepted_id=scan.accepted_id))
            reader._inventory_read_guard_scan = None
        return result

    start._inventory_read_guard = True
    cls.start_rfid_read, cls._schedule_rfid_read = start, schedule

    def restore():
        for name, wrapped, original in [('start_rfid_read', start, original_start),
                                        ('_schedule_rfid_read', schedule, original_schedule)]:
            if getattr(cls, name) is wrapped:
                setattr(cls, name, original)
    return restore


class InventoryRFIDReadGuard:
    def __init__(self, config):
        from . import box_rfid
        if hashlib.sha256(Path(box_rfid.__file__).read_bytes()).hexdigest() != READER_SHA:
            raise config.error('RFID read guard: reader changed; remove [inventory_rfid_read_guard] and audit compatibility')
        self.results = {}
        restore = install_guard(box_rfid.BoxRFID, self.report)
        config.get_printer().register_event_handler('klippy:disconnect', restore)
        logging.info('RFID read guard enabled: reject empty/malformed success; quarantine conflicts; stock timing and persistence')

    def report(self, slot, outcome, summary):
        self.results[slot] = dict(summary, outcome=outcome)
        logging.info('RFID read guard complete slot=%s outcome=%s counts=%s', slot, outcome, summary)

    def get_status(self, eventtime):
        return {'version': 'q2-read-guard-v2', 'last_scans': {k: dict(v) for k, v in self.results.items()}}


def load_config(config):
    return InventoryRFIDReadGuard(config)
