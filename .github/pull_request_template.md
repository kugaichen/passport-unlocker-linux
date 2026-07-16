## Summary

Describe the focused change and why it is needed.

## Safety impact

- Does this change protocol bytes, password handling, device validation, Polkit, SG_IO, or rescan behavior?
- Does it add any root-accessible operation or device write?
- Can passwords, hashes, serial numbers, payloads, or tokens enter argv, environment variables, logs, files, or exceptions?

## Validation

- [ ] Relevant unit tests were added or updated.
- [ ] Ruff, Mypy, and Pytest pass.
- [ ] Desktop/AppStream validation passes when affected.
- [ ] No real hardware write was performed, or the exact backed-up test procedure is documented.
- [ ] No erase, key reset, password management, formatting, partition, or generic raw SCSI feature was added.

## Hardware evidence

If applicable, provide only sanitized model, VID:PID, serial suffix, environment, and result. Never include a password, hash, complete serial number, or raw unlock payload.
